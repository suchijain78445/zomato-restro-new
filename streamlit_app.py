"""
Root entrypoint for Streamlit Community Cloud and Streamlit deployment.
"""

import sys
from pathlib import Path

# Ensure project root is in Python sys.path
root_dir = Path(__file__).resolve().parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

# Import and launch the Streamlit frontend app
import frontend.app  # noqa: F401, E402
