import logging.config
from pathlib import Path
from python_basic_template.utils.file_utils import ensure_dir
from python_basic_template.settings.logging_provider import LoggingConfigProvider


PROJECT_NAME = 'python_basic_template'
DEBUG = True
BASE_DATA_DIR = Path(__file__).parent.parent.parent.parent / 'data'


class DataDirs:
    BASE = ensure_dir(BASE_DATA_DIR)
    RAW = ensure_dir(BASE_DATA_DIR / 'raw')
    INTERIM = ensure_dir(BASE_DATA_DIR / 'interim')
    TS_RAW = ensure_dir(BASE_DATA_DIR / 'timeseries' / 'raw')
    TS_INTERIM = ensure_dir(BASE_DATA_DIR / 'timeseries' / 'interim')



logging_provider = LoggingConfigProvider(
    log_dir=DataDirs.BASE / 'logs',
    debug=DEBUG,
    project_name=PROJECT_NAME,
    use_rich=True,
    max_bytes=5 * 1024 * 1024,
    backups=3,
)
LOGGING = logging_provider.get_logging_config()
logging.config.dictConfig(LOGGING)