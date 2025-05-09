# main.py
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
import os
import uuid
from datetime import datetime
from pathlib import Path
from fastapi.responses import FileResponse
import shutil

app = FastAPI()
messages = []
UPLOAD_DIR = "uploads"
PHOTO_LIFETIME = 60  # Время жизни фото в секундах до автоматического удаления

# Очистка старых файлов при старте
Path(UPLOAD_DIR).mkdir(exist_ok=True)
[shutil.rmtree(UPLOAD_DIR), Path(UPLOAD_DIR).mkdir()] if any(Path(UPLOAD_DIR).iterdir()) else None

app.mount("/static", StaticFiles(directory=UPLOAD_DIR), name="static")


def cleanup_old_files():
    """Удаление файлов старше PHOTO_LIFETIME"""
    now = datetime.now().timestamp()
    for f in Path(UPLOAD_DIR).iterdir():
        if f.is_file() and (now - f.stat().st_ctime) > PHOTO_LIFETIME:
            f.unlink()


@app.get("/")
def status():
    return {"status": "ok"}


@app.get("/send_message/{message}")
def send_message(message: str):
    messages.append(message)
    return {"status": "Сообщение сохранено"}


@app.get("/get_message")
def get_message():
    return {"message": messages.pop(0) if messages else None}


@app.post("/upload_photo")
async def upload_photo(file: UploadFile = File(...)):
    """Загрузка фото с автоматическим удалением через 1 минуту"""
    cleanup_old_files()
    filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex}{Path(file.filename).suffix}"
    file_path = os.path.join(UPLOAD_DIR, filename)

    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    return {"filename": filename, "url": f"/photos/{filename}"}


@app.get("/photos/{filename}", response_class=FileResponse)
async def view_photo(filename: str):
    """
    Просмотр загруженного фото (доступно прямо в Swagger UI)

    - **filename**: Имя файла фото (из ответа upload_photo)
    """
    file_path = os.path.join(UPLOAD_DIR, filename)

    # Проверка существования файла
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Фото не найдено")

    # Проверка, что это файл (а не директория)
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=400, detail="Указанный путь не является файлом")

    # Определение MIME-типа по расширению файла
    ext = Path(filename).suffix.lower()
    media_type = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
    }.get(ext, 'application/octet-stream')

    return FileResponse(
        file_path,
        media_type=media_type,
        filename=filename  # Это имя файла для скачивания (если нужно)
    )

@app.get("/photos/")
async def list_photos():
    return {"photos": [f for f in os.listdir(UPLOAD_DIR) if os.path.isfile(os.path.join(UPLOAD_DIR, f))]}