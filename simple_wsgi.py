import sys
import os

# Add your project directory to the Python path
path = '/home/20511154/NavigatorsBibleReading'
if path not in sys.path:
    sys.path.append(path)

# Set environment variables
os.environ['TELEGRAM_TOKEN'] = 'your_telegram_bot_token_here'
os.environ['DATABASE_URL'] = 'sqlite:///./bible_reading.db'
os.environ['WEBHOOK_BASE_URL'] = 'https://20511154.pythonanywhere.com'
os.environ['CRON_SECRET'] = 'your_secret_key_here'

# Import the test app first
from test_app import app

# This is the WSGI application
application = app
