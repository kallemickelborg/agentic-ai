from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes.tasks import router
from config import setup_cors

# Create FastAPI app
app = FastAPI()

# Setup CORS
setup_cors(app)

# Include routers
app.include_router(router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
