from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QLabel, QHeaderView, QFrame, QSplitter, QLineEdit, QPushButton,
    QStyledItemDelegate, QStyleOptionViewItem, QTextEdit, QStyle
)
from PyQt6.QtCore import Qt, pyqtSignal, QRect, QRectF
from PyQt6.QtGui import QColor, QFont, QPainter, QBrush, QPen, QLinearGradient
from config import COLORS
from core.engine import engine

class RateVisualDelegate(QStyledItemDelegate):
    """Visual Gauge Bar Delegate for Fluctuation Rate (등락률 시각 게이지 바)"""
    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index):
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Base background
        if option.state & QStyle.StateFlag.State_Selected:
            painter.fillRect(option.rect, QColor("#1f2937"))
        else:
            painter.fillRect(option.rect, QColor(COLORS["bg_surface"]))

        rate_val = index.data(Qt.ItemDataRole.UserRole)
        display_text = index.data(Qt.ItemDataRole.DisplayRole) or ""

        if rate_val is not None:
            try:
                rate_num = float(rate_val)
            except:
                rate_num = 0.0

            # Draw visual background bar
            rect = option.rect
            margin = 3
            bar_height = rect.height() - (margin * 2)
            
            # Width proportional to rate (max at 30% for upper limit)
            pct = min(max(abs(rate_num) / 30.0, 0.05), 1.0)
            bar_width = int((rect.width() - 10) * pct)

            if rate_num >= 29.8:
                # Upper limit: Glowing Red-Gold Gradient
                grad = QLinearGradient(rect.left() + 5, rect.top(), rect.left() + 5 + bar_width, rect.top())
                grad.setColorAt(0, QColor(255, 75, 75, 200))
                grad.setColorAt(1, QColor(255, 180, 0, 230))
                painter.setBrush(QBrush(grad))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawRoundedRect(QRect(rect.left() + 5, rect.top() + margin, bar_width, bar_height), 4, 4)
            elif rate_num > 0:
                # Rising: Red Heat Bar
                alpha = int(60 + (pct * 140))
                painter.setBrush(QBrush(QColor(248, 81, 73, alpha)))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawRoundedRect(QRect(rect.left() + 5, rect.top() + margin, bar_width, bar_height), 4, 4)
            elif rate_num < 0:
                # Falling: Blue Bar
                alpha = int(60 + (pct * 120))
                painter.setBrush(QBrush(QColor(88, 166, 255, alpha)))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawRoundedRect(QRect(rect.left() + 5, rect.top() + margin, bar_width, bar_height), 4, 4)

        # Draw text
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
    """Visual Power Bar Delegate for Trading Value (수급 쏠림 거래대금 파워 바)"""
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
            # Ratio based on 200 billion KRW (2,000억) benchmark
            pct = min(max(val_num / 200000000000.0, 0.05), 1.0)
            rect = option.rect
            margin = 3
            bar_height = rect.height() - (margin * 2)
            bar_width = int((rect.width() - 10) * pct)

            if val_num >= 100000000000: # 1000억+ : Ultra High Volume (Cyan-Gold Neon)
                grad = QLinearGradient(rect.left() + 5, rect.top(), rect.left() + 5 + bar_width, rect.top())
                grad.setColorAt(0, QColor(57, 197, 207, 180))
                grad.setColorAt(1, QColor(255, 215, 0, 220))
                painter.setBrush(QBrush(grad))
            elif val_num >= 50000000000: # 500억+ : High Volume
                painter.setBrush(QBrush(QColor(57, 197, 207, 140)))
            else:
                painter.setBrush(QBrush(QColor(57, 197, 207, 60)))

            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(QRect(rect.left() + 5, rect.top() + margin, bar_width, bar_height), 4, 4)

        # Draw text
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
    """Visual Mini Dual Ratio Bar for Theme Rise/Fall (테마 상승/하락 비중 미니 바)"""
    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index):
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if option.state & QStyle.StateFlag.State_Selected:
            painter.fillRect(option.rect, QColor("#1f2937"))
        else:
            painter.fillRect(option.rect, QColor(COLORS["bg_surface"]))

        counts = index.data(Qt.ItemDataRole.UserRole) # (rise, fall, total)
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

                # Rise bar (Red)
                if rise_w > 0:
                    painter.setBrush(QBrush(QColor(COLORS["bull_red"])))
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.drawRect(QRect(x, y, rise_w, bar_h))

                # Fall bar (Blue)
                if fall_w > 0:
                    painter.setBrush(QBrush(QColor(COLORS["bear_blue"])))
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.drawRect(QRect(x + rise_w, y, fall_w, bar_h))

        # Text
        painter.setPen(QPen(QColor(COLORS["text_muted"])))
        text_rect = option.rect.adjusted(4, 0, -4, -6)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, display_text)
        painter.restore()


class MarketCenterView(QWidget):
    """
    TOMA Pro Market Center (상용 서비스 수준의 실시간 주도테마 & 대장주 수급 대시보드)
    """
    stockSelected = pyqtSignal(str, str) # code, name

    def __init__(self, parent=None):
        super().__init__(parent)
        self.themes_data = []
        self.selected_theme_no = None
        self.selected_theme_name = ""
        self.current_stocks = []
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # ── Left: Theme Ranking Panel ─────────────────────────────────────
        left_panel = QFrame()
        left_panel.setProperty("class", "panel")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(10, 10, 10, 10)

        # Left Header
        lh_layout = QHBoxLayout()
        lbl_theme_title = QLabel("🔥 실시간 주도 테마 랭킹")
        lbl_theme_title.setStyleSheet("font-size: 15px; font-weight: 800; color: #f0f6fc;")
        
        self.theme_search = QLineEdit()
        self.theme_search.setPlaceholderText("테마 검색...")
        self.theme_search.setMaximumWidth(140)
        self.theme_search.textChanged.connect(self.filter_themes)
        
        lh_layout.addWidget(lbl_theme_title)
        lh_layout.addStretch()
        lh_layout.addWidget(self.theme_search)
        left_layout.addLayout(lh_layout)

        # Theme Table (Interactive Column Resizing Enabled)
        self.theme_table = QTableWidget()
        self.theme_table.setColumnCount(5)
        self.theme_table.setHorizontalHeaderLabels(["순위", "테마명", "등락률 (수급강도)", "상승/하락 비중", "종목"])
        
        h_header_left = self.theme_table.horizontalHeader()
        h_header_left.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.theme_table.setColumnWidth(0, 48)   # 순위
        self.theme_table.setColumnWidth(1, 155)  # 테마명 (넉넉하게 기본 확장)
        self.theme_table.setColumnWidth(2, 115)  # 등락률
        self.theme_table.setColumnWidth(3, 95)   # 상승/하락 비중
        self.theme_table.setColumnWidth(4, 45)   # 종목수
        h_header_left.setStretchLastSection(False)

        self.theme_table.verticalHeader().setVisible(False)
        self.theme_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.theme_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.theme_table.setItemDelegateForColumn(2, RateVisualDelegate(self.theme_table))
        self.theme_table.setItemDelegateForColumn(3, ThemeRatioDelegate(self.theme_table))
        self.theme_table.itemSelectionChanged.connect(self.on_theme_selected)
        left_layout.addWidget(self.theme_table)

        splitter.addWidget(left_panel)

        # ── Right: Theme Intelligence & Leader Stocks Panel ───────────────
        right_panel = QFrame()
        right_panel.setProperty("class", "panel")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(12, 12, 12, 12)
        right_layout.setSpacing(8)

        # 1. Top Theme Insight Card (상단 테마 수급 브리핑 헤더)
        self.card_theme_header = QFrame()
        self.card_theme_header.setProperty("class", "card")
        card_layout = QVBoxLayout(self.card_theme_header)
        card_layout.setContentsMargins(12, 10, 12, 10)
        card_layout.setSpacing(6)

        # Title & Badges Line
        t_line = QHBoxLayout()
        self.lbl_selected_theme = QLabel("👑 테마를 선택해 주세요")
        self.lbl_selected_theme.setStyleSheet("font-size: 17px; font-weight: 900; color: #39c5cf;")
        self.lbl_theme_rate = QLabel("")
        self.lbl_theme_rate.setStyleSheet("font-size: 16px; font-weight: 900; color: #f85149; margin-left: 6px;")
        
        self.badge_money_total = QLabel("💰 테마 총 거래대금: -")
        self.badge_money_total.setStyleSheet("background-color: #161b22; color: #39c5cf; border: 1px solid #30363d; border-radius: 4px; padding: 3px 8px; font-size: 12px; font-weight: 700;")

        self.badge_intensity = QLabel("🔥 수급 강도: 보통")
        self.badge_intensity.setStyleSheet("background-color: #161b22; color: #e3b341; border: 1px solid #30363d; border-radius: 4px; padding: 3px 8px; font-size: 12px; font-weight: 700;")

        t_line.addWidget(self.lbl_selected_theme)
        t_line.addWidget(self.lbl_theme_rate)
        t_line.addStretch()
        t_line.addWidget(self.badge_money_total)
        t_line.addWidget(self.badge_intensity)
        card_layout.addLayout(t_line)

        # Theme Description (테마 상승 배경 / 이유)
        self.lbl_theme_desc = QLabel("테마의 상승 배경과 핵심 재료 요약이 여기에 표시됩니다.")
        self.lbl_theme_desc.setWordWrap(True)
        self.lbl_theme_desc.setStyleSheet("font-size: 12px; color: #8b949e; line-height: 1.4; background-color: #0d1117; border-radius: 4px; padding: 6px 8px;")
        card_layout.addWidget(self.lbl_theme_desc)

        # Selected Stock Reason Live Briefing Box (선택 종목 재료 전문 브리핑)
        self.lbl_selected_stock_reason = QLabel("📌 [종목을 클릭하면 상세 편입 사유 / 사업 재료 전문이 여기에 표시됩니다]")
        self.lbl_selected_stock_reason.setWordWrap(True)
        self.lbl_selected_stock_reason.setStyleSheet("font-size: 12px; color: #e3b341; line-height: 1.4; background-color: #161b22; border: 1px solid #30363d; border-radius: 4px; padding: 6px 8px;")
        card_layout.addWidget(self.lbl_selected_stock_reason)

        right_layout.addWidget(self.card_theme_header)

        # 2. Stock Leader Table (Interactive Column Resizing Enabled)
        self.stock_table = QTableWidget()
        self.stock_table.setColumnCount(7)
        self.stock_table.setHorizontalHeaderLabels(["구분", "종목코드", "종목명", "현재가", "등락률 (상승탄력)", "거래대금 (수급쏠림)", "테마 편입 사유 / 재료 (클릭 시 상단에 전문 표시)"])
        
        h_header_right = self.stock_table.horizontalHeader()
        h_header_right.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.stock_table.setColumnWidth(0, 68)   # 구분
        self.stock_table.setColumnWidth(1, 68)   # 코드
        self.stock_table.setColumnWidth(2, 110)  # 종목명
        self.stock_table.setColumnWidth(3, 80)   # 현재가
        self.stock_table.setColumnWidth(4, 135)  # 등락률
        self.stock_table.setColumnWidth(5, 115)  # 거래대금
        self.stock_table.setColumnWidth(6, 260)  # 재료
        h_header_right.setStretchLastSection(True)

        self.stock_table.verticalHeader().setVisible(False)
        self.stock_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.stock_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.stock_table.setItemDelegateForColumn(4, RateVisualDelegate(self.stock_table))
        self.stock_table.setItemDelegateForColumn(5, MoneyFlowDelegate(self.stock_table))
        self.stock_table.itemSelectionChanged.connect(self.on_stock_row_selected)
        self.stock_table.cellDoubleClicked.connect(self.on_stock_double_clicked)
        right_layout.addWidget(self.stock_table)

        splitter.addWidget(right_panel)
        splitter.setSizes([470, 770])

        layout.addWidget(splitter)

    def update_themes(self, themes_list):
        self.themes_data = themes_list
        self.render_themes(themes_list)

    def render_themes(self, themes):
        self.theme_table.setRowCount(len(themes))
        for row, t in enumerate(themes):
            rank = row + 1
            name = t.get("name", "")
            rate_str = str(t.get("changeRate", "0.00"))
            try:
                rate_val = float(rate_str)
            except:
                rate_val = 0.0
            rise = t.get("riseCount", 0)
            fall = t.get("fallCount", 0)
            total = t.get("totalCount", 0)

            # 1. Rank Item
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

            # 2. Theme Name
            item_name = QTableWidgetItem(name)
            item_name.setData(Qt.ItemDataRole.UserRole, t.get("no"))
            item_name.setToolTip(name)
            item_name.setFont(QFont("Pretendard", 10, QFont.Weight.Bold))
            self.theme_table.setItem(row, 1, item_name)

            # 3. Change Rate (Delegate will draw gauge)
            sign = "+" if rate_val > 0 else ""
            item_rate = QTableWidgetItem(f"{sign}{rate_val:.2f}%")
            item_rate.setData(Qt.ItemDataRole.UserRole, rate_val)
            self.theme_table.setItem(row, 2, item_rate)

            # 4. Rise / Fall Ratio (Delegate will draw mini bar)
            item_rf = QTableWidgetItem(f"▲{rise}  ▼{fall}")
            item_rf.setData(Qt.ItemDataRole.UserRole, (rise, fall, total))
            self.theme_table.setItem(row, 3, item_rf)

            # 5. Total Count
            item_cnt = QTableWidgetItem(f"{total}")
            item_cnt.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_cnt.setForeground(QColor(COLORS["text_muted"]))
            self.theme_table.setItem(row, 4, item_cnt)

        # Auto select first theme if nothing selected
        if not self.selected_theme_no and themes:
            self.theme_table.selectRow(0)

    def filter_themes(self, text):
        query = text.strip().lower()
        if not query:
            self.render_themes(self.themes_data)
            return
        filtered = [t for t in self.themes_data if query in t.get("name", "").lower()]
        self.render_themes(filtered)

    def on_theme_selected(self):
        selected_items = self.theme_table.selectedItems()
        if not selected_items:
            return
        row = self.theme_table.currentRow()
        name_item = self.theme_table.item(row, 1)
        rate_item = self.theme_table.item(row, 2)
        if not name_item:
            return

        theme_no = name_item.data(Qt.ItemDataRole.UserRole)
        theme_name = name_item.text()
        
        # Exact theme change rate from table
        fallback_rate = rate_item.data(Qt.ItemDataRole.UserRole) if rate_item else 0.0

        self.selected_theme_no = theme_no
        self.selected_theme_name = theme_name
        
        # Fetch Full Theme Detail (Stocks, Description, Reasons)
        detail = engine.get_theme_detail(theme_no)
        stocks = detail.get("stocks", [])
        desc = detail.get("description", "")
        group_info = detail.get("groupInfo", {})
        self.current_stocks = stocks

        self.render_theme_header(theme_name, desc, group_info, stocks, fallback_rate)
        self.render_stocks(stocks)

    def render_theme_header(self, name, desc, group_info, stocks, fallback_rate=0.0):
        change_rate = group_info.get("changeRate")
        if change_rate is not None and str(change_rate) != "0.0" and str(change_rate) != "0":
            try:
                rate_num = float(change_rate)
                sign = "+" if rate_num > 0 else ""
                self.lbl_theme_rate.setText(f"{sign}{rate_num:.2f}%")
            except:
                self.lbl_theme_rate.setText(f"{change_rate}%")
        else:
            # Fallback to theme table rate
            rate_num = float(fallback_rate) if fallback_rate else 0.0
            sign = "+" if rate_num > 0 else ""
            self.lbl_theme_rate.setText(f"{sign}{rate_num:.2f}%")

        self.lbl_selected_theme.setText(f"👑 [{name}] 주도테마 인텔리전스")

        # Sum total trading volume of theme
        total_val_sum = 0
        upper_limit_count = 0
        billion_count = 0 # 1000억 이상

        for s in stocks:
            try:
                v_raw = s.get("accumulatedTradingValueRaw", 0)
                v_num = float(str(v_raw).replace(",", "")) if v_raw else 0.0
                total_val_sum += v_num
                if v_num >= 100000000000:
                    billion_count += 1
            except:
                pass
            if s.get("is_upper_limit"):
                upper_limit_count += 1

        val_total_str = f"{total_val_sum / 100000000:,.0f}억원" if total_val_sum > 0 else "-"
        self.badge_money_total.setText(f"💰 테마 총 거래대금: {val_total_str}")

        # Compute Intensity
        if upper_limit_count >= 1 or billion_count >= 2:
            self.badge_intensity.setText(f"🔥 수급 집중도: 최상 (상한가 {upper_limit_count}개 / 1000억+ {billion_count}개)")
            self.badge_intensity.setStyleSheet("background-color: #3b1d22; color: #ff7b72; border: 1px solid #da3633; border-radius: 4px; padding: 3px 8px; font-size: 12px; font-weight: 800;")
        elif total_val_sum >= 200000000000:
            self.badge_intensity.setText("⚡ 수급 집중도: 강력 (거래대금 2000억+)")
            self.badge_intensity.setStyleSheet("background-color: #272115; color: #e3b341; border: 1px solid #d29922; border-radius: 4px; padding: 3px 8px; font-size: 12px; font-weight: 800;")
        else:
            self.badge_intensity.setText("ℹ️ 수급 집중도: 보통")
            self.badge_intensity.setStyleSheet("background-color: #161b22; color: #8b949e; border: 1px solid #30363d; border-radius: 4px; padding: 3px 8px; font-size: 12px; font-weight: 700;")

        # Description
        clean_desc = desc.strip() if desc else "등록된 테마 상세 설명이 없습니다."
        self.lbl_theme_desc.setText(f"💡 [테마 핵심 재료 / 상승 배경]  {clean_desc}")

        # Reset selected stock detail to default leader or notice
        if stocks:
            first = stocks[0]
            r = first.get("theme_reason", "")
            s_name = first.get("stockName", "")
            s_code = first.get("itemCode", "")
            if r:
                self.lbl_selected_stock_reason.setText(f"👑 [대장주: {s_name} ({s_code}) 편입 사유]  {r}")
            else:
                self.lbl_selected_stock_reason.setText(f"👑 [대장주: {s_name} ({s_code})] 테마 주도 대장주")
        else:
            self.lbl_selected_stock_reason.setText("📌 [종목을 클릭하면 상세 편입 사유 / 사업 재료 전문이 여기에 표시됩니다]")

    def render_stocks(self, stocks):
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
                if val_num >= 100000000000: # 1000억+
                    val_str = f"🔥 {val_num / 100000000:,.0f}억"
                elif val_num >= 50000000000: # 500억+
                    val_str = f"⚡ {val_num / 100000000:,.0f}억"
                elif val_num > 0:
                    val_str = f"{val_num / 100000000:,.0f}억"
                else:
                    val_str = "-"
            except Exception:
                val_num = 0.0
                val_str = "-"

            # 1. Leader Tag (👑 대장주 / 🥈 2등주)
            item_tag = QTableWidgetItem(leader_tag)
            item_tag.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if "👑" in leader_tag:
                item_tag.setForeground(QColor(COLORS["gold"]))
                font = item_tag.font()
                font.setBold(True)
                item_tag.setFont(font)
            elif "🥈" in leader_tag:
                item_tag.setForeground(QColor(COLORS["silver"]))
            elif "🥉" in leader_tag:
                item_tag.setForeground(QColor(COLORS["cyan"]))
            else:
                item_tag.setForeground(QColor(COLORS["text_dim"]))
            self.stock_table.setItem(row, 0, item_tag)

            # 2. Code
            item_code = QTableWidgetItem(code)
            item_code.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_code.setForeground(QColor(COLORS["text_muted"]))
            self.stock_table.setItem(row, 1, item_code)

            # 3. Stock Name
            item_name = QTableWidgetItem(name)
            item_name.setFont(QFont("Pretendard", 10, QFont.Weight.Bold))
            item_name.setToolTip(f"{name} ({code})")
            if s.get("is_upper_limit"):
                item_name.setForeground(QColor(COLORS["gold"]))
            self.stock_table.setItem(row, 2, item_name)

            # 4. Price
            item_price = QTableWidgetItem(f"{price}원")
            item_price.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.stock_table.setItem(row, 3, item_price)

            # 5. Rate (Visual Delegate)
            sign = "+" if rate_val > 0 else ""
            if rate_val >= 29.8:
                display_rate = f"★ 상한가 ({sign}{rate_val:.2f}%)"
            else:
                display_rate = f"{sign}{rate_val:.2f}%"
            item_rate = QTableWidgetItem(display_rate)
            item_rate.setData(Qt.ItemDataRole.UserRole, rate_val)
            self.stock_table.setItem(row, 4, item_rate)

            # 6. Trading Value (Visual Delegate)
            item_val = QTableWidgetItem(val_str)
            item_val.setData(Qt.ItemDataRole.UserRole, val_num)
            self.stock_table.setItem(row, 5, item_val)

            # 7. Theme 편입 사유 / 재료
            item_reason = QTableWidgetItem(reason)
            item_reason.setForeground(QColor("#8b949e"))
            item_reason.setToolTip(reason if reason != "-" else "상세 편입 사유가 없습니다.")
            self.stock_table.setItem(row, 6, item_reason)

    def on_stock_row_selected(self):
        row = self.stock_table.currentRow()
        if 0 <= row < len(self.current_stocks):
            s = self.current_stocks[row]
            name = s.get("stockName", "")
            code = s.get("itemCode", "")
            reason = s.get("theme_reason", "")
            if reason:
                self.lbl_selected_stock_reason.setText(f"📌 [{name} ({code}) 편입 사유]  {reason}")
            else:
                self.lbl_selected_stock_reason.setText(f"📌 [{name} ({code})] 등록된 편입 상세 사유가 없습니다.")

    def on_stock_double_clicked(self, row, col):
        code_item = self.stock_table.item(row, 1)
        name_item = self.stock_table.item(row, 2)
        if code_item and name_item:
            self.stockSelected.emit(code_item.text(), name_item.text())
