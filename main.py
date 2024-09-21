from fastapi import FastAPI, File, UploadFile, Form, Request
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
    # Define la ruta base del servidor
    base_path = "D:/" if os.name == 'nt' else "/"
    
    # Combina la ruta base con el path recibido
    full_path = os.path.join(base_path, path)
    
    # Verifica si la ruta completa existe, si no, la crea
    if not os.path.exists(full_path):
        os.makedirs(full_path)
        os.chmod(path, 0o777)
    
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