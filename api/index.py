import sys
import os

# Add techpulse directory to path so absolute imports work
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'techpulse'))

from backend.main import app
