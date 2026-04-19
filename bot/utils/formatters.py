"""
Text formatting utilities for Kingdom Conquest.
Number formatting, progress bars, and message builders.
"""


def format_number(n: int) -> str:
    """Format large numbers with commas (Indian style)."""
    if n is None:
        return "0"
    return f"{n:,}"


def format_power(power: int) -> str:
    """Format power with appropriate suffix."""
    if power >= 1_000_000:
        return f"{power / 1_000_000:.1f}M"
    elif power >= 1000:
        return f"{power / 1000:.1f}K"
    return str(power)


def progress_bar(current: int, total: int, length: int = 10) -> str:
    """Create a text progress bar."""
    if total <= 0:
        return "□" * length
    filled = int((current / total) * length)
    filled = min(filled, length)
    return "■" * filled + "□" * (length - filled)


def format_time_remaining(seconds: int) -> str:
    """Format seconds into human readable time."""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        return f"{seconds // 60}m {seconds % 60}s"
    elif seconds < 86400:
        return f"{seconds // 3600}h {(seconds % 3600) // 60}m"
    else:
        return f"{seconds // 86400}d {(seconds % 86400) // 3600}h"


def format_battle_summary(result: dict, attacker_name: str = "You", defender_name: str = "Enemy") -> str:
    """Format a battle result into a readable summary.
    
    Added to fix missing import in attack.py.
    """
    if result.get('won'):
        return (
            f"🎉 <b>VICTORY!</b>\n"
            f"━━━━━━━━━━━━━━\n\n"
            f"⚔️ Attacker: {attacker_name}\n"
            f"🛡 Defender: {defender_name}\n\n"
            f"💰 Gold Stolen: {format_number(result.get('gold_stolen', 0))}\n"
            f"💀 Your Losses: {format_number(result.get('attacker_losses', 0))}\n"
            f"💀 Enemy Losses: {format_number(result.get('defender_losses', 0))}\n\n"
            f"{result.get('message', '')}"
        )
    else:
        return (
            f"💀 <b>DEFEAT!</b>\n"
            f"━━━━━━━━━━━━━━\n\n"
            f"⚔️ Attacker: {attacker_name}\n"
            f"🛡 Defender: {defender_name}\n\n"
            f"💀 Your Losses: {format_number(result.get('attacker_losses', 0))}\n"
            f"💀 Enemy Losses: {format_number(result.get('defender_losses', 0))}\n\n"
            f"{result.get('message', '')}"
        )


def format_spy_report(target_name: str, intel_level: str, army_size: int = 0, 
                      wall_level: int = 0, gold: int = 0, food: int = 0) -> str:
    """Format a spy report.
    
    Added to fix missing import in attack.py.
    """
    quality_emojis = {
        'basic': '📄',
        'detailed': '📋',
        'full': '🔍'
    }
    emoji = quality_emojis.get(intel_level, '📄')
    
    report = (
        f"🕵️ <b>SPY REPORT</b>\n"
        f"━━━━━━━━━━━━━━\n\n"
        f"👑 Target: {target_name}\n"
        f"📊 Intel Quality: {emoji} {intel_level.upper()}\n\n"
    )
    
    if intel_level in ['basic', 'detailed', 'full']:
        report += f"⚔️ Army Size: ~{army_size}\n"
        report += f"🛡 Wall Level: {wall_level}\n"
    
    if intel_level in ['detailed', 'full']:
        report += f"💰 Gold: ~{format_number(gold)}\n"
        report += f"🍖 Food: ~{format_number(food)}\n"
    
    report += "\n━━━━━━━━━━━━━━"
    return report


def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to max length with ellipsis."""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


def escape_html(text: str) -> str:
    """Escape HTML special characters for Telegram."""
    if not text:
        return ""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
