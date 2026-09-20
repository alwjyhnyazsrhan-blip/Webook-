# apps/__init__.py
"""
Webook Project Apps Package
Configured for absolute resolution across all environments including Google Colab.
"""
import os
import sys
from pathlib import Path

# Resolve project root (parent directory of apps)
_ROOT_DIR = str(Path(__file__).resolve().parent.parent)

if _ROOT_DIR not in sys.path:
    sys.path.insert(0, _ROOT_DIR)

# Propagate to PYTHONPATH environment variable
_current_pp = os.environ.get("PYTHONPATH", "")
if _ROOT_DIR not in _current_pp.split(os.pathsep):
    os.environ["PYTHONPATH"] = f"{_ROOT_DIR}{os.pathsep}{_current_pp}" if _current_pp else _ROOT_DIR
