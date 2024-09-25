import sys
import os

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

from mangum import Mangum
from backend.app import app  # Import your main FastAPI app

handler = Mangum(app)

def lambda_handler(event, context):
    return handler(event, context)