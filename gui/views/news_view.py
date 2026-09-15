import webbrowser
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLabel, QHeaderView, QFrame, QTextBrowser, QPushButton, QSplitter,
    QLineEdit, QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QColor, QFont
from config import COLORS
from core.engine import engine

class ArticleFetchThread(QThread):
    """Worker thread to fetch full article body asynchronously"""
    contentLoaded = pyqtSignal(str)

    def __init__(self, oid, aid):
        super().__init__()
        self.oid = oid
        self.aid = aid

    def run(self):
        content = engine.get_news_content(self.oid, self.aid)
        self.contentLoaded.emit(content)

class NewsView(QWidget):
    """
    TOMA Real-time News & Disclosure Stream (실시간 특징주 뉴스 & 공시)
    - Left: Real-time News Stream
    - Right: Article Preview & Web View Link
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.news_items = []
        self.selected_item = None
        self.fetch_thread = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # ── Left: News List Panel ──────────────────────────────────────────
        left_panel = QFrame()
        left_panel.setProperty("class", "panel")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(10, 10, 10, 10)

        # Header with Search & Refresh
        lh_layout = QHBoxLayout()
        lbl_title = QLabel("📰 실시간 장중 특징주 뉴스 & 공시")
        lbl_title.setStyleSheet("font-size: 15px; font-weight: 800; color: #f0f6fc;")
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("뉴스 검색...")
        self.search_input.setMaximumWidth(150)
        self.search_input.textChanged.connect(self.filter_news)

        btn_refresh = QPushButton("새로고침")
        btn_refresh.setProperty("class", "action-btn")
        btn_refresh.clicked.connect(self.load_news)

        lh_layout.addWidget(lbl_title)
        lh_layout.addStretch()
        lh_layout.addWidget(self.search_input)
        lh_layout.addWidget(btn_refresh)
        left_layout.addLayout(lh_layout)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["발행시간", "언론사", "뉴스 / 공시 제목", "관련 종목"])
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.itemSelectionChanged.connect(self.on_news_selected)
        self.table.cellDoubleClicked.connect(self.on_news_double_clicked)
        left_layout.addWidget(self.table)

        splitter.addWidget(left_panel)

        # ── Right: Article Detail Panel ────────────────────────────────────
        right_panel = QFrame()
        right_panel.setProperty("class", "panel")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(12, 12, 12, 12)

        # Detail Header
        rh_layout = QHBoxLayout()
        self.lbl_detail_meta = QLabel("기사를 선택하면 상세 내용이 표시됩니다.")
        self.lbl_detail_meta.setStyleSheet("font-size: 12px; color: #8b949e; font-weight: 600;")
        
        self.btn_open_browser = QPushButton("🌐 원문 기사 열기")
        self.btn_open_browser.setProperty("class", "action-btn")
        self.btn_open_browser.clicked.connect(self.open_in_browser)
        self.btn_open_browser.setEnabled(False)

        rh_layout.addWidget(self.lbl_detail_meta)
        rh_layout.addStretch()
        rh_layout.addWidget(self.btn_open_browser)
        right_layout.addLayout(rh_layout)

        # Article Title
        self.lbl_detail_title = QLabel("")
        self.lbl_detail_title.setWordWrap(True)
        self.lbl_detail_title.setStyleSheet("font-size: 16px; font-weight: 800; color: #39c5cf; margin-top: 6px; margin-bottom: 6px;")
        right_layout.addWidget(self.lbl_detail_title)

        # Article Body Text Browser
        self.detail_browser = QTextBrowser()
        self.detail_browser.setOpenExternalLinks(True)
        self.detail_browser.setStyleSheet("""
            QTextBrowser {
                background-color: #0d1117;
                border: 1px solid #30363d;
                border-radius: 6px;
                padding: 10px;
                color: #c9d1d9;
                font-size: 13px;
                line-height: 1.6;
            }
        """)
        self.detail_browser.setPlaceholderText("좌측 뉴스 목록에서 기사를 클릭하면 본문 미리보기가 여기에 나타납니다.")
        right_layout.addWidget(self.detail_browser)

        splitter.addWidget(right_panel)
        splitter.setSizes([550, 550])

        layout.addWidget(splitter)
        self.load_news()

    def load_news(self):
        items = engine.get_realtime_news()
        if not items:
            items = [
                {"datetime": "15:20", "press": "한국경제", "title": "[특징주] 로봇 대장주 레인보우로보틱스, 신규 수주 계약 소식에 급등", "stock": "레인보우로보틱스", "summary": "로봇 대장주 레인보우로보틱스가 대규모 수주 소식에 강세를 보이고 있습니다.", "link": ""},
                {"datetime": "14:45", "press": "매일경제", "title": "[특징주] 양자암호 양자컴퓨팅 테마주 동반 급등세 지속", "stock": "한국첨단소재", "summary": "정부의 양자 클러스터 투자 발표로 관련주들이 일제히 상승세를 보이고 있습니다.", "link": ""},
                {"datetime": "13:10", "press": "전자공시", "title": "[공시] 삼성전자, 단일판매·공급계약체결 수주 공시 발표", "stock": "삼성전자", "summary": "삼성전자가 글로벌 고객사와 대규모 반도체 공급 계약을 체결했다고 공시했습니다.", "link": ""}
            ]
        self.news_items = items
        self.render_table(self.news_items)

    def render_table(self, items):
        self.table.setRowCount(len(items))
        for row, n in enumerate(items):
            time_str = n.get("datetime", "")
            press_str = n.get("press", "")
            title_str = n.get("title", "")
            stock_str = n.get("stock", "-")

            item_time = QTableWidgetItem(time_str)
            item_time.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_time.setForeground(QColor(COLORS["text_muted"]))
            self.table.setItem(row, 0, item_time)

            item_press = QTableWidgetItem(press_str)
            item_press.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_press.setForeground(QColor(COLORS["cyan"]))
            self.table.setItem(row, 1, item_press)

            item_title = QTableWidgetItem(title_str)
            item_title.setFont(QFont("Pretendard", 10, QFont.Weight.Bold))
            item_title.setData(Qt.ItemDataRole.UserRole, n)
            self.table.setItem(row, 2, item_title)

            item_stk = QTableWidgetItem(stock_str)
            item_stk.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_stk.setForeground(QColor(COLORS["gold"]))
            font = item_stk.font()
            font.setBold(True)
            item_stk.setFont(font)
            self.table.setItem(row, 3, item_stk)

        if items and self.table.currentRow() < 0:
            self.table.selectRow(0)

    def filter_news(self, text):
        query = text.strip().lower()
        if not query:
            self.render_table(self.news_items)
            return
        filtered = [
            n for n in self.news_items
            if query in n.get("title", "").lower() or query in n.get("press", "").lower() or query in n.get("stock", "").lower()
        ]
        self.render_table(filtered)

    def on_news_selected(self):
        selected_rows = self.table.selectedItems()
        if not selected_rows:
            return
        row = self.table.currentRow()
        title_item = self.table.item(row, 2)
        if not title_item:
            return

        item_data = title_item.data(Qt.ItemDataRole.UserRole)
        if not item_data:
            return

        self.selected_item = item_data
        title = item_data.get("title", "")
        press = item_data.get("press", "")
        dt = item_data.get("datetime", "")
        stock = item_data.get("stock", "-")
        summary = item_data.get("summary", "")
        link = item_data.get("link", "")
        oid = item_data.get("oid", "")
        aid = item_data.get("aid", "")

        self.lbl_detail_title.setText(title)
        self.lbl_detail_meta.setText(f"📰 출처: {press} | ⏰ {dt} | 🏷️ 관련: {stock}")
        self.btn_open_browser.setEnabled(bool(link))

        # Initial display with summary
        if summary:
            self.detail_browser.setHtml(f"<p style='font-size:14px; line-height:1.7; color:#c9d1d9;'><b>[요약]</b><br>{summary}</p><p style='color:#8b949e;'><i>전체 본문 로딩 중...</i></p>")
        else:
            self.detail_browser.setHtml("<p style='color:#8b949e;'><i>본문 로딩 중...</i></p>")

        # Asynchronously fetch full body
        if oid and aid:
            if self.fetch_thread and self.fetch_thread.isRunning():
                self.fetch_thread.terminate()
            self.fetch_thread = ArticleFetchThread(oid, aid)
            self.fetch_thread.contentLoaded.connect(self.on_article_loaded)
            self.fetch_thread.start()

    def on_article_loaded(self, content):
        if content:
            formatted_text = content.replace("\n", "<br>")
            self.detail_browser.setHtml(f"<div style='font-size:14px; line-height:1.8; color:#c9d1d9;'>{formatted_text}</div>")
        elif self.selected_item and self.selected_item.get("summary"):
            self.detail_browser.setHtml(f"<div style='font-size:14px; line-height:1.8; color:#c9d1d9;'>{self.selected_item.get('summary')}</div>")

    def on_news_double_clicked(self, row, col):
        title_item = self.table.item(row, 2)
        if not title_item:
            return
        item_data = title_item.data(Qt.ItemDataRole.UserRole)
        if item_data and item_data.get("link"):
            webbrowser.open(item_data["link"])

    def open_in_browser(self):
        if self.selected_item and self.selected_item.get("link"):
            webbrowser.open(self.selected_item["link"])
