from fastapi import FastAPI, Request, Depends
from aiogram import Bot, Dispatcher, types
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
import asyncio
import logging

from app.config import settings
from app.db import get_db, engine, Base
from app.handlers import register_handlers
from app.scheduler import router as scheduler_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="Bible Reading Tracker Bot", version="1.0.0")

# Create bot and dispatcher
bot = Bot(token=settings.telegram_token)
dp = Dispatcher()

# Register handlers
register_handlers(dp)

# Include scheduler routes
app.include_router(scheduler_router, prefix="/api")


@app.on_event("startup")
async def on_startup():
    """Initialize database and set webhook on startup"""
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Set webhook
    webhook_url = f"{settings.webhook_base_url}/webhook"
    await bot.set_webhook(webhook_url)
    logger.info(f"Webhook set to: {webhook_url}")


@app.on_event("shutdown")
async def on_shutdown():
    """Cleanup on shutdown"""
    await bot.delete_webhook()
    await bot.session.close()


@app.post("/webhook")
async def webhook_handler(request: Request):
    """Handle incoming webhook requests"""
    try:
        # Get update from request
        update_data = await request.json()
        update = types.Update(**update_data)
        
        # Process update
        await dp.process_update(update)
        
        return {"ok": True}
        
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return {"ok": False, "error": str(e)}


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Bible Reading Tracker Bot is running!"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)