"""Fluent-inspired Qt primitives using the installed Windows icon font."""
from PySide6.QtCore import QRectF, QSize, Qt
from PySide6.QtGui import QColor, QFont, QFontDatabase, QIcon, QPainter, QPalette, QPixmap
from PySide6.QtWidgets import QLabel, QPushButton, QSizePolicy, QStyle, QStyledItemDelegate, QStyleOptionViewItem

GLYPHS = {'activity':'\ue9d9', 'settings':'\ue713', 'about':'\ue946', 'exit':'\ue8bb',
          'folder':'\ue8b7', 'play':'\ue768', 'pause':'\ue769', 'search':'\ue721',
          'undo':'\ue7a7', 'refresh':'\ue72c', 'document':'\ue8a5', 'image':'\ueb9f',
          'chevron':'\ue70d', 'check':'\ue73e', 'history':'\ue81c', 'external':'\ue8a7'}
_icons = {}


def fluent_icon(name, color='#616161'):
    key = (name, color)
    if key not in _icons:
        pixmap = QPixmap(48, 48)
        pixmap.setDevicePixelRatio(2)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        family = 'Segoe Fluent Icons' if 'Segoe Fluent Icons' in QFontDatabase.families() else 'Segoe MDL2 Assets'
        font = QFont(family)
        font.setPixelSize(20)
        painter.setFont(font)
        painter.setPen(QColor(color))
        painter.drawText(QRectF(0, 0, 24, 24), Qt.AlignmentFlag.AlignCenter, GLYPHS[name])
        painter.end()
        _icons[key] = QIcon(pixmap)
    return _icons[key]


class NavigationButton(QPushButton):
    def paintEvent(self, event):
        super().paintEvent(event)
        if self.isChecked():
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor('#005FB8'))
            painter.drawRoundedRect(QRectF(0, (self.height()-18)/2, 3, 18), 1.5, 1.5)


class ElidedLabel(QLabel):
    def __init__(self, text='', parent=None):
        super().__init__(parent)
        self.full_text = text
        self.setMinimumWidth(0)
        self.setSizePolicy(QSizePolicy.Policy.Ignored,QSizePolicy.Policy.Preferred)
        self.setTextFormat(Qt.TextFormat.PlainText)
        self.setText(text)

    def setText(self, text):
        self.full_text = text
        self.setToolTip(text)
        super().setText(self.fontMetrics().elidedText(text, Qt.TextElideMode.ElideMiddle, max(self.width(), 40)))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.setText(self.full_text)


class StateDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        opt = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)
        text = opt.text
        opt.text = ''
        style = opt.widget.style()
        style.drawControl(QStyle.ControlElement.CE_ItemViewItem, opt, painter, opt.widget)
        background, foreground = {
            'Completed': ('#E8F3EC','#0F6B3B'), 'Undone': ('#F1F1F1','#616161'),
            'Pending': ('#E5F1FB','#005FB8'), 'Undo pending': ('#E5F1FB','#005FB8'),
            'Failed': ('#FDE7E9','#A4262C'), 'Review': ('#FFF4CE','#775B00'),
        }.get(text, ('#F1F1F1','#616161'))
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        font = QFont(opt.font)
        font.setPixelSize(12)
        painter.setFont(font)
        width = min(option.rect.width()-12, painter.fontMetrics().horizontalAdvance(text)+22)
        rect = QRectF(option.rect.x()+6, option.rect.center().y()-12, width, 24)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(background))
        painter.drawRoundedRect(rect, 12, 12)
        painter.setPen(QColor(foreground))
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, text)
        painter.restore()


def apply_theme(app):
    palette = QPalette()
    for role, color in {'Window':'#F9F9F9','WindowText':'#1B1B1B','Base':'#FFFFFF',
        'AlternateBase':'#FFFFFF','Text':'#1B1B1B','Button':'#FFFFFF','ButtonText':'#1B1B1B',
        'ToolTipBase':'#FFFFFF','ToolTipText':'#1B1B1B','Highlight':'#005FB8',
        'HighlightedText':'#FFFFFF','Link':'#005FB8','Light':'#FFFFFF','Midlight':'#F3F3F3',
        'Dark':'#8A8A8A','Mid':'#E5E5E5','Shadow':'#616161','BrightText':'#A4262C'}.items():
        palette.setColor(getattr(QPalette.ColorRole, role), QColor(color))
    for role in (QPalette.ColorRole.Text,QPalette.ColorRole.WindowText,QPalette.ColorRole.ButtonText):
        palette.setColor(QPalette.ColorGroup.Disabled,role,QColor('#8A8A8A'))
    app.setPalette(palette)


STYLESHEET = '''
QWidget { font-family: "Segoe UI"; font-size: 14px; color: #1B1B1B; }
QMainWindow, #Workspace { background: #F9F9F9; }
#Navigation { background: #F3F3F3; }
QLabel#Title { font-family: "Segoe UI Variable", "Segoe UI"; font-size: 28px; font-weight: 600; }
QLabel#Heading { font-size: 18px; font-weight: 600; }
QLabel#Brand { font-size: 18px; font-weight: 600; }
QLabel#Muted { color: #616161; }
QLabel#Caption { color: #616161; font-size: 12px; }
QLabel#Metric { font-size: 28px; font-weight: 600; }
QLabel#StatusPill { background: #EDEDED; color: #616161; border-radius: 12px; padding: 5px 12px; font-size: 12px; }
QLabel#StatusPill[tone="active"] { background: #E8F3EC; color: #0F6B3B; }
QLabel#StatusPill[tone="error"] { background: #FDE7E9; color: #A4262C; }
QFrame#Surface { background: #FFFFFF; border: 1px solid #E5E5E5; border-radius: 8px; }
QFrame#DetailSurface { background: #FAFAFA; border: 1px solid #EAEAEA; border-radius: 6px; }
QFrame#Rule { background: #E5E5E5; max-height: 1px; border: none; }
QPushButton { background: #FFFFFF; border: 1px solid #D1D1D1; border-bottom-color: #B8B8B8; border-radius: 4px; padding: 7px 14px; min-height: 20px; }
QPushButton:hover { background: #F6F6F6; }
QPushButton:pressed { background: #F0F0F0; color: #616161; border-bottom-color: #D1D1D1; }
QPushButton:focus, QLineEdit:focus, QTreeWidget:focus, QTableWidget:focus, QSpinBox:focus, QComboBox:focus { border: 2px solid #005FB8; }
QPushButton#Primary { background: #005FB8; color: #FFFFFF; border-color: #005FB8; border-bottom-color: #004A91; }
QPushButton#Primary:hover { background: #0055A6; }
QPushButton:disabled, QPushButton#Primary:disabled { color: #8A8A8A; background: #F0F0F0; border-color: #E5E5E5; }
QPushButton#NavItem { background: transparent; border: none; text-align: left; padding: 10px 14px; border-radius: 6px; }
QPushButton#NavItem:hover { background: #EAEAEA; }
QPushButton#NavItem:checked { background: #E5E5E5; font-weight: 600; }
QPushButton#NavItem:focus { border: 2px solid #005FB8; }
QPushButton#Quiet { background: transparent; border-color: transparent; color: #005FB8; }
QPushButton#Quiet:hover { background: #EAEFF4; }
QPushButton#LogToggle { background: transparent; border: none; text-align: left; color: #616161; padding: 6px 0; }
QLineEdit, QSpinBox, QComboBox { background: #FFFFFF; border: 1px solid #D1D1D1; border-bottom-color: #8A8A8A; border-radius: 4px; padding: 7px 10px; selection-background-color: #CFE6FA; selection-color: #1B1B1B; }
QSpinBox { min-width: 80px; }
QTreeWidget, QListWidget { background: #FFFFFF; alternate-background-color: #FAFAFA; border: 1px solid #E5E5E5; border-radius: 6px; padding: 4px; selection-background-color: #E5F1FB; selection-color: #1B1B1B; }
QTableWidget { background: #FFFFFF; border: none; gridline-color: #F1F1F1; selection-background-color: #E5F1FB; selection-color: #1B1B1B; outline: none; }
QTableWidget::item { padding: 6px 10px; border-bottom: 1px solid #F3F3F3; }
QTableWidget::item:hover { background: #F6F6F6; }
QTableWidget::item:selected { background: #E5F1FB; color: #1B1B1B; }
QHeaderView::section { background: #FFFFFF; color: #616161; padding: 10px; border: none; border-bottom: 1px solid #E5E5E5; font-size: 12px; }
QPlainTextEdit { background: #FFFFFF; border: 1px solid #E5E5E5; border-radius: 6px; padding: 8px; font-size: 12px; }
QGroupBox { background: #FFFFFF; border: 1px solid #E5E5E5; border-radius: 8px; margin-top: 24px; padding: 20px 16px 16px; font-weight: 600; }
QGroupBox::title { subcontrol-origin: margin; left: 16px; padding: 0 4px; }
QScrollArea { border: none; background: transparent; }
QRadioButton, QCheckBox { spacing: 10px; padding: 6px 0; }
QTabWidget::pane { border: none; }
QTabBar::tab { background: transparent; padding: 10px 18px; border-bottom: 2px solid transparent; color: #616161; }
QTabBar::tab:selected { color: #005FB8; border-bottom-color: #005FB8; font-weight: 600; }
QTabBar::tab:hover { background: #F0F0F0; }
QToolTip, QMenu { background: #FFFFFF; color: #1B1B1B; border: 1px solid #D1D1D1; }
QMenu::item { padding: 8px 24px; }
QMenu::item:selected { background: #E5F1FB; }
QStatusBar { color: #616161; font-size: 12px; border-top: 1px solid #EFEFEF; }
QScrollBar:vertical { background: transparent; width: 10px; margin: 4px 2px; }
QScrollBar::handle:vertical { background: #C4C4C4; border-radius: 3px; min-height: 28px; }
QScrollBar::handle:vertical:hover { background: #999999; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }
'''
