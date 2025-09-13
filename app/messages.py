import re
from typing import Dict, Any


def escape_markdown_v2(text: str) -> str:
    """Escape text for MarkdownV2"""
    # Characters that need escaping in MarkdownV2
    escape_chars = r'[_*[\]()~`>#+=|{}.!-]'
    return re.sub(escape_chars, r'\\\1', text)


def get_daily_card_template() -> str:
    """Template for daily reading card (MarkdownV2)"""
    return """📖 *Day {day} — Month {month}*

🔥 Current streak: {streak} day{plural}
🛌 Breaks left \\(last 30 days\\): {breaks_left}/5

🧭 *New Testament:*
\\- {nt1}
\\- {nt2}

🌿 *Old Testament:*
\\- {ot1}
\\- {ot2}"""


def get_help_message() -> str:
    """Help message with commands and break rules (MarkdownV2)"""
    return """🤖 *Bible Reading Tracker Bot*

*Commands:*
/start \\- Register and get your first reading
/help \\- Show this help message
/settz \\- Set your timezone \\(e\\.g\\., /settz America/New_York\\)
/today \\- Resend today's reading card
/next \\- Get the next pending reading
/stats \\- Show your reading statistics

*Break Rules:*
• You can take up to 5 breaks in any 30\\-day period
• Breaks don't advance your reading progress
• If you exceed 5 breaks, you'll need to catch up before taking more

*How it works:*
• Each month has 25 days of readings
• After Day 25, you automatically move to the next month
• Your streak counts consecutive days with completed readings
• Use the buttons to mark readings as complete or take breaks"""


def get_stats_message(stats: Dict[str, Any]) -> str:
    """Generate stats message (MarkdownV2)"""
    return f"""📊 *Your Reading Statistics*

🔥 Current streak: {stats['streak']} day{'s' if stats['streak'] != 1 else ''}
🛌 Breaks used \\(last 30 days\\): {stats['breaks_used']}/5
📖 Next reading: Day {stats['next_day']} — Month {stats['next_month']}
📅 Total completed: {stats['total_completed']} days"""


def get_nudge_message() -> str:
    """Evening nudge message (MarkdownV2)"""
    return "⏰ Quick nudge: remember to read today\\! You've got this\\. 🙏"


def get_streak_celebration_message(streak: int) -> str:
    """Celebration message for streak milestones (MarkdownV2)"""
    if streak % 7 == 0 and streak > 0:
        return f"🎁 {streak}\\-day streak\\! Treat yourself today — you've earned it\\."
    return f"🎉 Well done\\! See you at the next reading\\.\n🔥 Streak: {streak} day{'s' if streak != 1 else ''} in a row\\."


def get_break_rejected_message() -> str:
    """Message when break is rejected due to limit (MarkdownV2)"""
    return "❌ Sorry, you've used all 5 breaks in the last 30 days\\. Please complete a reading to reset your break count\\."


def get_break_recorded_message() -> str:
    """Message when break is successfully recorded (MarkdownV2)"""
    return "🛌 Break recorded\\. Have a good rest today\\. I'll remind you of the same reading tomorrow\\."


def get_reading_recorded_message() -> str:
    """Message when reading is successfully recorded (MarkdownV2)"""
    return "✅ Reading marked as complete\\!"


def get_no_readings_message() -> str:
    """Message when no readings are available (MarkdownV2)"""
    return "📚 No more readings available at the moment\\. Great job on your progress\\!"


def format_reading_text(reading: Dict[str, Any], stats: Dict[str, Any]) -> str:
    """Format reading text with stats (MarkdownV2)"""
    template = get_daily_card_template()
    
    # Escape dynamic content for MarkdownV2
    nt1 = escape_markdown_v2(f"{reading['nt1_book']} {reading['nt1_reading']}")
    nt2 = escape_markdown_v2(f"{reading['nt2_book']} {reading['nt2_reading']}")
    ot1 = escape_markdown_v2(f"{reading['ot1_book']} {reading['ot1_reading']}")
    ot2 = escape_markdown_v2(f"{reading['ot2_book']} {reading['ot2_reading']}")
    
    return template.format(
        day=reading['day'],
        month=reading['month'],
        streak=stats['streak'],
        plural='s' if stats['streak'] != 1 else '',
        breaks_left=stats['breaks_left'],
        nt1=nt1,
        nt2=nt2,
        ot1=ot1,
        ot2=ot2
    )