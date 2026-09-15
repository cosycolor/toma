import sys
import os

# Base directory for data storage (Works for both .py and PyInstaller .exe)
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

WATCHLIST_FILE = os.path.join(DATA_DIR, "watchlist.json")
MEMO_FILE = os.path.join(DATA_DIR, "trader_memo.txt")

# TOMA Desktop Trading Intelligence Configuration

APP_NAME = "TOMA Pro Desktop (주도주 트레이딩 내비게이션)"
APP_VERSION = "1.0.0"

# UI Color Palette (Pro Dark HTS)
COLORS = {
    "bg_main": "#0d1117",
    "bg_surface": "#161b22",
    "bg_surface_alt": "#21262d",
    "bg_hover": "#30363d",
    "border": "#30363d",
    "border_focus": "#58a6ff",
    "text_main": "#f0f6fc",
    "text_muted": "#8b949e",
    "text_dim": "#484f58",
    
    # Financial Bull / Bear (Korean Standard: Red Up / Blue Down)
    "bull_red": "#ff453a",
    "bull_red_bg": "#3b181c",
    "bear_blue": "#58a6ff",
    "bear_blue_bg": "#13233a",
    "upper_limit": "#ff7b72",
    "upper_limit_bg": "#4c1a1f",
    
    # Highlights & Badges
    "gold": "#e3b341",
    "gold_bg": "#3d2e05",
    "silver": "#c9d1d9",
    "silver_bg": "#252b33",
    "cyan": "#39c5cf",
    "purple": "#bc8cff"
}

REFRESH_THEME_MS = 5000       # 5s
REFRESH_NEWS_MS = 15000       # 15s
REFRESH_CALENDAR_MS = 60000   # 60s
