from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QLabel, QHeaderView, QFrame, QSplitter, QLineEdit, QPushButton,
    QStyledItemDelegate, QStyleOptionViewItem, QTextEdit, QStyle,
    QScrollArea, QGridLayout, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QRect, QThread, QObject
from PyQt6.QtGui import QColor, QFont, QPainter, QBrush, QPen, QLinearGradient
from config import COLORS
from core.engine import engine

class RateVisualDelegate(QStyledItemDelegate):
    """Visual Gauge Bar Delegate for Fluctuation Rate"""
    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index):
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if option.state & QStyle.StateFlag.State_Selected:
            painter.fillRect(option.rect, QColor("#1f2937"))
        else:
            painter.fillRect(option.rect, QColor(COLORS["bg_surface"]))

        rate_val = index.data(Qt.ItemDataRole.UserRole)
        display_text = index.data(Qt.ItemDataRole.DisplayRole) or ""

        if rate_val is not None:
            try:
                rate_num = float(rate_val)
            except Exception:
                rate_num = 0.0

            rect = option.rect
            margin = 3
            bar_height = rect.height() - (margin * 2)
            pct = min(max(abs(rate_num) / 30.0, 0.05), 1.0)
            bar_width = int((rect.width() - 10) * pct)

            if rate_num >= 29.8:
                grad = QLinearGradient(rect.left() + 5, rect.top(), rect.left() + 5 + bar_width, rect.top())
                grad.setColorAt(0, QColor(255, 75, 75, 200))
                grad.setColorAt(1, QColor(255, 180, 0, 230))
                painter.setBrush(QBrush(grad))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawRoundedRect(QRect(rect.left() + 5, rect.top() + margin, bar_width, bar_height), 4, 4)
            elif rate_num > 0:
                alpha = int(60 + (pct * 140))
                painter.setBrush(QBrush(QColor(248, 81, 73, alpha)))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawRoundedRect(QRect(rect.left() + 5, rect.top() + margin, bar_width, bar_height), 4, 4)
            elif rate_num < 0:
                alpha = int(60 + (pct * 120))
                painter.setBrush(QBrush(QColor(88, 166, 255, alpha)))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawRoundedRect(QRect(rect.left() + 5, rect.top() + margin, bar_width, bar_height), 4, 4)

        painter.setPen(QPen(QColor(option.palette.text().color())))
        if rate_val is not None and rate_val >= 29.8:
            painter.setPen(QPen(QColor(COLORS["gold"])))
            font = painter.font()
            font.setBold(True)
            painter.setFont(font)
        elif rate_val is not None and rate_val > 0:
            painter.setPen(QPen(QColor("#ffffff" if rate_val > 10 else COLORS["bull_red"])))
            font = painter.font()
            font.setBold(True)
            painter.setFont(font)
        elif rate_val is not None and rate_val < 0:
            painter.setPen(QPen(QColor(COLORS["bear_blue"])))

        text_rect = option.rect.adjusted(8, 0, -8, 0)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, display_text)
        painter.restore()


class MoneyFlowDelegate(QStyledItemDelegate):
    """Visual Power Bar Delegate for Trading Value"""
    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index):
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if option.state & QStyle.StateFlag.State_Selected:
            painter.fillRect(option.rect, QColor("#1f2937"))
        else:
            painter.fillRect(option.rect, QColor(COLORS["bg_surface"]))

        val_num = index.data(Qt.ItemDataRole.UserRole)
        display_text = index.data(Qt.ItemDataRole.DisplayRole) or "-"

        if val_num is not None and isinstance(val_num, (int, float)) and val_num > 0:
            pct = min(max(val_num / 200000000000.0, 0.05), 1.0)
            rect = option.rect
            margin = 3
            bar_height = rect.height() - (margin * 2)
            bar_width = int((rect.width() - 10) * pct)

            if val_num >= 100000000000:
                grad = QLinearGradient(rect.left() + 5, rect.top(), rect.left() + 5 + bar_width, rect.top())
                grad.setColorAt(0, QColor(57, 197, 207, 180))
                grad.setColorAt(1, QColor(255, 215, 0, 220))
                painter.setBrush(QBrush(grad))
            elif val_num >= 50000000000:
                painter.setBrush(QBrush(QColor(57, 197, 207, 140)))
            else:
                painter.setBrush(QBrush(QColor(57, 197, 207, 60)))

            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(QRect(rect.left() + 5, rect.top() + margin, bar_width, bar_height), 4, 4)

        painter.setPen(QPen(QColor(COLORS["cyan"] if (val_num and val_num >= 50000000000) else COLORS["text_main"])))
        font = painter.font()
        if val_num and val_num >= 100000000000:
            font.setBold(True)
            painter.setPen(QPen(QColor(COLORS["gold"])))
        painter.setFont(font)

        text_rect = option.rect.adjusted(8, 0, -8, 0)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, display_text)
        painter.restore()


class ThemeRatioDelegate(QStyledItemDelegate):
    """Visual Mini Dual Ratio Bar for Theme Rise/Fall"""
    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index):
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if option.state & QStyle.StateFlag.State_Selected:
            painter.fillRect(option.rect, QColor("#1f2937"))
        else:
            painter.fillRect(option.rect, QColor(COLORS["bg_surface"]))

        counts = index.data(Qt.ItemDataRole.UserRole)
        display_text = index.data(Qt.ItemDataRole.DisplayRole) or ""

        if counts and isinstance(counts, (list, tuple)) and len(counts) >= 3:
            rise, fall, total = counts
            if total > 0:
                rect = option.rect
                margin_y = 10
                bar_h = 4
                bar_w = rect.width() - 16
                rise_w = int(bar_w * (rise / total))
                fall_w = bar_w - rise_w

                x = rect.left() + 8
                y = rect.bottom() - margin_y

                if rise_w > 0:
                    painter.setBrush(QBrush(QColor(COLORS["bull_red"])))
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.drawRect(QRect(x, y, rise_w, bar_h))

                if fall_w > 0:
                    painter.setBrush(QBrush(QColor(COLORS["bear_blue"])))
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.drawRect(QRect(x + rise_w, y, fall_w, bar_h))

        painter.setPen(QPen(QColor(COLORS["text_muted"])))
        text_rect = option.rect.adjusted(4, 0, -4, -6)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, display_text)
        painter.restore()


class ThemeCardDetailsThread(QThread):
    """Worker to fetch stocks for a card asynchronously"""
    stocksLoaded = pyqtSignal(int, list, str) # theme_no, stocks, description

    def __init__(self, theme_no):
        super().__init__()
        self.theme_no = theme_no

    def run(self):
        detail = engine.get_theme_detail(self.theme_no)
        stocks = detail.get("stocks", [])
        desc = detail.get("description", "")
        self.stocksLoaded.emit(self.theme_no, stocks, desc)


class ThemeCardWidget(QFrame):
    """
    티마(TIMA) 스타일 주도 테마 카드 위젯
    각 테마별로 대장주/2등주/3등주 및 등락률, 거래대금, 사유를 한눈에 볼 수 있는 카드
    """
    stockSelected = pyqtSignal(str, str) # code, name
    themeDetailRequested = pyqtSignal(int, str) # theme_no, theme_name

    def __init__(self, rank: int, theme_info: dict, parent=None):
        super().__init__(parent)
        self.rank = rank
        self.theme_info = theme_info
        self.theme_no = theme_info.get("no")
        self.theme_name = theme_info.get("name", "")
        self.stocks = []
        self.is_expanded = False
        self.thread = None

        self.setProperty("class", "tima-card")
        self.init_ui()
        self.load_stocks()

    def init_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(8, 8, 8, 8)
        self.layout.setSpacing(6)

        # ── Header ──────────────────────────────────────────
        header_frame = QFrame()
        header_frame.setProperty("class", "tima-card-header")
        h_layout = QHBoxLayout(header_frame)
        h_layout.setContentsMargins(8, 6, 8, 6)
        h_layout.setSpacing(8)

        # Rank Badge
        rank_bg = "#d29922" if self.rank == 1 else ("#8b949e" if self.rank in (2, 3) else "#30363d")
        lbl_rank = QLabel(f"{self.rank:02d}")
        lbl_rank.setStyleSheet(f"background-color: {rank_bg}; color: #0d1117; font-weight: 900; font-size: 11px; border-radius: 3px; padding: 2px 5px;")
        lbl_rank.setFixedWidth(24)
        lbl_rank.setAlignment(Qt.AlignmentFlag.AlignCenter)
        h_layout.addWidget(lbl_rank)

        # Theme Name
        lbl_name = QLabel(self.theme_name)
        lbl_name.setStyleSheet("font-size: 14px; font-weight: 800; color: #f0f6fc;")
        lbl_name.setToolTip(self.theme_name)
        h_layout.addWidget(lbl_name)

        h_layout.addStretch()

        # Change Rate
        rate_str = str(self.theme_info.get("changeRate", "0.00"))
        try:
            rate_val = float(rate_str)
        except Exception:
            rate_val = 0.0
        sign = "+" if rate_val > 0 else ""
        rate_color = "#f85149" if rate_val > 0 else ("#58a6ff" if rate_val < 0 else "#8b949e")
        lbl_rate = QLabel(f"{sign}{rate_val:.2f}%")
        lbl_rate.setStyleSheet(f"font-size: 14px; font-weight: 900; color: {rate_color};")
        h_layout.addWidget(lbl_rate)

        # Counts
        rise = self.theme_info.get("riseCount", 0)
        fall = self.theme_info.get("fallCount", 0)
        lbl_counts = QLabel(f"▲{rise} ▼{fall}")
        lbl_counts.setStyleSheet("font-size: 10px; color: #8b949e; margin-left: 4px;")
        h_layout.addWidget(lbl_counts)

        self.layout.addWidget(header_frame)

        # ── Stock List Container ────────────────────────────
        self.stocks_container = QWidget()
        self.stocks_layout = QVBoxLayout(self.stocks_container)
        self.stocks_layout.setContentsMargins(2, 2, 2, 2)
        self.stocks_layout.setSpacing(4)

        self.loading_label = QLabel("⏳ 대장주/수급 분석 로딩 중...")
        self.loading_label.setStyleSheet("color: #8b949e; font-size: 11px; padding: 4px;")
        self.stocks_layout.addWidget(self.loading_label)

        self.layout.addWidget(self.stocks_container)

        # ── Bottom Control / Expand Button ──────────────────
        self.btn_more = QPushButton("전체 종목 보기 ▼")
        self.btn_more.setProperty("class", "tool-btn")
        self.btn_more.setStyleSheet("font-size: 11px; padding: 3px; color: #8b949e;")
        self.btn_more.clicked.connect(self.toggle_expand)
        self.btn_more.setVisible(False)
        self.layout.addWidget(self.btn_more)

    def load_stocks(self):
        self.thread = ThemeCardDetailsThread(self.theme_no)
        self.thread.stocksLoaded.connect(self.on_stocks_loaded)
        self.thread.start()

    def on_stocks_loaded(self, theme_no, stocks, desc):
        if theme_no != self.theme_no:
            return
        self.stocks = stocks
        self.render_stocks_view(limit=3)
        if len(stocks) > 3:
            self.btn_more.setVisible(True)

    def render_stocks_view(self, limit=3):
        # Clear container
        while self.stocks_layout.count():
            item = self.stocks_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self.stocks:
            no_lbl = QLabel("종목 정보 없음")
            no_lbl.setStyleSheet("color: #8b949e; font-size: 11px;")
            self.stocks_layout.addWidget(no_lbl)
            return

        display_stocks = self.stocks if self.is_expanded else self.stocks[:limit]

        for s in display_stocks:
            row_frame = QFrame()
            row_frame.setStyleSheet("background-color: #12171f; border-radius: 4px; padding: 2px;")
            r_layout = QHBoxLayout(row_frame)
            r_layout.setContentsMargins(6, 4, 6, 4)
            r_layout.setSpacing(6)

            tag = s.get("leader_tag", "후발주")
            name = s.get("stockName", "")
            code = s.get("itemCode", "")
            rate_str = s.get("fluctuationsRatio", "0.0")
            reason = s.get("theme_reason", "")
            try:
                rate_val = float(str(rate_str).replace(",", ""))
            except Exception:
                rate_val = 0.0

            try:
                val_raw = s.get("accumulatedTradingValueRaw", 0)
                val_num = float(str(val_raw).replace(",", "")) if val_raw else 0.0
                if val_num >= 100000000000:
                    val_str = f"🔥{val_num / 100000000:,.0f}억"
                elif val_num >= 50000000000:
                    val_str = f"⚡{val_num / 100000000:,.0f}억"
                elif val_num > 0:
                    val_str = f"{val_num / 100000000:,.0f}억"
                else:
                    val_str = "-"
            except Exception:
                val_str = "-"

            # Leader Tag
            tag_color = "#e3b341" if "👑" in tag else ("#8b949e" if "🥈" in tag else ("#39c5cf" if "🥉" in tag else "#484f58"))
            lbl_tag = QLabel(tag)
            lbl_tag.setStyleSheet(f"color: {tag_color}; font-size: 11px; font-weight: 800;")
            lbl_tag.setFixedWidth(52)
            r_layout.addWidget(lbl_tag)

            # Stock Name
            lbl_stock = QLabel(name)
            is_upper = s.get("is_upper_limit")
            stock_color = "#e3b341" if is_upper else "#f0f6fc"
            lbl_stock.setStyleSheet(f"color: {stock_color}; font-size: 12px; font-weight: 700;")
            lbl_stock.setToolTip(f"{name} ({code})\n더블클릭: 관심종목 추가\n이유: {reason}")
            r_layout.addWidget(lbl_stock)

            r_layout.addStretch()

            # Fluctuation Rate
            sign = "+" if rate_val > 0 else ""
            if rate_val >= 29.8:
                rate_text = f"★상한가({sign}{rate_val:.1f}%)"
                rate_style = "color: #ff7b72; font-weight: 900; font-size: 11px; background-color: #3b1d22; padding: 2px 4px; border-radius: 3px;"
            elif rate_val > 0:
                rate_text = f"{sign}{rate_val:.2f}%"
                rate_style = "color: #f85149; font-weight: 800; font-size: 12px;"
            elif rate_val < 0:
                rate_text = f"{rate_val:.2f}%"
                rate_style = "color: #58a6ff; font-size: 12px;"
            else:
                rate_text = "0.00%"
                rate_style = "color: #8b949e; font-size: 12px;"

            lbl_stock_rate = QLabel(rate_text)
            lbl_stock_rate.setStyleSheet(rate_style)
            r_layout.addWidget(lbl_stock_rate)

            # Trading Value
            lbl_val = QLabel(val_str)
            val_style = "color: #39c5cf; font-weight: 700; font-size: 11px;" if ("🔥" in val_str or "⚡" in val_str) else "color: #8b949e; font-size: 11px;"
            lbl_val.setStyleSheet(val_style)
            lbl_val.setFixedWidth(55)
            lbl_val.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            r_layout.addWidget(lbl_val)

            # Connect double click to add to watchlist
            row_frame.mouseDoubleClickEvent = lambda e, c=code, n=name: self.stockSelected.emit(c, n)

            self.stocks_layout.addWidget(row_frame)

    def toggle_expand(self):
        self.is_expanded = not self.is_expanded
        if self.is_expanded:
            self.btn_more.setText("접기 ▲")
            self.render_stocks_view(limit=len(self.stocks))
        else:
            self.btn_more.setText("전체 종목 보기 ▼")
            self.render_stocks_view(limit=3)


class MarketCenterView(QWidget):
    """
    TOMA Pro Market Center (티마 스타일 카드형 뷰 & 분할 테이블 뷰 듀얼 모드 지원)
    """
    stockSelected = pyqtSignal(str, str) # code, name

    def __init__(self, parent=None):
        super().__init__(parent)
        self.themes_data = []
        self.selected_theme_no = None
        self.selected_theme_name = ""
        self.current_stocks = []
        self.card_widgets = []
        self.current_view_mode = "card" # 'card' or 'table'

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # ── Top Toolbar (View Switcher & Search) ───────────────
        tb_frame = QFrame()
        tb_frame.setStyleSheet("background-color: transparent;")
        tb_layout = QHBoxLayout(tb_frame)
        tb_layout.setContentsMargins(0, 0, 0, 0)
        tb_layout.setSpacing(6)

        # Title
        lbl_title = QLabel("🔥 주도 테마 & 대장주")
        lbl_title.setStyleSheet("font-size: 14px; font-weight: 800; color: #f0f6fc;")
        tb_layout.addWidget(lbl_title)

        tb_layout.addStretch()

        # View Mode Toggle: [🗂️ 카드 뷰 (티마)] / [📊 표 뷰 (전문가)]
        self.btn_mode_card = QPushButton("🗂️ 티마 카드")
        self.btn_mode_card.setProperty("class", "tool-btn")
        self.btn_mode_card.setCheckable(True)
        self.btn_mode_card.setChecked(True)
        self.btn_mode_card.clicked.connect(lambda: self.switch_view_mode("card"))

        self.btn_mode_table = QPushButton("📊 분할 표")
        self.btn_mode_table.setProperty("class", "tool-btn")
        self.btn_mode_table.setCheckable(True)
        self.btn_mode_table.clicked.connect(lambda: self.switch_view_mode("table"))

        tb_layout.addWidget(self.btn_mode_card)
        tb_layout.addWidget(self.btn_mode_table)

        # Search Bar
        self.theme_search = QLineEdit()
        self.theme_search.setPlaceholderText("테마/종목 검색...")
        self.theme_search.setMaximumWidth(150)
        self.theme_search.textChanged.connect(self.filter_themes)
        tb_layout.addWidget(self.theme_search)

        layout.addWidget(tb_frame)

        # ── View 1: TIMA Card View (Scroll Area) ───────────────
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.card_container = QWidget()
        self.card_layout = QVBoxLayout(self.card_container)
        self.card_layout.setContentsMargins(0, 0, 4, 0)
        self.card_layout.setSpacing(8)
        self.scroll_area.setWidget(self.card_container)

        layout.addWidget(self.scroll_area)

        # ── View 2: Splitter Table View (Classic 2-Panel) ───────
        self.table_view_widget = QWidget()
        tv_layout = QHBoxLayout(self.table_view_widget)
        tv_layout.setContentsMargins(0, 0, 0, 0)
        tv_layout.setSpacing(8)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: Theme Ranking Table
        left_panel = QFrame()
        left_panel.setProperty("class", "panel")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(8, 8, 8, 8)

        self.theme_table = QTableWidget()
        self.theme_table.setColumnCount(5)
        self.theme_table.setHorizontalHeaderLabels(["순위", "테마명", "등락률", "상승/하락", "종목"])
        h_header_left = self.theme_table.horizontalHeader()
        h_header_left.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.theme_table.setColumnWidth(0, 42)
        self.theme_table.setColumnWidth(1, 140)
        self.theme_table.setColumnWidth(2, 100)
        self.theme_table.setColumnWidth(3, 85)
        self.theme_table.setColumnWidth(4, 45)
        self.theme_table.verticalHeader().setVisible(False)
        self.theme_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.theme_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.theme_table.setItemDelegateForColumn(2, RateVisualDelegate(self.theme_table))
        self.theme_table.setItemDelegateForColumn(3, ThemeRatioDelegate(self.theme_table))
        self.theme_table.itemSelectionChanged.connect(self.on_theme_selected)
        left_layout.addWidget(self.theme_table)

        splitter.addWidget(left_panel)

        # Right: Stock Details Table
        right_panel = QFrame()
        right_panel.setProperty("class", "panel")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(8, 8, 8, 8)
        right_layout.setSpacing(6)

        # Theme Header
        self.card_theme_header = QFrame()
        self.card_theme_header.setProperty("class", "card")
        card_layout = QVBoxLayout(self.card_theme_header)
        card_layout.setContentsMargins(8, 6, 8, 6)
        card_layout.setSpacing(4)

        t_line = QHBoxLayout()
        self.lbl_selected_theme = QLabel("👑 테마를 선택해 주세요")
        self.lbl_selected_theme.setStyleSheet("font-size: 15px; font-weight: 800; color: #39c5cf;")
        self.lbl_theme_rate = QLabel("")
        self.lbl_theme_rate.setStyleSheet("font-size: 14px; font-weight: 800; color: #f85149; margin-left: 6px;")
        t_line.addWidget(self.lbl_selected_theme)
        t_line.addWidget(self.lbl_theme_rate)
        t_line.addStretch()
        card_layout.addLayout(t_line)

        self.lbl_theme_desc = QLabel("")
        self.lbl_theme_desc.setWordWrap(True)
        self.lbl_theme_desc.setStyleSheet("font-size: 11px; color: #8b949e; background-color: #0d1117; border-radius: 4px; padding: 4px 6px;")
        card_layout.addWidget(self.lbl_theme_desc)

        right_layout.addWidget(self.card_theme_header)

        # Stock Table
        self.stock_table = QTableWidget()
        self.stock_table.setColumnCount(6)
        self.stock_table.setHorizontalHeaderLabels(["구분", "종목명", "현재가", "등락률", "거래대금", "사유/재료"])
        h_header_right = self.stock_table.horizontalHeader()
        h_header_right.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.stock_table.setColumnWidth(0, 65)
        self.stock_table.setColumnWidth(1, 105)
        self.stock_table.setColumnWidth(2, 75)
        self.stock_table.setColumnWidth(3, 110)
        self.stock_table.setColumnWidth(4, 100)
        self.stock_table.setColumnWidth(5, 200)
        h_header_right.setStretchLastSection(True)

        self.stock_table.verticalHeader().setVisible(False)
        self.stock_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.stock_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.stock_table.setItemDelegateForColumn(3, RateVisualDelegate(self.stock_table))
        self.stock_table.setItemDelegateForColumn(4, MoneyFlowDelegate(self.stock_table))
        self.stock_table.cellDoubleClicked.connect(self.on_stock_double_clicked)
        right_layout.addWidget(self.stock_table)

        splitter.addWidget(right_panel)
        splitter.setSizes([380, 520])

        tv_layout.addWidget(splitter)
        self.table_view_widget.setVisible(False)
        layout.addWidget(self.table_view_widget)

    def switch_view_mode(self, mode: str):
        self.current_view_mode = mode
        if mode == "card":
            self.btn_mode_card.setChecked(True)
            self.btn_mode_table.setChecked(False)
            self.scroll_area.setVisible(True)
            self.table_view_widget.setVisible(False)
        else:
            self.btn_mode_card.setChecked(False)
            self.btn_mode_table.setChecked(True)
            self.scroll_area.setVisible(False)
            self.table_view_widget.setVisible(True)
            if not self.selected_theme_no and self.themes_data:
                self.theme_table.selectRow(0)

    def update_themes(self, themes_list):
        self.themes_data = themes_list
        self.render_themes(themes_list)

    def render_themes(self, themes):
        # 1. Render Card View (TIMA Style)
        # Clear existing cards
        while self.card_layout.count():
            item = self.card_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.card_widgets.clear()

        for idx, t in enumerate(themes):
            rank = idx + 1
            card = ThemeCardWidget(rank, t)
            card.stockSelected.connect(self.stockSelected.emit)
            self.card_layout.addWidget(card)
            self.card_widgets.append(card)

        self.card_layout.addStretch()

        # 2. Render Table View (Classic 2-Panel)
        self.theme_table.setRowCount(len(themes))
        for row, t in enumerate(themes):
            rank = row + 1
            name = t.get("name", "")
            rate_str = str(t.get("changeRate", "0.00"))
            try:
                rate_val = float(rate_str)
            except Exception:
                rate_val = 0.0
            rise = t.get("riseCount", 0)
            fall = t.get("fallCount", 0)
            total = t.get("totalCount", 0)

            # Rank
            item_rank = QTableWidgetItem(f"{rank:02d}")
            item_rank.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if rank == 1:
                item_rank.setForeground(QColor(COLORS["gold"]))
                font = item_rank.font()
                font.setBold(True)
                item_rank.setFont(font)
            elif rank in (2, 3):
                item_rank.setForeground(QColor(COLORS["silver"]))
            self.theme_table.setItem(row, 0, item_rank)

            # Name
            item_name = QTableWidgetItem(name)
            item_name.setData(Qt.ItemDataRole.UserRole, t.get("no"))
            item_name.setToolTip(name)
            item_name.setFont(QFont("Pretendard", 10, QFont.Weight.Bold))
            self.theme_table.setItem(row, 1, item_name)

            # Rate
            sign = "+" if rate_val > 0 else ""
            item_rate = QTableWidgetItem(f"{sign}{rate_val:.2f}%")
            item_rate.setData(Qt.ItemDataRole.UserRole, rate_val)
            self.theme_table.setItem(row, 2, item_rate)

            # Rise/Fall
            item_rf = QTableWidgetItem(f"▲{rise} ▼{fall}")
            item_rf.setData(Qt.ItemDataRole.UserRole, (rise, fall, total))
            self.theme_table.setItem(row, 3, item_rf)

            # Total
            item_cnt = QTableWidgetItem(f"{total}")
            item_cnt.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_cnt.setForeground(QColor(COLORS["text_muted"]))
            self.theme_table.setItem(row, 4, item_cnt)

    def filter_themes(self, text):
        query = text.strip().lower()
        if not query:
            self.render_themes(self.themes_data)
            return
        filtered = [t for t in self.themes_data if query in t.get("name", "").lower()]
        self.render_themes(filtered)

    def on_theme_selected(self):
        row = self.theme_table.currentRow()
        if row < 0:
            return
        name_item = self.theme_table.item(row, 1)
        rate_item = self.theme_table.item(row, 2)
        if not name_item:
            return

        theme_no = name_item.data(Qt.ItemDataRole.UserRole)
        theme_name = name_item.text()
        fallback_rate = rate_item.data(Qt.ItemDataRole.UserRole) if rate_item else 0.0

        self.selected_theme_no = theme_no
        self.selected_theme_name = theme_name

        detail = engine.get_theme_detail(theme_no)
        stocks = detail.get("stocks", [])
        desc = detail.get("description", "")
        group_info = detail.get("groupInfo", {})
        self.current_stocks = stocks

        self.render_theme_header(theme_name, desc, group_info, stocks, fallback_rate)
        self.render_stocks_table(stocks)

    def render_theme_header(self, name, desc, group_info, stocks, fallback_rate=0.0):
        change_rate = group_info.get("changeRate")
        if change_rate is not None and str(change_rate) != "0.0" and str(change_rate) != "0":
            try:
                rate_num = float(change_rate)
                sign = "+" if rate_num > 0 else ""
                self.lbl_theme_rate.setText(f"{sign}{rate_num:.2f}%")
            except Exception:
                self.lbl_theme_rate.setText(f"{change_rate}%")
        else:
            rate_num = float(fallback_rate) if fallback_rate else 0.0
            sign = "+" if rate_num > 0 else ""
            self.lbl_theme_rate.setText(f"{sign}{rate_num:.2f}%")

        self.lbl_selected_theme.setText(f"👑 [{name}]")
        self.lbl_theme_desc.setText(f"💡 {desc.strip() if desc else '등록된 설명이 없습니다.'}")

    def render_stocks_table(self, stocks):
        self.stock_table.setRowCount(len(stocks))
        for row, s in enumerate(stocks):
            leader_tag = s.get("leader_tag", "후발주")
            code = s.get("itemCode", "")
            name = s.get("stockName", "")
            price = s.get("closePrice", "0")
            rate_str = s.get("fluctuationsRatio", "0.0")
            reason = s.get("theme_reason", "") or "-"
            try:
                rate_val = float(str(rate_str).replace(",", ""))
            except Exception:
                rate_val = 0.0
            
            try:
                val_raw = s.get("accumulatedTradingValueRaw", 0)
                val_num = float(str(val_raw).replace(",", "")) if val_raw else 0.0
                if val_num >= 100000000000:
                    val_str = f"🔥 {val_num / 100000000:,.0f}억"
                elif val_num >= 50000000000:
                    val_str = f"⚡ {val_num / 100000000:,.0f}억"
                elif val_num > 0:
                    val_str = f"{val_num / 100000000:,.0f}억"
                else:
                    val_str = "-"
            except Exception:
                val_num = 0.0
                val_str = "-"

            # Tag
            item_tag = QTableWidgetItem(leader_tag)
            item_tag.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if "👑" in leader_tag:
                item_tag.setForeground(QColor(COLORS["gold"]))
            elif "🥈" in leader_tag:
                item_tag.setForeground(QColor(COLORS["silver"]))
            elif "🥉" in leader_tag:
                item_tag.setForeground(QColor(COLORS["cyan"]))
            else:
                item_tag.setForeground(QColor(COLORS["text_dim"]))
            self.stock_table.setItem(row, 0, item_tag)

            # Name
            item_name = QTableWidgetItem(name)
            item_name.setData(Qt.ItemDataRole.UserRole, code)
            item_name.setFont(QFont("Pretendard", 10, QFont.Weight.Bold))
            if s.get("is_upper_limit"):
                item_name.setForeground(QColor(COLORS["gold"]))
            self.stock_table.setItem(row, 1, item_name)

            # Price
            item_price = QTableWidgetItem(f"{price}원")
            item_price.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.stock_table.setItem(row, 2, item_price)

            # Rate
            sign = "+" if rate_val > 0 else ""
            display_rate = f"★ 상한가 ({sign}{rate_val:.2f}%)" if rate_val >= 29.8 else f"{sign}{rate_val:.2f}%"
            item_rate = QTableWidgetItem(display_rate)
            item_rate.setData(Qt.ItemDataRole.UserRole, rate_val)
            self.stock_table.setItem(row, 3, item_rate)

            # Trading Value
            item_val = QTableWidgetItem(val_str)
            item_val.setData(Qt.ItemDataRole.UserRole, val_num)
            self.stock_table.setItem(row, 4, item_val)

            # Reason
            item_reason = QTableWidgetItem(reason)
            item_reason.setForeground(QColor("#8b949e"))
            item_reason.setToolTip(reason)
            self.stock_table.setItem(row, 5, item_reason)

    def on_stock_double_clicked(self, row, col):
        name_item = self.stock_table.item(row, 1)
        if name_item:
            code = name_item.data(Qt.ItemDataRole.UserRole) or ""
            name = name_item.text()
            self.stockSelected.emit(code, name)
