from datetime import datetime, timedelta, date
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func
from zoneinfo import ZoneInfo

from app.models import User, Plan, UserProgress, UserEvent
from app.config import settings


def get_user_timezone(user: User) -> ZoneInfo:
    """Get user's timezone as ZoneInfo object"""
    return ZoneInfo(user.timezone)


def get_user_local_now(user: User) -> datetime:
    """Get current time in user's timezone"""
    tz = get_user_timezone(user)
    return datetime.now(tz)


def get_user_local_date(user: User) -> date:
    """Get current date in user's timezone"""
    return get_user_local_now(user).date()


def get_current_pointer(db: Session, user: User) -> tuple[int, int]:
    """Get current pointer (month, day) for user"""
    # Check if user has any progress
    last_progress = db.query(UserProgress).filter(
        UserProgress.user_id == user.id
    ).order_by(desc(UserProgress.completed_at)).first()
    
    if not last_progress:
        # No progress yet, start from configured start point
        return settings.start_at_month, settings.start_at_day
    else:
        # Return the last completed reading position
        return last_progress.month, last_progress.day


def get_next_pointer(month: int, day: int) -> tuple[int, int]:
    """Calculate next pointer from current position"""
    next_month = month
    next_day = day + 1
    
    if next_day > settings.plan_days_per_month:
        # Move to next month
        next_day = 1
        next_month = next_month + 1
        if next_month > settings.plan_months:
            next_month = 1
    
    return next_month, next_day


def get_reading_by_pointer(db: Session, month: int, day: int) -> Optional[Dict[str, Any]]:
    """Get reading for specific month/day pointer"""
    # Query plan table with quoted column names
    plan = db.query(Plan).filter(
        and_(
            Plan.Month == month,
            Plan.Day == day
        )
    ).first()
    
    if not plan:
        return None
    
    return {
        'month': plan.Month,
        'day': plan.Day,
        'nt1_book': plan.NT1_Book,
        'nt1_reading': plan.NT1_Reading,
        'nt2_book': plan.NT2_Book,
        'nt2_reading': plan.NT2_Reading,
        'ot1_book': plan.OT1_Book,
        'ot1_reading': plan.OT1_Reading,
        'ot2_book': plan.OT2_Book,
        'ot2_reading': plan.OT2_Reading
    }


def get_next_reading(db: Session, user: User) -> Optional[Dict[str, Any]]:
    """Get the next pending reading for a user"""
    current_month, current_day = get_current_pointer(db, user)
    next_month, next_day = get_next_pointer(current_month, current_day)
    return get_reading_by_pointer(db, next_month, next_day)


def get_reading_streak(db: Session, user: User) -> int:
    """Calculate user's reading streak ending today"""
    tz = get_user_timezone(user)
    today = datetime.now(tz).date()
    
    # Get all read events in chronological order
    read_events = db.query(UserEvent).filter(
        and_(
            UserEvent.user_id == user.id,
            UserEvent.action == 'read'
        )
    ).order_by(UserEvent.created_at.desc()).all()
    
    # Group by date in user's timezone
    read_dates = set()
    for event in read_events:
        event_date = event.created_at.astimezone(tz).date()
        read_dates.add(event_date)
    
    # Count consecutive days ending today
    streak = 0
    current_date = today
    
    while current_date in read_dates:
        streak += 1
        current_date = current_date - timedelta(days=1)
    
    return streak


def get_breaks_used(db: Session, user: User) -> int:
    """Count breaks used in the last 30 days"""
    tz = get_user_timezone(user)
    now = datetime.now(tz)
    thirty_days_ago = now - timedelta(days=30)
    
    # Count break events in the last 30 days
    break_count = db.query(UserEvent).filter(
        and_(
            UserEvent.user_id == user.id,
            UserEvent.action == 'break',
            UserEvent.created_at >= thirty_days_ago
        )
    ).count()
    
    return min(break_count, settings.max_breaks_per_30_days)


def get_breaks_left(db: Session, user: User) -> int:
    """Get remaining breaks for user"""
    breaks_used = get_breaks_used(db, user)
    return max(0, settings.max_breaks_per_30_days - breaks_used)


def can_take_break(db: Session, user: User) -> bool:
    """Check if user can take a break"""
    return get_breaks_left(db, user) > 0


def record_reading(db: Session, user: User, plan_month: int, plan_day: int) -> None:
    """Record a reading completion and advance progress"""
    tz = get_user_timezone(user)
    now = datetime.now(tz)
    
    # Add to user_progress
    progress = UserProgress(
        user_id=user.id,
        month=plan_month,
        day=plan_day
    )
    db.add(progress)
    
    # Add to user_events
    event = UserEvent(
        user_id=user.id,
        action='read',
        plan_month=plan_month,
        plan_day=plan_day
    )
    db.add(event)
    
    # Calculate next position (advance to next day)
    next_month, next_day = get_next_pointer(plan_month, plan_day)
    
    # Update user's current position
    user.current_month = next_month
    user.current_day = next_day
    
    db.commit()


def record_break(db: Session, user: User, plan_month: int, plan_day: int) -> None:
    """Record a break (doesn't advance progress)"""
    event = UserEvent(
        user_id=user.id,
        action='break',
        plan_month=plan_month,
        plan_day=plan_day
    )
    db.add(event)
    db.commit()


def record_nudge(db: Session, user: User) -> None:
    """Record that a nudge was sent"""
    event = UserEvent(
        user_id=user.id,
        action='nudge'
    )
    db.add(event)
    db.commit()


def was_nudged_today(db: Session, user: User) -> bool:
    """Check if user was nudged today"""
    tz = get_user_timezone(user)
    today = datetime.now(tz).date()
    
    nudge_today = db.query(UserEvent).filter(
        and_(
            UserEvent.user_id == user.id,
            UserEvent.action == 'nudge',
            func.date(UserEvent.created_at.astimezone(tz)) == today
        )
    ).first()
    
    return nudge_today is not None


def did_read_today(db: Session, user: User) -> bool:
    """Check if user read today"""
    tz = get_user_timezone(user)
    today = datetime.now(tz).date()
    
    read_today = db.query(UserEvent).filter(
        and_(
            UserEvent.user_id == user.id,
            UserEvent.action == 'read',
            func.date(UserEvent.created_at.astimezone(tz)) == today
        )
    ).first()
    
    return read_today is not None


def was_daily_card_sent_today(db: Session, user: User) -> bool:
    """Check if daily card was sent today"""
    tz = get_user_timezone(user)
    today = datetime.now(tz).date()
    
    return user.last_daily_sent == today


def mark_daily_card_sent_today(db: Session, user: User) -> None:
    """Mark that daily card was sent today"""
    tz = get_user_timezone(user)
    today = datetime.now(tz).date()
    
    user.last_daily_sent = today
    db.commit()


def mark_nudge_sent_today(db: Session, user: User) -> None:
    """Mark that nudge was sent today"""
    tz = get_user_timezone(user)
    today = datetime.now(tz).date()
    
    user.last_nudge_sent = today
    db.commit()


def get_user_stats(db: Session, user: User) -> Dict[str, Any]:
    """Get comprehensive user statistics"""
    current_month, current_day = get_current_pointer(db, user)
    next_month, next_day = get_next_pointer(current_month, current_day)
    streak = get_reading_streak(db, user)
    breaks_used = get_breaks_used(db, user)
    breaks_left = get_breaks_left(db, user)
    
    # Count total completed readings
    total_completed = db.query(UserProgress).filter(
        UserProgress.user_id == user.id
    ).count()
    
    return {
        'streak': streak,
        'breaks_used': breaks_used,
        'breaks_left': breaks_left,
        'current_month': current_month,
        'current_day': current_day,
        'next_month': next_month,
        'next_day': next_day,
        'total_completed': total_completed
    }


def is_time_for_daily_card(user: User) -> bool:
    """Check if it's time to send daily card (around 07:00 local time)"""
    tz = get_user_timezone(user)
    now = datetime.now(tz)
    current_time = now.time()
    
    # Check if it's around 07:00 (within 1 hour window)
    target_time = datetime.strptime("07:00", "%H:%M").time()
    time_diff = abs((current_time.hour * 60 + current_time.minute) - 
                   (target_time.hour * 60 + target_time.minute))
    
    return time_diff <= 60  # Within 1 hour


def is_time_for_nudge(user: User) -> bool:
    """Check if it's time to send nudge (around 20:00 local time)"""
    tz = get_user_timezone(user)
    now = datetime.now(tz)
    current_time = now.time()
    
    # Check if it's around 20:00 (within 1 hour window)
    target_time = datetime.strptime("20:00", "%H:%M").time()
    time_diff = abs((current_time.hour * 60 + current_time.minute) - 
                   (target_time.hour * 60 + target_time.minute))
    
    return time_diff <= 60  # Within 1 hour


def upsert_user(db: Session, telegram_id: int, username: str = None, 
                first_name: str = None, last_name: str = None) -> User:
    """Upsert user by telegram_id"""
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    
    if not user:
        # Create new user
        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            timezone=settings.default_tz,
            current_month=settings.start_at_month,
            current_day=settings.start_at_day
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        # Update existing user info
        user.username = username
        user.first_name = first_name
        user.last_name = last_name
        db.commit()
    
    return user


def ensure_user_progress(db: Session, user: User) -> None:
    """Ensure user has a progress record starting at Month=1, Day=1 if missing"""
    existing_progress = db.query(UserProgress).filter(
        UserProgress.user_id == user.id
    ).first()
    
    if not existing_progress:
        # Create initial progress record
        progress = UserProgress(
            user_id=user.id,
            month=settings.start_at_month,
            day=settings.start_at_day
        )
        db.add(progress)
        db.commit()