"""
Formatting utilities for displaying game data.
"""
from datetime import datetime, timedelta
from typing import Optional


def format_number(num: int) -> str:
    """Format large numbers with commas."""
    return f"{num:,}"


def format_time_remaining(expires_at: Optional[datetime]) -> str:
    """Format time remaining until expiry."""
    if not expires_at:
        return "❌ None"
    
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
    
    now = datetime.now()
    if expires_at <= now:
        return "❌ Expired"
    
    diff = expires_at - now
    hours, remainder = divmod(int(diff.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)
    
    if hours > 0:
        return f"⏳ {hours}h {minutes}m"
    elif minutes > 0:
        return f"⏳ {minutes}m {seconds}s"
    else:
        return f"⏳ {seconds}s"


def format_duration(minutes: int) -> str:
    """Format duration in minutes to readable string."""
    if minutes >= 60:
        hours = minutes // 60
        mins = minutes % 60
        return f"{hours}h {mins}m"
    return f"{minutes}m"


def format_building_list(buildings: list) -> str:
    """Format building list for display."""
    lines = []
    for b in buildings:
        emoji = {
            'town_hall': '🏰', 'gold_mine': '⛏', 'farm': '🌾',
            'barracks': '🏹', 'wall': '🛡'
        }.get(b['building_type'], '🏗')
        name = b['building_type'].replace('_', ' ').title()
        status = "⬆️ Upgrading" if b.get('is_upgrading') else "✅ Ready"
        lines.append(f"{emoji} {name}: Lv.{b['level']} {status}")
    return '\n'.join(lines)


def format_army_composition(army: dict) -> str:
    """Format army composition."""
    total = army.get('infantry', 0) + army.get('archers', 0) + army.get('cavalry', 0)
    return (
        f"⚔️ Total: {total}\n"
        f"   🗡 Infantry: {army.get('infantry', 0)}\n"
        f"   🏹 Archers: {army.get('archers', 0)}\n"
        f"   🐎 Cavalry: {army.get('cavalry', 0)}"
    )


def format_battle_report(report: dict) -> str:
    """Format battle report message."""
    winner = report.get('winner', 'unknown')
    result_emoji = "🏆 VICTORY!" if winner == 'attacker' else "💀 DEFEAT!"
    
    rounds_text = ""
    for r in report.get('rounds', []):
        rounds_text += f"\n{r.get('action', '')}"
        rounds_text += f"\n💥 Damage: {r.get('damage', 0)}"
    
    a_loss = report.get('attacker_losses', {})
    d_loss = report.get('defender_losses', {})
    
    return f"""
⚔️ BATTLE REPORT
━━━━━━━━━━━━━━
{result_emoji}

⚔️ Rounds:{rounds_text}

💀 Losses:
Attacker: 🗡-{a_loss.get('infantry', 0)} 🏹-{a_loss.get('archers', 0)} 🐎-{a_loss.get('cavalry', 0)}
Defender: 🗡-{d_loss.get('infantry', 0)} 🏹-{d_loss.get('archers', 0)} 🐎-{d_loss.get('cavalry', 0)}

🏆 Rewards:
💰 +{format_number(report.get('gold_loot', 0))} Gold
⭐ +{report.get('xp_gain', 0)} XP
━━━━━━━━━━━━━━
"""


def create_progress_bar(current: int, maximum: int, length: int = 10) -> str:
    """Create a visual progress bar."""
    if maximum <= 0:
        return "▪️" * length
    filled = int((current / maximum) * length)
    filled = min(filled, length)
    return "▪️" * filled + "▫️" * (length - filled)


def create_resource_bar(current: int, maximum: int, emoji: str = "▪️") -> str:
    """Create a compact resource bar."""
    bar = create_progress_bar(current, maximum, 8)
    return f"{bar} {current}/{maximum}"


def get_defense_rating(defense_value: int) -> str:
    """Get defense rating label."""
    if defense_value < 100:
        return "Weak 🟡"
    elif defense_value < 300:
        return "Moderate 🟠"
    elif defense_value < 600:
        return "Strong 🔴"
    else:
        return "Unbreakable ⚫"


def format_leaderboard_entry(rank: int, name: str, flag: str, power: int,
                              is_player: bool = False) -> str:
    """Format a single leaderboard entry."""
    rank_emoji = {1: "🥇", 2: "🥈", 3: "🥉"}.get(rank, f"#{rank}")
    prefix = "👤" if not is_player else "🎯"
    return f"{rank_emoji} {prefix} {name} {flag} — {format_number(power)} Power"


def format_quest_line(quest: dict) -> str:
    """Format a quest entry."""
    status = "✅" if quest.get('completed') else "⏳"
    progress = quest.get('progress', 0)
    target = quest.get('target', 1)
    quest_type = quest.get('quest_type', 'Unknown')
    return f"{status} {quest_type}: {format_number(progress)}/{format_number(target)}"


def truncate_text(text: str, max_length: int = 800) -> str:
    """Truncate text to max length with ellipsis."""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


def format_kingdom_name(name: str, flag: str, title: str = None) -> str:
    """Format kingdom name with flag and title."""
    if title:
        return f"{title} {name} {flag}"
    return f"{name} {flag}"
