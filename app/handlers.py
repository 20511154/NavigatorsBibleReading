from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.exceptions import TelegramAPIError
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models import User, ProcessedCallback
from app.logic import (
    get_next_reading, get_user_stats, record_reading, record_break,
    can_take_break, did_read_today, was_nudged_today, get_reading_streak,
    get_user_local_date, upsert_user, ensure_user_progress, get_current_pointer,
    get_reading_by_pointer, get_next_pointer
)
from app.messages import (
    get_help_message, get_stats_message, get_break_rejected_message,
    get_break_recorded_message, get_reading_recorded_message,
    get_no_readings_message, get_streak_celebration_message,
    format_reading_text
)
from app.config import settings


async def start_command(message: types.Message, db: Session):
    """Handle /start command"""
    user_id = message.from_user.id
    
    # Upsert user
    user = upsert_user(
        db, user_id, 
        message.from_user.username,
        message.from_user.first_name,
        message.from_user.last_name
    )
    
    # Ensure user has progress record
    ensure_user_progress(db, user)
    
    # Get current pointer and reading
    current_month, current_day = get_current_pointer(db, user)
    reading = get_reading_by_pointer(db, current_month, current_day)
    
    if not reading:
        await message.answer("Welcome! No readings available at the moment.")
        return
    
    # Get stats and format message
    stats = get_user_stats(db, user)
    text = format_reading_text(reading, stats)
    
    # Create keyboard
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton("✅ Read", callback_data=f"read|{reading['month']}|{reading['day']}"),
            InlineKeyboardButton("🛌 Break", callback_data=f"break|{reading['month']}|{reading['day']}")
        ],
        [InlineKeyboardButton("📖 Next", callback_data="next")]
    ])
    
    await message.answer(text, parse_mode='MarkdownV2', reply_markup=keyboard)


async def help_command(message: types.Message):
    """Handle /help command"""
    await message.answer(get_help_message(), parse_mode='MarkdownV2')


async def settz_command(message: types.Message, db: Session):
    """Handle /settz command"""
    try:
        # Extract timezone from command
        timezone = message.text.split(' ', 1)[1].strip()
        
        # Validate timezone (basic check)
        from zoneinfo import ZoneInfo
        ZoneInfo(timezone)  # This will raise if invalid
        
        # Update user timezone
        user = db.query(User).filter(User.telegram_id == message.from_user.id).first()
        if user:
            user.timezone = timezone
            db.commit()
            await message.answer(f"✅ Timezone updated to {timezone}")
        else:
            await message.answer("❌ User not found. Please use /start first.")
            
    except IndexError:
        await message.answer("❌ Please provide a timezone. Example: /settz America/New_York")
    except Exception as e:
        await message.answer(f"❌ Invalid timezone. Error: {str(e)}")


async def today_command(message: types.Message, db: Session):
    """Handle /today command"""
    user = db.query(User).filter(User.telegram_id == message.from_user.id).first()
    if not user:
        await message.answer("❌ User not found. Please use /start first.")
        return
    
    # Get current pointer and reading
    current_month, current_day = get_current_pointer(db, user)
    reading = get_reading_by_pointer(db, current_month, current_day)
    
    if not reading:
        await message.answer(get_no_readings_message(), parse_mode='MarkdownV2')
        return
    
    # Get stats and format message
    stats = get_user_stats(db, user)
    text = format_reading_text(reading, stats)
    
    # Create keyboard
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton("✅ Read", callback_data=f"read|{reading['month']}|{reading['day']}"),
            InlineKeyboardButton("🛌 Break", callback_data=f"break|{reading['month']}|{reading['day']}")
        ],
        [InlineKeyboardButton("📖 Next", callback_data="next")]
    ])
    
    await message.answer(text, parse_mode='MarkdownV2', reply_markup=keyboard)


async def next_command(message: types.Message, db: Session):
    """Handle /next command"""
    user = db.query(User).filter(User.telegram_id == message.from_user.id).first()
    if not user:
        await message.answer("❌ User not found. Please use /start first.")
        return
    
    # Get next reading
    reading = get_next_reading(db, user)
    if not reading:
        await message.answer(get_no_readings_message(), parse_mode='MarkdownV2')
        return
    
    # Get stats and format message
    stats = get_user_stats(db, user)
    text = format_reading_text(reading, stats)
    
    # Create keyboard
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton("✅ Read", callback_data=f"read|{reading['month']}|{reading['day']}"),
            InlineKeyboardButton("🛌 Break", callback_data=f"break|{reading['month']}|{reading['day']}")
        ],
        [InlineKeyboardButton("📖 Next", callback_data="next")]
    ])
    
    await message.answer(text, parse_mode='MarkdownV2', reply_markup=keyboard)


async def stats_command(message: types.Message, db: Session):
    """Handle /stats command"""
    user = db.query(User).filter(User.telegram_id == message.from_user.id).first()
    if not user:
        await message.answer("❌ User not found. Please use /start first.")
        return
    
    stats = get_user_stats(db, user)
    text = get_stats_message(stats)
    
    await message.answer(text, parse_mode='MarkdownV2')


async def handle_callback_query(callback_query: CallbackQuery, db: Session, bot: Bot):
    """Handle callback queries from inline keyboards"""
    # Check if callback was already processed
    existing_callback = db.query(ProcessedCallback).filter(
        ProcessedCallback.callback_id == callback_query.id
    ).first()
    
    if existing_callback:
        await callback_query.answer("Already processed.")
        return
    
    # Mark callback as processed
    processed = ProcessedCallback(callback_id=callback_query.id)
    db.add(processed)
    db.commit()
    
    user = db.query(User).filter(User.telegram_id == callback_query.from_user.id).first()
    if not user:
        await callback_query.answer("❌ User not found.")
        return
    
    data = callback_query.data
    parts = data.split('|')
    action = parts[0]
    
    try:
        if action == "read":
            plan_month = int(parts[1])
            plan_day = int(parts[2])
            
            # Record reading
            record_reading(db, user, plan_month, plan_day)
            
            # Get updated stats
            stats = get_user_stats(db, user)
            streak = stats['streak']
            
            # Send celebration message
            celebration = get_streak_celebration_message(streak)
            await callback_query.message.answer(celebration, parse_mode='MarkdownV2')
            
            await callback_query.answer("✅ Reading recorded!")
            
        elif action == "break":
            plan_month = int(parts[1])
            plan_day = int(parts[2])
            
            # Check if user can take a break
            if not can_take_break(db, user):
                await callback_query.answer(get_break_rejected_message(), show_alert=True)
                return
            
            # Record break
            record_break(db, user, plan_month, plan_day)
            
            await callback_query.answer("🛌 Break recorded!")
            await callback_query.message.answer(get_break_recorded_message(), parse_mode='MarkdownV2')
            
        elif action == "next":
            # Send next reading (without modifying stored progress)
            current_month, current_day = get_current_pointer(db, user)
            next_month, next_day = get_next_pointer(current_month, current_day)
            reading = get_reading_by_pointer(db, next_month, next_day)
            
            if not reading:
                await callback_query.answer("No more readings available.")
                return
            
            stats = get_user_stats(db, user)
            text = format_reading_text(reading, stats)
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton("✅ Read", callback_data=f"read|{reading['month']}|{reading['day']}"),
                    InlineKeyboardButton("🛌 Break", callback_data=f"break|{reading['month']}|{reading['day']}")
                ],
                [InlineKeyboardButton("📖 Next", callback_data="next")]
            ])
            
            await callback_query.message.answer(text, parse_mode='MarkdownV2', reply_markup=keyboard)
            await callback_query.answer("📖 Next reading sent!")
            
    except Exception as e:
        await callback_query.answer(f"❌ Error: {str(e)}", show_alert=True)


def register_handlers(dp: Dispatcher):
    """Register all handlers with the dispatcher"""
    
    @dp.message_handler(commands=['start'])
    async def start_handler(message: types.Message):
        from app.db import SessionLocal
        db = SessionLocal()
        try:
            await start_command(message, db)
        finally:
            db.close()
    
    @dp.message_handler(commands=['help'])
    async def help_handler(message: types.Message):
        await help_command(message)
    
    @dp.message_handler(commands=['settz'])
    async def settz_handler(message: types.Message):
        from app.db import SessionLocal
        db = SessionLocal()
        try:
            await settz_command(message, db)
        finally:
            db.close()
    
    @dp.message_handler(commands=['today'])
    async def today_handler(message: types.Message):
        from app.db import SessionLocal
        db = SessionLocal()
        try:
            await today_command(message, db)
        finally:
            db.close()
    
    @dp.message_handler(commands=['next'])
    async def next_handler(message: types.Message):
        from app.db import SessionLocal
        db = SessionLocal()
        try:
            await next_command(message, db)
        finally:
            db.close()
    
    @dp.message_handler(commands=['stats'])
    async def stats_handler(message: types.Message):
        from app.db import SessionLocal
        db = SessionLocal()
        try:
            await stats_command(message, db)
        finally:
            db.close()
    
    @dp.callback_query_handler()
    async def callback_handler(callback_query: CallbackQuery):
        from app.db import SessionLocal
        db = SessionLocal()
        try:
            await handle_callback_query(callback_query, db, dp.bot)
        finally:
            db.close()