# Handlers package for Kingdom Conquest Bot
# Handlers package - Add new handlers
# Import existing handlers
# ... existing imports ...

# New handlers
try:
    from handlers.stats import (
        handler_stats, handler_stats_callback,
        handler_army_chart, handler_resource_chart,
        handler_battle_stats, handler_power_profile
    )
    STATS_HANDLER_AVAILABLE = True
except ImportError:
    STATS_HANDLER_AVAILABLE = False

try:
    from handlers.visual_commands import (
        handler_animate_battle, handler_levelup_animation, handler_reward_animation,
        handler_training_animation, handler_achievement_animation,
        handler_hero_card, handler_kingdom_banner, handler_battle_report_card,
        handler_spy_report_card, handler_compare, handler_achievements_chart,
        handler_leaderboard_chart, handler_leaderboard_podium,
        handler_spin_wheel, handler_notification_card, handler_visual_help
    )
    VISUAL_COMMANDS_AVAILABLE = True
except ImportError:
    VISUAL_COMMANDS_AVAILABLE = False
  
