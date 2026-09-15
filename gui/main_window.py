from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QStackedWidget, QLabel, QFrame, QStatusBar, QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QIcon, QFont
from config import APP_NAME, APP_VERSION, COLORS, REFRESH_THEME_MS
from styles import QSS_DARK_THEME
from core.engine import engine

from gui.views.market_center import MarketCenterView
from gui.views.market_calendar import MarketCalendarView
from gui.views.news_view import NewsView
from gui.views.watchlist_view import WatchlistView

class DataWorkerThread(QThread):
    """Background worker thread for non-blocking real-time theme & stock updates"""
    themesLoaded = pyqtSignal(list)

    def run(self):
        data = engine.get_theme_ranking(page=1, page_size=50)
        themes = data.get("groups", [])
        self.themesLoaded.emit(themes)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.resize(1420, 880)
        self.setMinimumSize(1080, 700)
        self.setStyleSheet(QSS_DARK_THEME)

        self.init_ui()
        self.init_timer()
        self.refresh_data()

    def init_ui(self):
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── Top Navigation Bar ───────────────────────────────────────────
        nav_frame = QFrame()
        nav_frame.setObjectName("navBar")
        nav_layout = QHBoxLayout(nav_frame)
        nav_layout.setContentsMargins(12, 6, 12, 6)

        # Brand Title
        brand_label = QLabel("⚡ TOMA Pro")
        brand_label.setStyleSheet("font-size: 18px; font-weight: 900; color: #39c5cf; letter-spacing: -0.5px;")
        sub_label = QLabel("주도주 트레이딩 인텔리전스")
        sub_label.setStyleSheet("font-size: 11px; font-weight: 600; color: #8b949e; margin-left: 6px;")
        nav_layout.addWidget(brand_label)
        nav_layout.addWidget(sub_label)
        nav_layout.addSpacing(20)

        # Nav Buttons
        self.btn_market = QPushButton("👑 마켓중심 (주도테마/대장주)")
        self.btn_calendar = QPushButton("📅 마켓일정")
        self.btn_news = QPushButton("📰 특징주 뉴스/공시")
        self.btn_watch = QPushButton("⭐ 관심종목/메모")

        self.nav_buttons = [self.btn_market, self.btn_calendar, self.btn_news, self.btn_watch]
        for idx, btn in enumerate(self.nav_buttons):
            btn.setProperty("class", "nav-btn")
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, i=idx: self.switch_view(i))
            nav_layout.addWidget(btn)

        self.btn_market.setChecked(True)
        nav_layout.addStretch()

        # Status Badge & Manual Refresh
        self.status_badge = QLabel("🟢 실시간 연동 중")
        self.status_badge.setStyleSheet("color: #39c5cf; font-weight: 700; font-size: 12px; margin-right: 10px;")
        nav_layout.addWidget(self.status_badge)

        btn_refresh = QPushButton("새로고침 (F5)")
        btn_refresh.setProperty("class", "action-btn")
        btn_refresh.clicked.connect(self.refresh_data)
        nav_layout.addWidget(btn_refresh)

        main_layout.addWidget(nav_frame)

        # ── Main Stacked Views ───────────────────────────────────────────
        self.stack = QStackedWidget()
        
        self.view_market = MarketCenterView()
        self.view_calendar = MarketCalendarView()
        self.view_news = NewsView()
        self.view_watch = WatchlistView()

        # Connect double-click on market center stocks to add directly to watchlist
        self.view_market.stockSelected.connect(self.on_market_stock_selected)

        self.stack.addWidget(self.view_market)
        self.stack.addWidget(self.view_calendar)
        self.stack.addWidget(self.view_news)
        self.stack.addWidget(self.view_watch)

        main_layout.addWidget(self.stack)

        # ── Status Bar ───────────────────────────────────────────────────
        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("TOMA Pro Desktop 준비 완료 | 코스피/코스닥 실시간 주도테마 감지 중")

        self.setCentralWidget(central_widget)

    def on_market_stock_selected(self, code, name):
        self.view_watch.add_stock(code, name, memo="마켓중심 테마 주도주")
        self.statusBar().showMessage(f"⭐ 관심종목 추가 완료: {name}({code})", 4000)

    def switch_view(self, index):
        for idx, btn in enumerate(self.nav_buttons):
            btn.setChecked(idx == index)
        self.stack.setCurrentIndex(index)

    def init_timer(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_data)
        self.timer.start(REFRESH_THEME_MS)

    def refresh_data(self):
        self.status_badge.setText("🔄 갱신 중...")
        self.worker = DataWorkerThread()
        self.worker.themesLoaded.connect(self.on_themes_loaded)
        self.worker.start()

    def on_themes_loaded(self, themes):
        self.view_market.update_themes(themes)
        self.status_badge.setText("🟢 실시간 연동 중")
        self.statusBar().showMessage(f"실시간 갱신 완료 (총 {len(themes)}개 테마 연동)")
