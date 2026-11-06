"""Fluent-inspired native workspace backed by the persisted operation journal."""
from datetime import date, datetime
from pathlib import Path

from PySide6.QtCore import QSize, Qt, QTimer, QUrl, Slot
from PySide6.QtGui import QAction, QDesktopServices, QIcon, QKeySequence
from PySide6.QtWidgets import (
    QAbstractItemView, QApplication, QComboBox, QFrame, QHeaderView, QHBoxLayout,
    QLabel, QLineEdit, QMainWindow, QMenu, QPlainTextEdit, QPushButton,
    QStackedWidget, QSystemTrayIcon, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from . import __version__
from .config_manager import load_config
from .settings_page import SettingsPage
from .signals import signals
from .theme import STYLESHEET, ElidedLabel, NavigationButton, StateDelegate, apply_theme, fluent_icon
from .utils import data_root, get_absolute_path


def label(text, role=None):
    widget = QLabel(text)
    widget.setTextFormat(Qt.TextFormat.PlainText)
    if role:
        widget.setObjectName(role)
    return widget


def surface(name='Surface'):
    widget = QFrame()
    widget.setObjectName(name)
    return widget


class TidyCoreGUI(QMainWindow):
    def __init__(self, engine, app: QApplication):
        super().__init__()
        self.engine, self.app, self.db = engine, app, engine.db
        apply_theme(app)
        self._stats_date = date.today()
        self.operations, self.displayed_operations = [], []
        self.setWindowTitle(f'TidyCore {__version__}')
        self.setWindowIcon(QIcon(get_absolute_path('assets/tidycore.svg')))
        self.resize(1160, 800)
        self.setMinimumSize(860, 600)
        self.setStyleSheet(STYLESHEET)
        root = QWidget()
        root.setObjectName('Workspace')
        self.setCentralWidget(root)
        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        navigation = QWidget()
        navigation.setObjectName('Navigation')
        navigation.setFixedWidth(220)
        nav = QVBoxLayout(navigation)
        nav.setContentsMargins(14, 28, 14, 18)
        nav.setSpacing(6)
        brand = QHBoxLayout()
        mark = label('')
        mark.setPixmap(self.windowIcon().pixmap(36, 36))
        brand.addWidget(mark)
        brand_text = QVBoxLayout()
        brand_text.setSpacing(2)
        brand_text.addWidget(label('TidyCore', 'Brand'))
        brand_text.addWidget(label('File organization, simplified', 'Caption'))
        brand.addLayout(brand_text)
        brand.addStretch()
        nav.addLayout(brand)
        nav.addSpacing(28)
        nav.addWidget(label('WORKSPACE', 'Caption'))
        nav.addSpacing(4)
        self.stacked_widget = QStackedWidget()
        self.dashboard_button = NavigationButton('&Activity')
        self.settings_button = NavigationButton('&Settings')
        self.about_button = NavigationButton('A&bout')
        for index, button in enumerate((self.dashboard_button, self.settings_button, self.about_button)):
            button.setObjectName('NavItem')
            button.setCheckable(True)
            button.setIconSize(QSize(20, 20))
            button.clicked.connect(lambda checked=False, i=index: self.select_page(i))
            nav.addWidget(button)
        nav.addStretch()
        self.nav_status = label('●  Paused', 'Caption')
        self.nav_status.setContentsMargins(14, 0, 0, 0)
        nav.addWidget(self.nav_status)
        nav.addSpacing(8)
        self.exit_button = QPushButton('E&xit TidyCore')
        self.exit_button.setObjectName('NavItem')
        self.exit_button.setIcon(fluent_icon('exit'))
        self.exit_button.clicked.connect(self._exit_application)
        nav.addWidget(self.exit_button)
        version = label(f'Version {__version__}', 'Caption')
        version.setContentsMargins(14, 4, 0, 0)
        nav.addWidget(version)
        layout.addWidget(navigation)
        layout.addWidget(self.stacked_widget, 1)
        self.stacked_widget.addWidget(self._activity_page())
        self.settings_page = SettingsPage()
        self.stacked_widget.addWidget(self.settings_page)
        self.stacked_widget.addWidget(self._about_page())
        self.select_page(0)
        self._create_tray_icon()
        signals.log_message.connect(self.add_log_message, Qt.ConnectionType.QueuedConnection)
        signals.status_changed.connect(self.update_status, Qt.ConnectionType.QueuedConnection)
        signals.activity_changed.connect(self.schedule_refresh, Qt.ConnectionType.QueuedConnection)
        signals.config_changed.connect(self.handle_config_change)
        signals.command_completed.connect(self.command_completed, Qt.ConnectionType.QueuedConnection)
        self.refresh_timer = QTimer(self)
        self.refresh_timer.setSingleShot(True)
        self.refresh_timer.setInterval(150)
        self.refresh_timer.timeout.connect(self.refresh_history)
        self.status_timer = QTimer(self)
        self.status_timer.setInterval(1000)
        self.status_timer.timeout.connect(self.refresh_status)
        self.status_timer.start()
        self.refresh_history()
        self.refresh_status()
        self.statusBar().showMessage('Close to keep watching in the tray. Exit to stop TidyCore.')
        for title, shortcut, callback in (
            ('Undo selected move', 'Ctrl+Z', self.undo_selected),
            ('Pause or resume', 'Ctrl+P', self.toggle_pause_resume),
            ('Search history', 'Ctrl+F', self.focus_search),
        ):
            action = QAction(title, self)
            action.setShortcut(QKeySequence(shortcut))
            action.triggered.connect(callback)
            self.addAction(action)

    def select_page(self, index):
        self.stacked_widget.setCurrentIndex(index)
        for i, (button, icon) in enumerate(((self.dashboard_button,'activity'),(self.settings_button,'settings'),(self.about_button,'about'))):
            button.setChecked(i == index)
            button.setIcon(fluent_icon(icon, '#005FB8' if i == index else '#616161'))

    def _activity_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(28, 26, 28, 16)
        layout.setSpacing(18)
        heading = QHBoxLayout()
        title = QVBoxLayout()
        title.setSpacing(4)
        title.addWidget(label('Activity', 'Title'))
        title.addWidget(label('A little order. A lot less clutter.', 'Muted'))
        heading.addLayout(title)
        heading.addStretch()
        self.status_label = label('Starting', 'StatusPill')
        self.pause_resume_button = QPushButton('Start watching')
        self.pause_resume_button.setObjectName('Primary')
        self.pause_resume_button.setToolTip('Start or pause organization (Ctrl+P)')
        self.pause_resume_button.clicked.connect(self.toggle_pause_resume)
        heading.addWidget(self.status_label,alignment=Qt.AlignmentFlag.AlignVCenter)
        heading.addSpacing(6)
        heading.addWidget(self.pause_resume_button,alignment=Qt.AlignmentFlag.AlignVCenter)
        layout.addLayout(heading)

        watch = surface()
        watch_layout = QHBoxLayout(watch)
        watch_layout.setContentsMargins(18, 15, 14, 15)
        watch_layout.setSpacing(14)
        folder = label('')
        folder.setPixmap(fluent_icon('folder','#005FB8').pixmap(28,28))
        watch_layout.addWidget(folder)
        path_layout = QVBoxLayout()
        path_layout.setSpacing(4)
        path_layout.addWidget(label('Watched folder', 'Caption'))
        self.path_label = ElidedLabel('No folder selected')
        self.path_label.setAccessibleName('Watched folder path')
        path_layout.addWidget(self.path_label)
        watch_layout.addLayout(path_layout, 1)
        change = QPushButton('Change folder')
        change.setObjectName('Quiet')
        change.clicked.connect(lambda: self.select_page(1))
        watch_layout.addWidget(change)
        layout.addWidget(watch)

        metrics = QHBoxLayout()
        metrics.setContentsMargins(2, 0, 2, 0)
        metrics.setSpacing(36)
        self.today_value, self.total_value, self.category_value = (label('0','Metric') for _ in range(3))
        for value, caption in ((self.today_value,'Organized today'),(self.total_value,'Net moves recorded'),(self.category_value,'Categories today')):
            column = QVBoxLayout()
            column.setSpacing(1)
            column.addWidget(value)
            column.addWidget(label(caption,'Caption'))
            metrics.addLayout(column)
        metrics.addStretch()
        self.stats_label = label('History is saved on this device', 'Caption')
        metrics.addWidget(self.stats_label, alignment=Qt.AlignmentFlag.AlignBottom)
        self.metrics_container = QWidget()
        self.metrics_container.setLayout(metrics)
        layout.addWidget(self.metrics_container)

        history = surface()
        history_layout = QVBoxLayout(history)
        history_layout.setContentsMargins(16, 16, 16, 12)
        history_layout.setSpacing(10)
        history_heading = QHBoxLayout()
        history_heading.addWidget(label('Organization history','Heading'))
        history_heading.addStretch()
        self.history_count = label('Latest 200 operations','Caption')
        history_heading.addWidget(self.history_count)
        history_layout.addLayout(history_heading)
        toolbar = QHBoxLayout()
        self.history_search = QLineEdit()
        self.history_search.setPlaceholderText('Search files, categories or paths')
        self.history_search.setAccessibleName('Search organization history')
        self.history_search.setClearButtonEnabled(True)
        self.history_search.addAction(fluent_icon('search'), QLineEdit.ActionPosition.LeadingPosition)
        self.history_search.textChanged.connect(self.render_history)
        self.history_filter = QComboBox()
        self.history_filter.setAccessibleName('Filter history by state')
        self.history_filter.addItems(['All activity','Organized','Undone','Needs attention'])
        self.history_filter.currentIndexChanged.connect(self.render_history)
        reload_button = QPushButton()
        reload_button.setIcon(fluent_icon('refresh'))
        reload_button.setToolTip('Refresh history')
        reload_button.setAccessibleName('Refresh history')
        reload_button.clicked.connect(self.refresh_history)
        toolbar.addWidget(self.history_search, 1)
        toolbar.addWidget(self.history_filter)
        toolbar.addWidget(reload_button)
        history_layout.addLayout(toolbar)
        self.empty_label = label('Choose a folder in Settings to get started.','Muted')
        self.empty_label.setWordWrap(True)
        self.empty_label.setContentsMargins(12, 16, 12, 16)
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        history_layout.addWidget(self.empty_label,1)
        self.history_table = QTableWidget(0, 4)
        self.history_table.setAccessibleName('Persisted organization history')
        self.history_table.setHorizontalHeaderLabels(['Name','Category','When','State'])
        self.history_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.history_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.history_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.history_table.setShowGrid(False)
        self.history_table.setMinimumHeight(128)
        self.history_table.setIconSize(QSize(20,20))
        self.history_table.setItemDelegateForColumn(3,StateDelegate(self.history_table))
        self.history_table.verticalHeader().hide()
        self.history_table.verticalHeader().setDefaultSectionSize(44)
        self.history_table.horizontalHeader().setSectionResizeMode(0,QHeaderView.ResizeMode.Stretch)
        for col, width in ((1,150),(2,135),(3,115)):
            self.history_table.horizontalHeader().setSectionResizeMode(col,QHeaderView.ResizeMode.Interactive)
            self.history_table.setColumnWidth(col,width)
        self.history_table.itemSelectionChanged.connect(self.show_selection)
        history_layout.addWidget(self.history_table, 1)
        self.detail_surface = surface('DetailSurface')
        detail = QHBoxLayout(self.detail_surface)
        detail.setContentsMargins(12,10,12,10)
        detail_paths = QVBoxLayout()
        detail_paths.setSpacing(3)
        self.details_label = ElidedLabel('')
        self.details_label.setObjectName('Caption')
        self.destination_label = ElidedLabel('')
        self.destination_label.setObjectName('Caption')
        detail_paths.addWidget(self.details_label)
        detail_paths.addWidget(self.destination_label)
        detail.addLayout(detail_paths,1)
        self.undo_button = QPushButton('&Undo move')
        self.undo_button.setIcon(fluent_icon('undo'))
        self.undo_button.setToolTip('Restore unchanged contents without overwriting (Ctrl+Z)')
        self.undo_button.clicked.connect(self.undo_selected)
        detail.addWidget(self.undo_button,alignment=Qt.AlignmentFlag.AlignVCenter)
        history_layout.addWidget(self.detail_surface)
        layout.addWidget(history,1)

        log_header = QHBoxLayout()
        self.log_toggle = QPushButton('Activity log')
        self.log_toggle.setObjectName('LogToggle')
        self.log_toggle.setIcon(fluent_icon('chevron'))
        self.log_toggle.setCheckable(True)
        self.log_toggle.toggled.connect(self.toggle_log)
        log_header.addWidget(self.log_toggle)
        self.last_message = ElidedLabel('No events in this session')
        self.last_message.setObjectName('Caption')
        log_header.addWidget(self.last_message,1)
        layout.addLayout(log_header)
        self.activity_feed = QPlainTextEdit()
        self.activity_feed.setAccessibleName('Session activity log')
        self.activity_feed.setReadOnly(True)
        self.activity_feed.setMaximumBlockCount(500)
        self.activity_feed.setMaximumHeight(130)
        self.activity_feed.setPlaceholderText('Moves, settings and errors appear here.')
        self.activity_feed.hide()
        layout.addWidget(self.activity_feed)
        return page

    def _about_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(28,26,28,24)
        layout.setSpacing(20)
        layout.addWidget(label('About','Title'))
        brand = QHBoxLayout()
        mark = label('')
        mark.setPixmap(self.windowIcon().pixmap(64,64))
        brand.addWidget(mark)
        text = QVBoxLayout()
        text.addWidget(label('TidyCore','Title'))
        text.addWidget(label(f'Version {__version__} · Windows desktop','Muted'))
        brand.addLayout(text)
        brand.addStretch()
        layout.addLayout(brand)
        description = label('A place for every file.\n\nTidyCore keeps the folders you choose organized with clear rules,\npersistent history and moves you can safely undo.','Muted')
        description.setWordWrap(True)
        layout.addWidget(description)
        info = surface()
        info_layout = QVBoxLayout(info)
        info_layout.setContentsMargins(20,16,20,16)
        info_layout.setSpacing(14)
        for title, body in [('Made by','Le Nguyen Gia Hung (hei)'),('Your data stays on this device',str(data_root())),('Updates','Manual downloads from the official GitHub releases page.')]:
            info_layout.addWidget(label(title,'Caption'))
            row = label(body)
            row.setWordWrap(True)
            row.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            info_layout.addWidget(row)
        layout.addWidget(info)
        releases = QPushButton('View releases on GitHub')
        releases.setIcon(fluent_icon('external'))
        releases.clicked.connect(lambda: QDesktopServices.openUrl(QUrl('https://github.com/hei1sme/tidycore/releases')))
        layout.addWidget(releases,alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addStretch()
        return page

    def focus_search(self):
        self.select_page(0)
        self.history_search.setFocus()
        self.history_search.selectAll()

    def toggle_log(self, expanded):
        self.activity_feed.setVisible(expanded)
        self.log_toggle.setText('Hide activity log' if expanded else 'Activity log')

    @Slot()
    def schedule_refresh(self):
        if not self.refresh_timer.isActive():
            self.refresh_timer.start()

    @Slot()
    def refresh_history(self):
        self._stats_date = date.today()
        try:
            self.operations, today, total, categories = self.db.dashboard_snapshot(200)
            self.today_value.setText(str(today))
            self.total_value.setText(str(total))
            self.category_value.setText(str(len(categories)))
            self.stats_label.setText('History saved on this device')
            tooltip = 'Completed journal operations minus undo; not a live disk inventory.\nToday: ' + (', '.join(f'{key}: {value}' for key,value in categories.items()) or 'no moves')
            for widget in (self.today_value,self.total_value,self.category_value,self.stats_label):
                widget.setToolTip(tooltip)
            self.render_history()
        except Exception as exc:
            self.stats_label.setText('History unavailable')
            self.add_log_message(f'[ERROR] Could not read history: {exc}')

    def render_history(self, *_):
        if not hasattr(self,'history_table'):
            return
        selected = self.selected_operation()
        selected_id = selected['id'] if selected else None
        query = self.history_search.text().strip().casefold()
        state = self.history_filter.currentIndex()
        self.displayed_operations = [row for row in self.operations
            if (not query or query in ' '.join(str(row.get(key) or '') for key in ('filename','category','subcategory','source_path','destination_path')).casefold())
            and (state == 0 or state == 1 and row['status']=='completed' or state == 2 and row['status']=='undone'
                 or state == 3 and row['status'] in {'review','failed','pending','undo_pending'})]
        self.history_table.blockSignals(True)
        self.history_table.clearSelection()
        self.history_table.setCurrentCell(-1,-1)
        self.history_table.setRowCount(len(self.displayed_operations))
        for index,row in enumerate(self.displayed_operations):
            when = row['timestamp'].replace('T',' ')[:16]
            if row['operation_date'] == date.today().isoformat():
                when = 'Today, ' + row['timestamp'].replace('T',' ')[11:16]
            values = (row['filename'],row['category']+(f" / {row['subcategory']}" if row['subcategory'] else ''),when,row['status'].replace('_',' ').capitalize())
            for col,value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setToolTip(row['error'] or (row['timestamp'] if col==2 else value))
                if col==0:
                    image = Path(row['filename']).suffix.lower() in {'.png','.jpg','.jpeg','.webp','.gif'}
                    item.setIcon(fluent_icon('image' if image else 'document','#0F6B3B' if image else '#005FB8'))
                self.history_table.setItem(index,col,item)
            if row['id']==selected_id:
                self.history_table.selectRow(index)
        self.history_table.blockSignals(False)
        count=len(self.displayed_operations)
        self.history_count.setText(f'{count} of {len(self.operations)} records' if query or state else f'{len(self.operations)} recent records')
        self.empty_label.setVisible(not count)
        self.history_table.setVisible(bool(count))
        if not count:
            self.empty_label.setText('No matching activity. Try another search or filter.' if self.operations else
                'Nothing organized yet. Choose a folder, review your rules, and start watching.')
        self.show_selection()

    def selected_operation(self):
        index=self.history_table.currentRow()
        return self.displayed_operations[index] if 0 <= index < len(self.displayed_operations) else None

    def show_selection(self):
        row=self.selected_operation()
        self.undo_button.setEnabled(bool(row and row['status']=='completed' and row['fingerprint']))
        self.detail_surface.setVisible(bool(row))
        if row:
            self.details_label.setText(f"From  {row['source_path']}")
            self.destination_label.setText(f"To      {row['destination_path']}")
            self.detail_surface.setToolTip(row['error'] or 'Full paths are available by hovering each line.')

    def resizeEvent(self,event):
        super().resizeEvent(event)
        if hasattr(self,'metrics_container'):
            self.metrics_container.setVisible(self.height()>=730)
        if hasattr(self,'activity_feed'):
            self.activity_feed.setMaximumHeight(90 if self.height()<730 else 130)

    def undo_selected(self):
        row=self.selected_operation()
        if row and self.undo_button.isEnabled():
            self.undo_button.setEnabled(False)
            self.engine.request_undo(row['id'])

    @Slot(bool,str)
    def command_completed(self,ok,message):
        self.statusBar().showMessage(message,12000)
        self.refresh_history()

    @Slot(str)
    def add_log_message(self,message):
        self.activity_feed.appendPlainText(f'{datetime.now():%H:%M:%S}  {message}')
        self.last_message.setText(message)
        if '[ERROR]' in message:
            self.log_toggle.setChecked(True)

    @Slot(bool)
    def update_status(self,running):
        self.refresh_status()

    def refresh_status(self):
        if self._stats_date!=date.today():
            self.schedule_refresh()
        health=self.engine.get_health_status()
        running=health['is_running']
        text = 'Restart required' if health['error'] else 'Not configured' if not self.engine.target_folder else 'Starting' if running and not health['observer_alive'] else 'Watching' if running else 'Paused'
        self.status_label.setText('●  '+text)
        self.status_label.setProperty('tone','error' if health['error'] else 'active' if running else 'neutral')
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)
        self.nav_status.setText('●  '+text)
        self.path_label.setText(str(self.engine.target_folder) if self.engine.target_folder else 'Choose a folder to get started')
        self.pause_resume_button.setText('Pause watching' if running else 'Start watching')
        self.pause_resume_button.setIcon(fluent_icon('pause' if running else 'play','#FFFFFF' if self.engine.target_folder and not health['error'] else '#8A8A8A'))
        self.pause_resume_button.setEnabled(bool(self.engine.target_folder) and not health['error'])
        if hasattr(self,'tray_pause_action'):
            self.tray_pause_action.setText('Pause watching' if running else 'Start watching')
            self.tray_pause_action.setEnabled(self.pause_resume_button.isEnabled())
            self.tray_icon.setToolTip(f'TidyCore — {text}')

    def toggle_pause_resume(self):
        self.engine.pause() if self.engine.is_running else self.engine.resume()
        self.refresh_status()

    @Slot()
    def handle_config_change(self):
        try:
            self.engine.reload_config(load_config())
        except Exception as exc:
            self.add_log_message(f'[ERROR] Settings could not be applied: {exc}')

    def _create_tray_icon(self):
        self.tray_icon = QSystemTrayIcon(self.windowIcon(), self)
        self.tray_menu = QMenu(self)
        show = self.tray_menu.addAction('Show TidyCore')
        show.triggered.connect(self.show_window)
        self.tray_pause_action = self.tray_menu.addAction('Start watching')
        self.tray_pause_action.triggered.connect(self.toggle_pause_resume)
        self.tray_menu.addSeparator()
        self.tray_menu.addAction('Exit TidyCore').triggered.connect(self._exit_application)
        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.activated.connect(self._tray_activated)
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon.show()

    def _tray_activated(self, reason):
        if reason in (QSystemTrayIcon.ActivationReason.Trigger, QSystemTrayIcon.ActivationReason.DoubleClick):
            self.show_window()

    def show_window(self):
        self.showNormal()
        self.activateWindow()
        self.raise_()

    def closeEvent(self, event):
        if self.tray_icon.isVisible() and not getattr(self, '_force_exit', False):
            event.ignore()
            self.hide()
        else:
            event.accept()
            self._exit_application()

    def _exit_application(self):
        self._force_exit = True
        self.engine.stop()
        self.tray_icon.hide()
        self.app.quit()
