from fastapi import FastAPI
from .pubsub.a2a_client import get_a2a_integration
from fastapi.middleware.cors import CORSMiddleware
import logging
from .pubsub.broker import broker

from .routes import  channels, messages, agents
from .db.database import engine, Base

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AutonomousSphere API",
    description="API for the AutonomousSphere chat platform with A2A agent integration",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
# app.include_router(auth.router)
# app.include_router(users.router)
app.include_router(channels.router)
app.include_router(messages.router)
app.include_router(agents.router)


@app.on_event("startup")
async def startup_event():
    # Initialize and start the A2A integration
    a2a_integration = get_a2a_integration()
    await a2a_integration.start()
    await broker.start_redis_listener()

@app.get("/")
def read_root():
    return {"message": "Welcome to AutonomousSphere API"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}