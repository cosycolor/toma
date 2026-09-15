from config import COLORS

QSS_DARK_THEME = f"""
QMainWindow {{
    background-color: {COLORS['bg_main']};
    color: {COLORS['text_main']};
}}

QWidget {{
    background-color: {COLORS['bg_main']};
    color: {COLORS['text_main']};
    font-family: 'Pretendard', 'Malgun Gothic', 'Segoe UI', sans-serif;
    font-size: 13px;
}}

/* Top Navigation Bar */
QFrame#navBar {{
    background-color: {COLORS['bg_surface']};
    border-bottom: 1px solid {COLORS['border']};
    padding: 6px 12px;
}}

QPushButton.nav-btn {{
    background-color: transparent;
    color: {COLORS['text_muted']};
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 700;
    font-size: 14px;
    text-align: center;
}}

QPushButton.nav-btn:hover {{
    background-color: {COLORS['bg_surface_alt']};
    color: {COLORS['text_main']};
}}

QPushButton.nav-btn:checked {{
    background-color: {COLORS['bg_surface_alt']};
    color: {COLORS['cyan']};
    border-bottom: 2px solid {COLORS['cyan']};
}}

/* Panels & Cards */
QFrame.panel {{
    background-color: {COLORS['bg_surface']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
}}

QFrame.card {{
    background-color: {COLORS['bg_surface_alt']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 8px;
}}

/* Tables */
QTableWidget {{
    background-color: {COLORS['bg_surface']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    gridline-color: {COLORS['border']};
    color: {COLORS['text_main']};
    selection-background-color: {COLORS['bg_hover']};
    selection-color: {COLORS['text_main']};
}}

QTableWidget::item {{
    padding: 6px;
    border-bottom: 1px solid {COLORS['border']};
}}

QTableWidget::item:selected {{
    background-color: #1f2937;
}}

QHeaderView::section {{
    background-color: {COLORS['bg_surface_alt']};
    color: {COLORS['text_muted']};
    padding: 6px 8px;
    border: none;
    border-bottom: 1px solid {COLORS['border']};
    font-weight: 700;
    font-size: 12px;
}}

/* Scrollbar */
QScrollBar:vertical {{
    background: {COLORS['bg_main']};
    width: 8px;
    margin: 0px;
}}

QScrollBar::handle:vertical {{
    background: {COLORS['border']};
    min-height: 20px;
    border-radius: 4px;
}}

QScrollBar::handle:vertical:hover {{
    background: {COLORS['text_muted']};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

/* Status Bar */
QStatusBar {{
    background-color: {COLORS['bg_surface']};
    color: {COLORS['text_muted']};
    border-top: 1px solid {COLORS['border']};
    font-size: 12px;
}}

/* Buttons */
QPushButton.action-btn {{
    background-color: {COLORS['bg_surface_alt']};
    color: {COLORS['text_main']};
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    padding: 4px 10px;
    font-weight: 600;
}}

QPushButton.action-btn:hover {{
    background-color: {COLORS['bg_hover']};
    border-color: {COLORS['border_focus']};
}}

QLineEdit, QTextEdit {{
    background-color: {COLORS['bg_surface_alt']};
    color: {COLORS['text_main']};
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    padding: 6px;
}}

QLineEdit:focus, QTextEdit:focus {{
    border: 1px solid {COLORS['border_focus']};
}}
"""
