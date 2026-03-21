import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "real_local_bridge: richiede il bridge locale reale gia' stabilizzato e viene eseguito solo su ambiente configurato.",
    )
