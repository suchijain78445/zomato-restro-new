import sys
from pathlib import Path
import importlib.util

# Ensure project root is in Python sys.path
root_dir = Path(__file__).resolve().parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

# Direct run frontend/app.py without import conflicts
spec = importlib.util.spec_from_file_location("frontend_app", str(root_dir / "frontend" / "app.py"))
frontend_app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(frontend_app)
