from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = PROJECT_ROOT / 'data'
RAW_ROOT = DATA_ROOT / 'raw'
PROCESSED_ROOT = DATA_ROOT / 'processed'
LOG_ROOT = DATA_ROOT / 'logs'

SCHEMA_VERSION = '2.0'
SOURCE_LAYER_B = 'B'
SOURCE_LAYER_A = 'A'

OFFICIAL_SOURCE_DOMAINS = (
    'normattiva.it',
    'www.normattiva.it',
    'gazzettaufficiale.it',
    'www.gazzettaufficiale.it',
    'dati.normattiva.it',
)

DEFAULT_CHUNK_MAX_CHARS = 1200
