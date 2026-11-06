"""Native Windows entry point. Configure isolation before importing app modules."""
import argparse
import os
from pathlib import Path
import sys


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description='TidyCore file organizer')
    parser.add_argument('--data-dir', type=Path, help='Explicit directory for settings, history and logs')
    parser.add_argument('--test-mode', action='store_true', help='Disable startup integration; restrict watch folder to data directory')
    args = parser.parse_args(argv)
    if args.data_dir:
        os.environ['TIDYCORE_DATA_DIR'] = str(args.data_dir.resolve())
    if args.test_mode:
        if not args.data_dir:
            parser.error('--test-mode requires --data-dir')
        os.environ['TIDYCORE_TEST_MODE'] = '1'

    from PySide6.QtCore import QLockFile
    from PySide6.QtWidgets import QApplication, QMessageBox
    from src.tidycore.config_manager import load_config
    from src.tidycore.database import StatisticsDatabase
    from src.tidycore.engine import TidyCoreEngine
    from src.tidycore.gui import TidyCoreGUI
    from src.tidycore.logger import setup_logger
    from src.tidycore.instance import InstanceServer, server_name, show_existing
    from src.tidycore.utils import data_root

    app = QApplication([sys.argv[0]])
    app.setApplicationName('TidyCore')
    app.setOrganizationName('TidyCore')
    app.setStyle('Fusion')
    app.setPalette(app.style().standardPalette())
    app.setQuitOnLastWindowClosed(False)
    logger = setup_logger()
    lock = QLockFile(str(data_root() / 'tidycore.lock'))
    lock.setStaleLockTime(0)
    if not lock.tryLock(100):
        if show_existing(server_name(data_root())):
            return 0
        QMessageBox.information(None, 'TidyCore is already running',
                                'An instance already uses this data directory. Open it from the system tray.')
        return 1
    engine = None
    try:
        config = load_config()
        if args.test_mode and config['target_folder']:
            Path(config['target_folder']).resolve().relative_to(data_root())
        database = StatisticsDatabase()
        engine = TidyCoreEngine(config, database)
        window = TidyCoreGUI(engine, app)
        instance_server = InstanceServer(server_name(data_root()), window)
        app.aboutToQuit.connect(engine.stop)
        window.show()
        engine.start()
        return app.exec()
    except Exception as exc:
        logger.exception('Application failed')
        QMessageBox.critical(None, 'TidyCore could not start',
            f'{exc}\n\nData was retained at:\n{data_root()}\n\nCheck tidycore.log. No replacement settings or history were created over unreadable data.')
        return 2
    finally:
        if engine:
            engine.stop()
            engine.join()
        lock.unlock()


if __name__ == '__main__':
    sys.exit(main())
