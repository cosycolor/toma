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
        themes = engine.get_leading_themes(top_n=6, candidate_count=25)
        self.themesLoaded.emit(themes)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        # Default size: comfortable compact size for trading sidebar (450 x 820)
        self.resize(480, 840)
        # Allow users to make window very small like TIMA
        self.setMinimumSize(360, 460)
        self.setStyleSheet(QSS_DARK_THEME)

        self.is_pinned = False
        self.is_mini = True

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
        nav_layout = QVBoxLayout(nav_frame)
        nav_layout.setContentsMargins(8, 6, 8, 6)
        nav_layout.setSpacing(6)

        # Top Control Row: Brand, Status, Mini Mode, Pin on Top, Refresh
        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(6)

        brand_label = QLabel("⚡ TOMA Pro")
        brand_label.setStyleSheet("font-size: 15px; font-weight: 900; color: #39c5cf;")
        top_row.addWidget(brand_label)

        self.status_badge = QLabel("🟢 실시간")
        self.status_badge.setStyleSheet("color: #39c5cf; font-weight: 700; font-size: 11px;")
        top_row.addWidget(self.status_badge)

        top_row.addStretch()

        # Mini / Wide Toggle
        self.btn_size_toggle = QPushButton("💻 넓게")
        self.btn_size_toggle.setProperty("class", "tool-btn")
        self.btn_size_toggle.clicked.connect(self.toggle_window_size)
        top_row.addWidget(self.btn_size_toggle)

        # Always On Top (Pin)
        self.btn_pin = QPushButton("📌 핀")
        self.btn_pin.setProperty("class", "tool-btn")
        self.btn_pin.setCheckable(True)
        self.btn_pin.clicked.connect(self.toggle_always_on_top)
        top_row.addWidget(self.btn_pin)

        # Refresh
        btn_refresh = QPushButton("🔄")
        btn_refresh.setProperty("class", "tool-btn")
        btn_refresh.setToolTip("새로고침 (F5)")
        btn_refresh.clicked.connect(self.refresh_data)
        top_row.addWidget(btn_refresh)

        nav_layout.addLayout(top_row)

        # Nav Buttons Row (Compact Responsive Tabs)
        tabs_row = QHBoxLayout()
        tabs_row.setContentsMargins(0, 0, 0, 0)
        tabs_row.setSpacing(4)

        self.btn_market = QPushButton("👑 주도주")
        self.btn_calendar = QPushButton("📅 일정")
        self.btn_news = QPushButton("📰 뉴스")
        self.btn_watch = QPushButton("⭐ 관심/메모")

        self.nav_buttons = [self.btn_market, self.btn_calendar, self.btn_news, self.btn_watch]
        for idx, btn in enumerate(self.nav_buttons):
            btn.setProperty("class", "nav-btn")
            btn.setStyleSheet("padding: 5px 8px; font-size: 12px; font-weight: 700;")
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, i=idx: self.switch_view(i))
            tabs_row.addWidget(btn)

        self.btn_market.setChecked(True)
        nav_layout.addLayout(tabs_row)

        main_layout.addWidget(nav_frame)

        # ── Main Stacked Views ───────────────────────────────────────────
        self.stack = QStackedWidget()
        
        self.view_market = MarketCenterView()
        self.view_calendar = MarketCalendarView()
        self.view_news = NewsView()
        self.view_watch = WatchlistView()

        # Connect stock selected signal
        self.view_market.stockSelected.connect(self.on_market_stock_selected)

        self.stack.addWidget(self.view_market)
        self.stack.addWidget(self.view_calendar)
        self.stack.addWidget(self.view_news)
        self.stack.addWidget(self.view_watch)

        main_layout.addWidget(self.stack)

        # ── Status Bar ───────────────────────────────────────────────────
        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("TOMA Pro | 티마 주도주 모드 준비 완료")

        self.setCentralWidget(central_widget)

    def toggle_window_size(self):
        if self.is_mini:
            self.resize(1380, 860)
            self.btn_size_toggle.setText("📱 미니")
            self.is_mini = False
        else:
            self.resize(480, 840)
            self.btn_size_toggle.setText("💻 넓게")
            self.is_mini = True

    def toggle_always_on_top(self):
        self.is_pinned = not self.is_pinned
        self.btn_pin.setChecked(self.is_pinned)
        flags = self.windowFlags()
        if self.is_pinned:
            self.setWindowFlags(flags | Qt.WindowType.WindowStaysOnTopHint)
            self.btn_pin.setText("📌 고정됨")
        else:
            self.setWindowFlags(flags & ~Qt.WindowType.WindowStaysOnTopHint)
            self.btn_pin.setText("📌 핀")
        self.show()

    def on_market_stock_selected(self, code, name):
        self.view_watch.add_stock(code, name, memo="마켓중심 테마 주도주")
        self.statusBar().showMessage(f"⭐ 관심종목 추가 완료: {name}({code})", 3000)

    def switch_view(self, index):
        for idx, btn in enumerate(self.nav_buttons):
            btn.setChecked(idx == index)
        self.stack.setCurrentIndex(index)

    def init_timer(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_data)
        self.timer.start(REFRESH_THEME_MS)

    def refresh_data(self):
        self.status_badge.setText("🔄 갱신 중")
        self.worker = DataWorkerThread()
        self.worker.themesLoaded.connect(self.on_themes_loaded)
        self.worker.start()

    def on_themes_loaded(self, themes):
        self.view_market.update_themes(themes)
        self.status_badge.setText("🟢 실시간")
        self.statusBar().showMessage(f"실시간 갱신 완료 ({len(themes)}개 테마)")

