# src/main.py
import yaml
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, Header
from loguru import logger
import uvicorn
from typing import Optional
from datetime import datetime, timezone

# Import necessary components from other modules
from .database import init_db
from .evolution_api import handle_evolution_webhook, WEBHOOK_VERIFY_TOKEN, close_http_client


# Load configuration (simple approach for now)
try:
    with open("config/config.yaml", "r") as f:
        config = yaml.safe_load(f)
except FileNotFoundError:
    logger.error("Configuration file config/config.yaml not found.")
    config = {}
except yaml.YAMLError as e:
    logger.error(f"Error parsing configuration file: {e}")
    config = {}

# Configure logger
log_level = config.get("logging", {}).get("level", "INFO")
logger.add("logs/app.log", rotation="10 MB", level=log_level)

# Track startup time for health check
_startup_time: datetime | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manages application startup and shutdown lifecycle."""
    global _startup_time
    logger.info("Starting Farmácia AI Agent API...")
    await init_db()
    _startup_time = datetime.now(timezone.utc)
    logger.info("API Started and Database Initialized (Tables created if needed).")
    yield
    # Shutdown
    logger.info("Shutting down Farmácia AI Agent API...")
    await close_http_client()
    logger.info("Shutdown complete.")


app = FastAPI(
    title="Farmácia AI Agent",
    version="0.2.0",
    lifespan=lifespan,
)


@app.get("/")
async def read_root():
    return {"message": f"Welcome to the {config.get('agent', {}).get('pharmacy_name', 'Farmácia')} AI Agent API"}


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring and container orchestration."""
    return {
        "status": "healthy",
        "version": "0.2.0",
        "uptime_since": _startup_time.isoformat() if _startup_time else None,
    }


# Evolution API Webhook Endpoint
@app.post("/webhook/evolution")
async def evolution_webhook(request: Request, x_webhook_verify_token: Optional[str] = Header(None)):
    logger.info("Received request on /webhook/evolution")

    # 1. Verify Webhook Token (if configured)
    if WEBHOOK_VERIFY_TOKEN and x_webhook_verify_token != WEBHOOK_VERIFY_TOKEN:
        logger.warning(f"Invalid webhook verify token received: {x_webhook_verify_token}")
        raise HTTPException(status_code=403, detail="Invalid webhook verify token")
    elif WEBHOOK_VERIFY_TOKEN:
        logger.debug("Webhook verify token validated successfully.")

    # 2. Parse request body
    try:
        body = await request.json()
        logger.debug(f"Webhook payload: {body}")
    except Exception as e:
        logger.error(f"Error parsing request body: {e}")
        raise HTTPException(status_code=400, detail="Invalid request body")

    # 3. Call handler function (run in background to avoid blocking webhook response)
    # For simplicity now, call directly. Consider background tasks for long processing.
    try:
        await handle_evolution_webhook(body)
    except Exception as e:
        logger.error(f"Error handling webhook payload: {e}")
        # Still return 200 to Evolution API to acknowledge receipt, but log the error
        return {"status": "error processing"}

    # 4. Return success status to Evolution API
    return {"status": "received"}

# Placeholder for running with uvicorn if script is executed directly
# (Not typically used when running via Docker)
# if __name__ == "__main__":
#     server_config = config.get("server", {})
#     uvicorn.run(
#         "src.main:app", # Ensure the path is correct if running this way
#         host=server_config.get("host", "127.0.0.1"), # Default to localhost for direct run
#         port=server_config.get("port", 8000),
#         reload=True # Enable reload for local development
#     )
