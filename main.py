from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
import os
import uvicorn
from scraper import download_and_zip

app = FastAPI()

# Mount the current directory to serve static files like index.html
app.mount("/static", StaticFiles(directory="."), name="static")

@app.get("/", response_class=HTMLResponse)
async def get_index():
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/api/download")
async def api_download(subject: str, start_year: int, end_year: int, background_tasks: BackgroundTasks):
    try:
        # Call the scraper to get the zip file
        zip_path = download_and_zip(subject, start_year, end_year)
        
        # We need to delete the zip file after sending it
        background_tasks.add_task(os.remove, zip_path)
        
        return FileResponse(
            path=zip_path,
            filename=f"GSAT_{subject}_{start_year}-{end_year}.zip",
            media_type="application/zip"
        )
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
