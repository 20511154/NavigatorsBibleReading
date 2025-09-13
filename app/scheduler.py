from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from datetime import datetime, time
from zoneinfo import ZoneInfo

from app.db import get_db
from app.models import User, UserEvent
from app.config import settings
from app.logic import (
    get_next_reading, get_user_stats, format_reading_text,
    did_read_today, was_nudged_today, record_nudge,
    get_user_timezone, get_user_local_now, is_time_for_daily_card,
    is_time_for_nudge, was_daily_card_sent_today, mark_daily_card_sent_today,
    mark_nudge_sent_today
)
from app.messages import get_nudge_message

router = APIRouter()


def verify_cron_secret(x_cron_secret: str = Header(None)):
    """Verify cron secret for security"""
    if not x_cron_secret or x_cron_secret != settings.cron_secret:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return True


async def send_daily_card_to_user(user: User, db: Session, bot):
    """Send daily card to a specific user"""
    try:
        # Get current pointer and reading
        from app.logic import get_current_pointer, get_reading_by_pointer
        current_month, current_day = get_current_pointer(db, user)
        reading = get_reading_by_pointer(db, current_month, current_day)
        
        if not reading:
            return False
        
        # Get stats and format message
        stats = get_user_stats(db, user)
        text = format_reading_text(reading, stats)
        
        # Create keyboard
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton("✅ Read", callback_data=f"read|{reading['month']}|{reading['day']}"),
                InlineKeyboardButton("🛌 Break", callback_data=f"break|{reading['month']}|{reading['day']}")
            ],
            [InlineKeyboardButton("📖 Next", callback_data="next")]
        ])
        
        # Send message
        await bot.send_message(
            chat_id=user.telegram_id,
            text=text,
            parse_mode='MarkdownV2',
            reply_markup=keyboard
        )
        
        # Mark as sent today
        mark_daily_card_sent_today(db, user)
        return True
        
    except Exception as e:
        print(f"Error sending daily card to user {user.telegram_id}: {e}")
        return False


async def send_nudge_to_user(user: User, db: Session, bot):
    """Send nudge to a specific user"""
    try:
        await bot.send_message(
            chat_id=user.telegram_id,
            text=get_nudge_message(),
            parse_mode='MarkdownV2'
        )
        
        # Record nudge and mark as sent today
        record_nudge(db, user)
        mark_nudge_sent_today(db, user)
        return True
        
    except Exception as e:
        print(f"Error sending nudge to user {user.telegram_id}: {e}")
        return False


@router.post("/cron/daily")
async def daily_cron(
    db: Session = Depends(get_db),
    _: bool = Depends(verify_cron_secret)
):
    """Daily cron job - send reading cards at 07:00 local time"""
    from app.main import bot
    
    # Get all users
    users = db.query(User).all()
    sent_count = 0
    
    for user in users:
        try:
            # Check if it's time for daily card and not already sent today
            if is_time_for_daily_card(user) and not was_daily_card_sent_today(db, user):
                success = await send_daily_card_to_user(user, db, bot)
                if success:
                    sent_count += 1
                        
        except Exception as e:
            print(f"Error processing user {user.telegram_id} for daily cron: {e}")
            continue
    
    return {"message": f"Daily cron completed. Sent {sent_count} cards."}


@router.post("/cron/nudge")
async def nudge_cron(
    db: Session = Depends(get_db),
    _: bool = Depends(verify_cron_secret)
):
    """Nudge cron job - send nudges at 20:00 local time"""
    from app.main import bot
    
    # Get all users
    users = db.query(User).all()
    nudged_count = 0
    
    for user in users:
        try:
            # Check if it's time for nudge, user hasn't read today, and not already nudged today
            if (is_time_for_nudge(user) and 
                not did_read_today(db, user) and 
                not was_nudged_today(db, user)):
                success = await send_nudge_to_user(user, db, bot)
                if success:
                    nudged_count += 1
                        
        except Exception as e:
            print(f"Error processing user {user.telegram_id} for nudge cron: {e}")
            continue
    
    return {"message": f"Nudge cron completed. Sent {nudged_count} nudges."}


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}