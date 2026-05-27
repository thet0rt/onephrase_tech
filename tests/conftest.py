import sys
import os

# Add the project root to sys.path so that top-level modules (app, db, models, etc.)
# are importable from within the tests/ directory.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
