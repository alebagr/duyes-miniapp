import os
import logging
from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="DuYes Mini App")

# Текущая директория файла main.py (папка /miniapp)
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# 1. Отдаем главную страницу index.html по адресу /
@app.get("/")
async def serve_index():
    index_path = os.path.join(CURRENT_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return JSONResponse(
        status_code=404,
        content={"error": "index.html not found", "path": index_path}
    )

# 2. Отдаем файлы app.js и styles.css, если к ним обращаются напрямую
@app.get("/app.js")
async def serve_js():
    return FileResponse(os.path.join(CURRENT_DIR, "app.js"))

@app.get("/styles.css")
async def serve_css():
    return FileResponse(os.path.join(CURRENT_DIR, "styles.css"))

# 3. Эндпоинт проверки статуса
@app.get("/health")
async def health():
    return {"status": "ok"}
