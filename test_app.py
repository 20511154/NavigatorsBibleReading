from fastapi import FastAPI

# Create a simple FastAPI app for testing
app = FastAPI(title="Bible Reading Tracker Bot - Test", version="1.0.0")

@app.get("/")
async def root():
    """Root endpoint for testing"""
    return {"message": "Bible Reading Tracker Bot is running!", "status": "success"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "bible-reading-bot"}

# This is the WSGI application
application = app
