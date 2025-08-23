from fastapi import FastAPI, File, UploadFile, Form, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os
import asyncio
from typing import List, Dict, Any
import uvicorn
import aiofiles

app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("upload.html", {"request": request})

CHUNK_SIZE_BYTES = 8 * 1024 * 1024  # 8 MiB chunks for good throughput without huge memory
MAX_CONCURRENT_WRITES = int(os.environ.get("MAX_CONCURRENT_WRITES", "4"))


def _get_base_upload_dir() -> str:
    base_path = "/Volumes/Test/"
    return base_path


def _ensure_target_dir(path: str) -> str:
    base_path = _get_base_upload_dir()
    if not os.path.isdir(base_path):
        raise HTTPException(status_code=400, detail=f"Base path '{base_path}' not found. Plug in or mount the drive, or change the base path.")
    if not os.access(base_path, os.W_OK):
        raise HTTPException(status_code=400, detail=f"Base path '{base_path}' is not writable (drive may be read-only, e.g., NTFS on macOS).")

    safe_rel_path = os.path.normpath(path).lstrip(os.sep)
    full_path = os.path.join(base_path, safe_rel_path)
    if not os.path.exists(full_path):
        os.makedirs(full_path, exist_ok=True)
        try:
            os.chmod(full_path, 0o777)
        except Exception:
            pass
    return full_path


async def _save_upload_file_chunked(upload_file: UploadFile, destination_dir: str) -> Dict[str, Any]:
    target_path = os.path.join(destination_dir, upload_file.filename)
    tmp_path = f"{target_path}.part"
    total_written = 0
    try:
        async with aiofiles.open(tmp_path, "wb") as out_file:
            while True:
                chunk = await upload_file.read(CHUNK_SIZE_BYTES)
                if not chunk:
                    break
                await out_file.write(chunk)
                total_written += len(chunk)
        # Atomic move into final filename after successful write
        os.replace(tmp_path, target_path)
        return {"filename": upload_file.filename, "path": target_path, "bytes": total_written, "status": "ok"}
    except Exception as exc:
        # Best effort clean-up of temp file
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception:
            pass
        return {"filename": upload_file.filename, "error": str(exc), "status": "error"}
    finally:
        try:
            await upload_file.close()
        except Exception:
            pass


@app.post("/upload/single")
async def upload_single(file: UploadFile = File(...), path: str = Form(...)):
    destination = _ensure_target_dir(path)
    result = await _save_upload_file_chunked(file, destination)
    if result.get("status") != "ok":
        raise HTTPException(status_code=500, detail=result.get("error", "Unknown error"))
    return result


@app.post("/upload/")
async def upload_videos(files: List[UploadFile] = File(...), path: str = Form(...)):
    destination = _ensure_target_dir(path)

    # Concurrent saves with a semaphore to cap disk contention
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_WRITES)

    async def _guarded_save(f: UploadFile) -> Dict[str, Any]:
        async with semaphore:
            return await _save_upload_file_chunked(f, destination)

    results = await asyncio.gather(*[_guarded_save(f) for f in files], return_exceptions=False)
    successes = [r for r in results if r.get("status") == "ok"]
    failures = [r for r in results if r.get("status") != "ok"]
    return {"uploaded_files": successes, "failed": failures, "concurrency": MAX_CONCURRENT_WRITES}
    
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)