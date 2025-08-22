from fastapi import FastAPI, File, UploadFile, Form, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import shutil
import os
import uvicorn

app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("upload.html", {"request": request})

@app.post("/upload/")
async def upload_videos(files: list[UploadFile] = File(...), path: str = Form(...)):
    # Define base path: allow override via env var, otherwise pick OS-specific default
    base_path = "/Volumes/Test/"

    # Validate base path availability and writability to avoid server errors on read-only volumes
    if not os.path.isdir(base_path):
        print(f"Base path '{base_path}' not found. Plug in or mount the drive, or change the base path.")
        raise HTTPException(status_code=400, detail=f"Base path '{base_path}' not found. Plug in or mount the drive, or change the base path.")
    if not os.access(base_path, os.W_OK):
        print(f"Base path '{base_path}' is not writable (drive may be read-only, e.g., NTFS on macOS).")
        raise HTTPException(status_code=400, detail=f"Base path '{base_path}' is not writable (drive may be read-only, e.g., NTFS on macOS).")

    # Sanitize provided relative path to prevent traversal and absolute paths
    safe_rel_path = os.path.normpath(path).lstrip(os.sep)
    full_path = os.path.join(base_path, safe_rel_path)

    # Ensure target directory exists
    if not os.path.exists(full_path):
        os.makedirs(full_path, exist_ok=True)
        try:
            os.chmod(full_path, 0o777)
        except Exception:
            # Some filesystems (e.g., FAT/NTFS via third-party drivers) may not support chmod
            pass
    
    uploaded_files = []
    
    for file in files:
        # Define la ruta completa del archivo
        file_path = os.path.join(full_path, file.filename)
        
        # Guarda el archivo en la ruta especificada
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        uploaded_files.append({"filename": file.filename, "path": file_path})
    
    return {"uploaded_files": uploaded_files}
    
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)