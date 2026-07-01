import asyncio
import os
import shutil
import subprocess
import tempfile
import time
import logging
from collections import defaultdict, deque
from pathlib import Path
from uuid import uuid4

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles


BASE_DIR = Path(__file__).resolve().parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "50"))
MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024
CONVERSION_TIMEOUT_SECONDS = int(os.getenv("CONVERSION_TIMEOUT_SECONDS", "180"))
MAX_CONCURRENT_CONVERSIONS = int(os.getenv("MAX_CONCURRENT_CONVERSIONS", "2"))
RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
RATE_LIMIT_MAX_REQUESTS = int(os.getenv("RATE_LIMIT_MAX_REQUESTS", "30"))
TEMP_FILE_TTL_MINUTES = int(os.getenv("TEMP_FILE_TTL_MINUTES", "30"))
SHOW_CONVERSION_ERRORS = os.getenv("SHOW_CONVERSION_ERRORS", "1") == "1"
APP_VERSION = "2026-07-01-security-layer"
ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv("ALLOWED_HOSTS", "127.0.0.1,localhost,*.onrender.com").split(",")
    if host.strip()
]
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", "http://127.0.0.1:8000,http://localhost:8000").split(",")
    if origin.strip()
]

logging.basicConfig(
    filename=LOG_DIR / "conversions.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

CALIBRE_PARAMS = [
    "--enable-heuristics",
    "--html-unwrap-factor",
    "0.40",
    "--page-breaks-before",
    "/",
]

app = FastAPI(title="PDF para EPUB")
conversion_slots = asyncio.Semaphore(MAX_CONCURRENT_CONVERSIONS)
rate_limit_hits: dict[str, deque[float]] = defaultdict(deque)

app.add_middleware(TrustedHostMiddleware, allowed_hosts=ALLOWED_HOSTS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


def client_ip(request: Request) -> str:
    cf_ip = request.headers.get("cf-connecting-ip")
    forwarded_for = request.headers.get("x-forwarded-for", "").split(",")[0].strip()

    if cf_ip:
        return cf_ip

    if forwarded_for:
        return forwarded_for

    return request.client.host if request.client else "unknown"


def is_rate_limited(ip: str) -> bool:
    now = time.monotonic()
    hits = rate_limit_hits[ip]

    while hits and now - hits[0] > RATE_LIMIT_WINDOW_SECONDS:
        hits.popleft()

    if len(hits) >= RATE_LIMIT_MAX_REQUESTS:
        return True

    hits.append(now)
    return False


def cleanup_old_temp_directories() -> None:
    temp_root = Path(tempfile.gettempdir())
    max_age_seconds = TEMP_FILE_TTL_MINUTES * 60
    now = time.time()

    for path in temp_root.glob("pdf-epub-*"):
        if not path.is_dir():
            continue

        try:
            if now - path.stat().st_mtime > max_age_seconds:
                cleanup_directory(path)
        except OSError:
            logging.warning("Could not inspect temp directory %s", path)


@app.on_event("startup")
async def startup_cleanup() -> None:
    cleanup_old_temp_directories()


@app.middleware("http")
async def security_middleware(request: Request, call_next):
    if request.url.path == "/api/convert" and is_rate_limited(client_ip(request)):
        return JSONResponse(
            status_code=429,
            content={"detail": "Muitas conversoes em pouco tempo. Tente novamente em instantes."},
        )

    if request.url.path == "/api/convert":
        content_length = request.headers.get("content-length")

        if content_length and int(content_length) > MAX_UPLOAD_BYTES + 1024 * 1024:
            return JSONResponse(
                status_code=413,
                content={"detail": f"O arquivo ultrapassa o limite de {MAX_UPLOAD_MB} MB."},
            )

    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
    return response


def cleanup_directory(path: Path) -> None:
    shutil.rmtree(path, ignore_errors=True)


def epub_filename(original_name: str) -> str:
    name = Path(original_name).stem.strip() or "arquivo"
    safe = "".join(char if char.isalnum() or char in ("-", "_", " ") else "-" for char in name)
    return f"{safe[:90]}.epub"


def build_conversion_error(stderr: str) -> str:
    stderr_clean = " ".join(stderr.split())

    if SHOW_CONVERSION_ERRORS and stderr_clean:
        return f"Erro do Calibre: {stderr_clean[-1200:]}"

    return "Nao foi possivel converter este PDF."


def run_calibre(input_path: Path, output_path: Path, file_name: str) -> None:
    attempts = [
        ["ebook-convert", str(input_path), str(output_path), *CALIBRE_PARAMS],
        ["ebook-convert", str(input_path), str(output_path)],
    ]
    last_error = ""

    for index, command in enumerate(attempts, start=1):
        if output_path.exists():
            output_path.unlink()

        logging.info("Running command for %s: %s", file_name, " ".join(command))
        result = subprocess.run(command, capture_output=True, text=True, timeout=CONVERSION_TIMEOUT_SECONDS)

        if result.returncode == 0 and output_path.exists() and output_path.stat().st_size > 0:
            if index > 1:
                logging.info("Fallback conversion succeeded for %s", file_name)
            return

        last_error = result.stderr.strip() or result.stdout.strip() or f"ebook-convert retornou codigo {result.returncode}"
        logging.warning(
            "Conversion attempt %s failed for %s with code %s. stdout=%s stderr=%s",
            index,
            file_name,
            result.returncode,
            result.stdout[-1200:],
            result.stderr[-1200:],
        )

    raise HTTPException(status_code=422, detail=build_conversion_error(last_error))


async def save_upload(upload: UploadFile, destination: Path) -> None:
    total = 0

    with destination.open("wb") as output:
        while chunk := await upload.read(1024 * 1024):
            total += len(chunk)

            if total > MAX_UPLOAD_BYTES:
                raise HTTPException(
                    status_code=413,
                    detail=f"O arquivo ultrapassa o limite de {MAX_UPLOAD_MB} MB.",
                )

            output.write(chunk)

    if total == 0:
        raise HTTPException(status_code=400, detail="O arquivo enviado esta vazio.")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/version")
def version() -> dict[str, str]:
    return {"version": APP_VERSION}


@app.post("/api/convert")
async def convert_pdf_to_epub(file: UploadFile, background_tasks: BackgroundTasks) -> FileResponse:
    file_name = file.filename or "arquivo.pdf"

    if not file_name.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Envie um arquivo PDF.")

    work_dir = Path(tempfile.mkdtemp(prefix="pdf-epub-"))
    input_path = work_dir / "entrada.pdf"
    output_path = work_dir / "saida.epub"

    try:
        await save_upload(file, input_path)

        async with conversion_slots:
            run_calibre(input_path, output_path, file_name)

        if not output_path.exists() or output_path.stat().st_size == 0:
            raise HTTPException(status_code=422, detail="O EPUB nao foi gerado.")

        background_tasks.add_task(cleanup_directory, work_dir)
        return FileResponse(
            output_path,
            media_type="application/epub+zip",
            filename=epub_filename(file_name),
            background=background_tasks,
        )
    except subprocess.TimeoutExpired as exc:
        cleanup_directory(work_dir)
        raise HTTPException(status_code=408, detail="A conversao demorou demais.") from exc
    except FileNotFoundError as exc:
        cleanup_directory(work_dir)
        raise HTTPException(status_code=500, detail="O Calibre nao foi encontrado no servidor.") from exc
    except HTTPException:
        cleanup_directory(work_dir)
        raise


app.mount("/", StaticFiles(directory=BASE_DIR, html=True), name="site")
