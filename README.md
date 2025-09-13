# Bible Reading Tracker Bot

A FastAPI + aiogram Telegram bot that helps users track their daily Bible reading progress with streak tracking and break management.

## Features

- **Daily Reading Cards**: Automated daily reading prompts with current streak and break count
- **Progress Tracking**: Plan-based progress (not calendar-based) with 12 months × 25 days each
- **Streak Management**: Tracks consecutive days of completed readings
- **Break System**: Allows up to 5 breaks per 30-day rolling window
- **Timezone Support**: Users can set their own timezone
- **Scheduled Notifications**: Daily cards at 07:00 and nudges at 20:00 local time
- **Idempotency**: Prevents duplicate processing of callback queries

## Commands

- `/start` - Register and get your first reading
- `/help` - Show help message and break rules
- `/settz <timezone>` - Set your timezone (e.g., `/settz America/New_York`)
- `/today` - Resend today's reading card
- `/next` - Get the next pending reading
- `/stats` - Show your reading statistics

## Database Schema

The bot uses the following Supabase Postgres tables:

- `users` - User information and current progress
- `plan` - 12-month reading plan (300 total readings)
- `user_progress` - Completed readings
- `user_events` - All user actions (read, break, nudge)
- `processed_callbacks` - Callback query deduplication

## Setup

1. **Clone and install dependencies:**
   ```bash
   git clone <repository>
   cd bible-reading-tracker
   pip install -r requirements.txt
   ```

2. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your actual values
   ```

3. **Set up Supabase database:**
   - Create a new Supabase project
   - Run the SQL schema (see `database/schema.sql`)
   - Get your DATABASE_URL

4. **Seed the plan table:**
   ```bash
   python scripts/seed_plan.py scripts/example_plan.csv
   ```

5. **Run the bot:**
   ```bash
   python -m app.main
   ```

## CSV Format

The plan CSV should have these columns:
- Month, Day
- NT1_Book, NT1_Chapter
- NT2_Book, NT2_Chapter
- OT1_Book, OT1_Chapter
- OT2_Book, OT2_Chapter

## API Endpoints

- `POST /webhook` - Telegram webhook endpoint
- `POST /api/cron/daily` - Daily reading card cron
- `POST /api/cron/nudge` - Evening nudge cron
- `GET /api/health` - Health check

## Development

```bash
# Run in development mode
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
pytest

# Format code
black app/
isort app/
```

## License

MIT License