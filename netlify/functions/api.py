import sys
import os
from mangum import Mangum

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from backend.app import app  # Import your main FastAPI app

# Create a handler for the FastAPI app
handler = Mangum(app)