import os
from typing import Optional
from fastapi import FastAPI, Request, Query
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from core.engine import engine

app = FastAPI(title="TOMA Pro Web", version="1.0.0")

# Setup directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
INDEX_HTML_PATH = os.path.join(TEMPLATES_DIR, "index.html")

os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(TEMPLATES_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/", response_class=FileResponse)
async def home():
    """Serve the single-page web app"""
    return FileResponse(INDEX_HTML_PATH)

@app.get("/api/themes")
async def get_themes(leading: bool = True, top_n: int = 6, page: int = 1, page_size: int = 50):
    """Return real-time leading themes or raw ranking"""
    if leading:
        themes = engine.get_leading_themes(top_n=top_n, candidate_count=25)
        return JSONResponse(content={"groups": themes, "totalCount": len(themes)})
    data = engine.get_theme_ranking(page=page, page_size=page_size)
    return JSONResponse(content=data)

@app.get("/api/themes/{theme_no}")
async def get_theme_detail(theme_no: int, page: int = 1, page_size: int = 50):
    """Return detailed leader stocks & description for a theme"""
    data = engine.get_theme_detail(theme_no=theme_no, page=page, page_size=page_size)
    return JSONResponse(content=data)

@app.get("/api/news")
async def get_news(page: int = 1):
    """Return real-time market news"""
    items = engine.get_realtime_news()
    return JSONResponse(content={"items": items})

@app.get("/api/news/content")
async def get_news_content(oid: str, aid: str):
    """Return parsed full text of news article"""
    content = engine.get_news_content(oid=oid, aid=aid)
    return JSONResponse(content={"content": content})

@app.get("/api/calendar")
async def get_calendar():
    """Return economic schedule and IPO/lockup events"""
    events = engine.get_economic_calendar()
    return JSONResponse(content={"events": events})

@app.get("/api/stock/search")
async def search_stock(q: str = Query(..., min_length=1)):
    """Search stock autocomplete"""
    items = engine.search_stock(q)
    return JSONResponse(content={"items": items})

@app.get("/api/stock/{code}")
async def get_stock_basic(code: str):
    """Fetch basic stock quotes"""
    data = engine.get_stock_basic(code)
    return JSONResponse(content={"data": data})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
