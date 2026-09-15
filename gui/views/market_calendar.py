from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLabel, QHeaderView, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont
from config import COLORS
from core.engine import engine

class MarketCalendarView(QWidget):
    """
    TOMA Market Calendar (마켓일정 캘린더)
    - Major Economic Indicators (FOMC, CPI, Rates)
    - IPO, Lockup Expiry, Dividends
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        panel = QFrame()
        panel.setProperty("class", "panel")
        p_layout = QVBoxLayout(panel)
        p_layout.setContentsMargins(10, 10, 10, 10)

        lbl_title = QLabel("📅 국내외 주요 마켓 경제 일정 & 증시 이벤트")
        lbl_title.setStyleSheet("font-size: 16px; font-weight: 800; color: #f0f6fc; margin-bottom: 6px;")
        p_layout.addWidget(lbl_title)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["일자", "시간", "국가/구분", "주요 이벤트 / 지표 발표", "영향도(중요도)"])
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        p_layout.addWidget(self.table)

        layout.addWidget(panel)
        self.load_calendar()

    def load_calendar(self):
        events = engine.get_economic_calendar()
        self.table.setRowCount(len(events))
        for row, ev in enumerate(events):
            # 1. Date
            item_date = QTableWidgetItem(ev.get("date", ""))
            item_date.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 0, item_date)

            # 2. Time
            item_time = QTableWidgetItem(ev.get("time", ""))
            item_time.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_time.setForeground(QColor(COLORS["text_muted"]))
            self.table.setItem(row, 1, item_time)

            # 3. Country
            item_country = QTableWidgetItem(ev.get("country", ""))
            item_country.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 2, item_country)

            # 4. Event
            item_ev = QTableWidgetItem(ev.get("event", ""))
            item_ev.setFont(QFont("Pretendard", 10, QFont.Weight.Bold))
            self.table.setItem(row, 3, item_ev)

            # 5. Impact
            impact = ev.get("impact", "")
            item_imp = QTableWidgetItem()
            item_imp.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if impact == "VERY_HIGH":
                item_imp.setText("🚨 초특급 (최대변동)")
                item_imp.setForeground(QColor(COLORS["bull_red"]))
                font = item_imp.font()
                font.setBold(True)
                item_imp.setFont(font)
            elif impact == "HIGH":
                item_imp.setText("⚠️ 중요 (고변동)")
                item_imp.setForeground(QColor(COLORS["gold"]))
            else:
                item_imp.setText("ℹ️ 일반")
                item_imp.setForeground(QColor(COLORS["cyan"]))
            self.table.setItem(row, 4, item_imp)
