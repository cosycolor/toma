import os
import json
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLabel, QHeaderView, QFrame, QTextEdit, QPushButton, QLineEdit,
    QMessageBox, QAbstractItemView
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QColor, QFont
from config import COLORS, WATCHLIST_FILE, MEMO_FILE
from core.engine import engine

class WatchlistRefreshThread(QThread):
    """Worker thread to fetch latest quotes for watchlist stocks"""
    quotesUpdated = pyqtSignal(list)

    def __init__(self, stocks):
        super().__init__()
        self.stocks = stocks

    def run(self):
        updated = []
        for item in self.stocks:
            code = item.get("code", "")
            basic = engine.get_stock_basic(code) if code else None
            price = item.get("price", "-")
            rate = item.get("rate", "0.00%")
            val_str = item.get("trading_val", "-")
            name = item.get("name", "")

            if basic:
                name = basic.get("stockName", name)
                price = f"{basic.get('closePrice', '0')}원"
                rate = f"{basic.get('fluctuationsRatio', '0.00')}%"
                val_raw = basic.get("accumulatedTradingValueRaw", 0)
                try:
                    val_num = float(str(val_raw).replace(",", "")) if val_raw else 0.0
                    val_str = f"{val_num / 100000000:,.0f}억" if val_num > 0 else "-"
                except:
                    val_str = "-"

            updated.append({
                "code": code,
                "name": name,
                "price": price,
                "rate": rate,
                "trading_val": val_str,
                "memo": item.get("memo", "")
            })
        self.quotesUpdated.emit(updated)

class WatchlistView(QWidget):
    """
    TOMA Watchlist & Trader Notepad (관심종목 및 트레이딩 메모장)
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.watchlist_data = []
        self.init_ui()
        self.load_saved_data()

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # ── Left: Watchlist Table Panel ────────────────────────────────────
        left_panel = QFrame()
        left_panel.setProperty("class", "panel")
        l_layout = QVBoxLayout(left_panel)
        l_layout.setContentsMargins(10, 10, 10, 10)

        lh_layout = QHBoxLayout()
        lbl_w = QLabel("⭐ 나의 관심종목 (Watchlist)")
        lbl_w.setStyleSheet("font-size: 15px; font-weight: 800; color: #f0f6fc;")
        
        self.inp_code = QLineEdit()
        self.inp_code.setPlaceholderText("종목명 또는 코드 입력 (예: 삼성전자, 005930)")
        self.inp_code.setMinimumWidth(220)
        self.inp_code.returnPressed.connect(self.search_and_add_stock)

        btn_add = QPushButton("🔍 종목 추가")
        btn_add.setProperty("class", "action-btn")
        btn_add.clicked.connect(self.search_and_add_stock)

        btn_refresh = QPushButton("시세 갱신")
        btn_refresh.setProperty("class", "action-btn")
        btn_refresh.clicked.connect(self.refresh_watchlist_quotes)

        btn_delete = QPushButton("선택 삭제")
        btn_delete.setStyleSheet("background-color: #3b1d22; color: #ff7b72; border: 1px solid #da3633; border-radius: 4px; padding: 4px 10px; font-weight: 700;")
        btn_delete.clicked.connect(self.delete_selected_stock)

        lh_layout.addWidget(lbl_w)
        lh_layout.addStretch()
        lh_layout.addWidget(self.inp_code)
        lh_layout.addWidget(btn_add)
        lh_layout.addWidget(btn_refresh)
        lh_layout.addWidget(btn_delete)
        l_layout.addLayout(lh_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["종목코드", "종목명", "현재가", "등락률", "거래대금", "관심 메모 (더블클릭 편집)"])
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.itemChanged.connect(self.on_table_item_changed)
        l_layout.addWidget(self.table)

        layout.addWidget(left_panel, 65)

        # ── Right: Quick Trader Notepad ────────────────────────────────────
        right_panel = QFrame()
        right_panel.setProperty("class", "panel")
        r_layout = QVBoxLayout(right_panel)
        r_layout.setContentsMargins(10, 10, 10, 10)

        rh_layout = QHBoxLayout()
        lbl_memo = QLabel("📝 장중 전략 및 트레이딩 메모장")
        lbl_memo.setStyleSheet("font-size: 15px; font-weight: 800; color: #39c5cf;")
        btn_save_memo = QPushButton("메모 저장")
        btn_save_memo.setProperty("class", "action-btn")
        btn_save_memo.clicked.connect(self.save_memo_file)
        rh_layout.addWidget(lbl_memo)
        rh_layout.addStretch()
        rh_layout.addWidget(btn_save_memo)
        r_layout.addLayout(rh_layout)

        self.memo_edit = QTextEdit()
        self.memo_edit.setPlaceholderText("오늘의 매매 원칙, 주도 테마 시나리오, 목표가/손절가를 자유롭게 기록하세요...")
        self.memo_edit.textChanged.connect(self.auto_save_memo)
        r_layout.addWidget(self.memo_edit)

        layout.addWidget(right_panel, 35)

    def search_and_add_stock(self):
        query = self.inp_code.text().strip()
        if not query:
            return

        # 1. Check if input is direct 6-digit stock code
        found_code = None
        found_name = None

        if len(query) == 6 and query.isdigit():
            basic = engine.get_stock_basic(query)
            if basic and basic.get("stockName"):
                found_code = query
                found_name = basic.get("stockName")
        
        # 2. Search by autocomplete if not direct or failed
        if not found_code:
            items = engine.search_stock(query)
            if items:
                first = items[0]
                found_code = first.get("code")
                found_name = first.get("name")

        if not found_code or not found_name:
            QMessageBox.warning(self, "종목 검색 실패", f"'{query}'에 해당하는 국내 주식 종목을 찾을 수 없습니다.")
            return

        # Check duplicated
        for item in self.watchlist_data:
            if item.get("code") == found_code:
                QMessageBox.information(self, "알림", f"'{found_name}({found_code})'은(는) 이미 관심종목에 등록되어 있습니다.")
                self.inp_code.clear()
                return

        # Fetch latest price info
        basic = engine.get_stock_basic(found_code)
        price_str = f"{basic.get('closePrice', '0')}원" if basic else "-"
        rate_str = f"{basic.get('fluctuationsRatio', '0.00')}%" if basic else "0.00%"
        val_raw = basic.get("accumulatedTradingValueRaw", 0) if basic else 0
        try:
            val_num = float(str(val_raw).replace(",", "")) if val_raw else 0.0
            val_str = f"{val_num / 100000000:,.0f}억" if val_num > 0 else "-"
        except:
            val_str = "-"

        new_stock = {
            "code": found_code,
            "name": found_name,
            "price": price_str,
            "rate": rate_str,
            "trading_val": val_str,
            "memo": "주요 테마 관심주"
        }

        self.watchlist_data.append(new_stock)
        self.render_watchlist()
        self.save_watchlist_file()
        self.inp_code.clear()

    def add_stock(self, code: str, name: str, memo: str = ""):
        """External helper to add stock from market center"""
        if any(item.get("code") == code for item in self.watchlist_data):
            return
        basic = engine.get_stock_basic(code)
        price_str = f"{basic.get('closePrice', '0')}원" if basic else "-"
        rate_str = f"{basic.get('fluctuationsRatio', '0.00')}%" if basic else "0.00%"
        val_raw = basic.get("accumulatedTradingValueRaw", 0) if basic else 0
        try:
            val_num = float(str(val_raw).replace(",", "")) if val_raw else 0.0
            val_str = f"{val_num / 100000000:,.0f}억" if val_num > 0 else "-"
        except:
            val_str = "-"

        self.watchlist_data.append({
            "code": code,
            "name": name,
            "price": price_str,
            "rate": rate_str,
            "trading_val": val_str,
            "memo": memo or "테마 주도주"
        })
        self.render_watchlist()
        self.save_watchlist_file()

    def render_watchlist(self):
        self.table.blockSignals(True)
        self.table.setRowCount(len(self.watchlist_data))
        for row, item in enumerate(self.watchlist_data):
            code = item.get("code", "")
            name = item.get("name", "")
            price = item.get("price", "-")
            rate = item.get("rate", "0.00%")
            val = item.get("trading_val", "-")
            memo = item.get("memo", "")

            # Code
            it_code = QTableWidgetItem(code)
            it_code.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            it_code.setFlags(it_code.flags() & ~Qt.ItemFlag.ItemIsEditable)
            it_code.setForeground(QColor(COLORS["text_muted"]))
            self.table.setItem(row, 0, it_code)

            # Name
            it_name = QTableWidgetItem(name)
            it_name.setFont(QFont("Pretendard", 10, QFont.Weight.Bold))
            it_name.setFlags(it_name.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 1, it_name)

            # Price
            it_price = QTableWidgetItem(price)
            it_price.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            it_price.setFlags(it_price.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 2, it_price)

            # Rate
            try:
                rate_num = float(rate.replace("%", "").replace(",", ""))
            except:
                rate_num = 0.0
            sign = "+" if rate_num > 0 else ""
            it_rate = QTableWidgetItem(f"{sign}{rate_num:.2f}%")
            it_rate.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            it_rate.setFlags(it_rate.flags() & ~Qt.ItemFlag.ItemIsEditable)
            if rate_num > 0:
                it_rate.setForeground(QColor(COLORS["bull_red"]))
                font = it_rate.font()
                font.setBold(True)
                it_rate.setFont(font)
            elif rate_num < 0:
                it_rate.setForeground(QColor(COLORS["bear_blue"]))
            self.table.setItem(row, 3, it_rate)

            # Trading Value
            it_val = QTableWidgetItem(val)
            it_val.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            it_val.setFlags(it_val.flags() & ~Qt.ItemFlag.ItemIsEditable)
            it_val.setForeground(QColor(COLORS["cyan"]))
            self.table.setItem(row, 4, it_val)

            # Memo (Editable)
            it_memo = QTableWidgetItem(memo)
            self.table.setItem(row, 5, it_memo)

        self.table.blockSignals(False)

    def on_table_item_changed(self, item):
        row = item.row()
        col = item.column()
        if col == 5 and 0 <= row < len(self.watchlist_data):
            self.watchlist_data[row]["memo"] = item.text()
            self.save_watchlist_file()

    def delete_selected_stock(self):
        selected_rows = sorted(set(index.row() for index in self.table.selectedIndexes()), reverse=True)
        if not selected_rows:
            QMessageBox.information(self, "선택 안내", "삭제할 관심종목을 테이블에서 선택해 주세요.")
            return
        for r in selected_rows:
            if 0 <= r < len(self.watchlist_data):
                del self.watchlist_data[r]
        self.render_watchlist()
        self.save_watchlist_file()

    def refresh_watchlist_quotes(self):
        if not self.watchlist_data:
            return
        self.worker = WatchlistRefreshThread(self.watchlist_data)
        self.worker.quotesUpdated.connect(self.on_quotes_updated)
        self.worker.start()

    def on_quotes_updated(self, updated_list):
        self.watchlist_data = updated_list
        self.render_watchlist()
        self.save_watchlist_file()

    def load_saved_data(self):
        # 1. Load watchlist JSON
        os.makedirs(os.path.dirname(WATCHLIST_FILE), exist_ok=True)
        if os.path.exists(WATCHLIST_FILE):
            try:
                with open(WATCHLIST_FILE, "r", encoding="utf-8") as f:
                    self.watchlist_data = json.load(f)
            except Exception:
                self.watchlist_data = []
        else:
            self.watchlist_data = []
        
        self.render_watchlist()
        if self.watchlist_data:
            self.refresh_watchlist_quotes()

        # 2. Load memo text
        if os.path.exists(MEMO_FILE):
            try:
                with open(MEMO_FILE, "r", encoding="utf-8") as f:
                    self.memo_edit.setText(f.read())
            except Exception:
                pass
        else:
            default_memo = "📌 [오늘의 주도 테마 체크포인트]\n- 양자암호/로봇 테마 거래대금 쏠림 확인\n- 대장주 상한가 안착 시 2등주 눌림목 관망\n- 09:30 이후 거래대금 500억 이상 주도주만 공략"
            self.memo_edit.setText(default_memo)

    def save_watchlist_file(self):
        try:
            with open(WATCHLIST_FILE, "w", encoding="utf-8") as f:
                json.dump(self.watchlist_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print("Error saving watchlist:", e)

    def auto_save_memo(self):
        self.save_memo_file()

    def save_memo_file(self):
        try:
            with open(MEMO_FILE, "w", encoding="utf-8") as f:
                f.write(self.memo_edit.toPlainText())
        except Exception as e:
            print("Error saving memo:", e)
