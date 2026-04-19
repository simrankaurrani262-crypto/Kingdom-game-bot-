"""
Kingdom Conquest - Telegram Multiplayer Strategy Bot
Enhanced main entry point with scheduler, photo support, and real visuals.
"""
import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

from config import TELEGRAM_BOT_TOKEN, USE_WEBHOOK, WEBHOOK_URL, WEBHOOK_PORT, ADMIN_TELEGRAM_ID
from models.database import Database
from services.notification import NotificationService
from tasks.scheduler import GameScheduler

# ===== NEW: VISUAL HANDLERS IMPORT =====
try:
    from handlers.stats import (
        handler_stats, handler_stats_callback,
        handler_army_chart, handler_resource_chart,
        handler_battle_stats, handler_power_profile
    )
    from handlers.visual_commands import (
        handler_animate_battle, handler_levelup_animation, handler_reward_animation,
        handler_training_animation, handler_achievement_animation,
        handler_hero_card, handler_kingdom_banner, handler_battle_report_card,
        handler_spy_report_card, handler_compare, handler_achievements_chart,
        handler_leaderboard_chart, handler_leaderboard_podium,
        handler_spin_wheel, handler_notification_card, handler_visual_help
    )
    VISUAL_HANDLERS_ENABLED = True
except ImportError as e:
    print(f"[ERROR] Visual handlers load nahi hue: {e}")
    VISUAL_HANDLERS_ENABLED = False

# Handler imports
from handlers.start import (
    handler_start, handle_start_callback,
    process_kingdom_name, process_flag_selection,
    process_trait_selection, handle_tutorial_callback,
    handle_text_input,
)
from handlers.dashboard import render_dashboard, handle_dashboard_callback
from handlers.build import handle_build, menu_build, handle_build_callback
from handlers.army import handle_army, menu_army, handle_army_callback
from handlers.attack import handle_attack, menu_attack, handle_attack_callback
from handlers.map_system import handle_map, menu_map, handle_map_callback, handle_scout_command
from handlers.alliance import handle_alliance, menu_alliance, handle_alliance_callback, process_alliance_name
from handlers.quests import handle_quests, menu_quests, handle_quest_callback
from handlers.heroes import handle_heroes, menu_heroes, handle_heroes_callback
from handlers.spy import handle_spy, menu_spy, handle_spy_callback
from handlers.black_market import handle_market, menu_market, handle_market_callback
from handlers.games import handle_games, menu_games, handle_games_callback
from handlers.leaderboard import handle_leaderboard, menu_leaderboard, handle_leaderboard_callback
from handlers.settings import handle_settings, menu_settings, handle_settings_callback
from handlers.admin import handle_admin_command
from handlers.bounty import handle_bounty_command, handle_bounties_command
from handlers.survival import handle_survival, menu_survival, handle_survival_callback
from handlers.events import handle_event_callback

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

db = Database()
notif_service = NotificationService()
game_scheduler = GameScheduler()


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors gracefully."""
    logger.error(f"Update caused error: {context.error}")
    if update and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "❌ <b>Something went wrong!</b>\n\n"
                "Please try again.\n"
                "Use /dashboard to return to main menu.",
                parse_mode='HTML'
            )
        except Exception:
            pass


async def post_init(application: Application):
    """Post-initialization: set up services and scheduler."""
    notif_service.set_bot(application.bot)
    game_scheduler.set_bot(application.bot)
    await game_scheduler.start()
    
    await application.bot.set_my_commands([
        ("start", "Start the game / Dashboard"),
        ("dashboard", "Open main dashboard"),
        ("attack", "Attack enemies"),
        ("build", "Manage buildings"),
        ("army", "Army management"),
        ("map", "World map"),
        ("alliance", "Alliance hub"),
        ("quests", "Quest board"),
        ("hero", "Hero roster"),
        ("spy", "Spy missions"),
        ("raid", "Quick raid"),
        ("market", "Black market"),
        ("gems", "Premium shop"),
        ("leaderboard", "Rankings"),
        ("settings", "Preferences"),
        ("survival", "Survival mode"),
        ("bounty", "Place bounty"),
        ("bounties", "List bounties"),
        ("scout", "Scout map tile"),
        ("help", "How to play"),
    ])
    
    logger.info("Bot initialized! Commands set. Scheduler running.")


async def post_shutdown(application: Application):
    """Cleanup on shutdown."""
    await game_scheduler.stop()
    logger.info("Bot shutdown complete.")


def main():
    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "your_bot_token_here":
        logger.error("TELEGRAM_BOT_TOKEN not set!")
        print("\n❌ Set your bot token in .env file first!")
        sys.exit(1)
    
    application = (
        Application.builder()
        .token(TELEGRAM_BOT_TOKEN)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .build()
    )
    
    # ===== COMMAND HANDLERS =====
    application.add_handler(CommandHandler("start", handler_start))
    application.add_handler(CommandHandler("dashboard", render_dashboard))
    application.add_handler(CommandHandler("attack", handle_attack))
    application.add_handler(CommandHandler("build", handle_build))
    application.add_handler(CommandHandler("army", handle_army))
    application.add_handler(CommandHandler("map", handle_map))
    application.add_handler(CommandHandler("alliance", handle_alliance))
    application.add_handler(CommandHandler("quests", handle_quests))
    application.add_handler(CommandHandler("hero", handle_heroes))
    application.add_handler(CommandHandler("spy", handle_spy))
    application.add_handler(CommandHandler("raid", handle_attack))
    application.add_handler(CommandHandler("market", handle_market))
    application.add_handler(CommandHandler("leaderboard", handle_leaderboard))
    application.add_handler(CommandHandler("gems", handle_market))
    application.add_handler(CommandHandler("settings", handle_settings))
    application.add_handler(CommandHandler("help", handler_start))
    application.add_handler(CommandHandler("scout", handle_scout_command))
    application.add_handler(CommandHandler("survival", handle_survival))
    application.add_handler(CommandHandler("bounty", handle_bounty_command))
    application.add_handler(CommandHandler("bounties", handle_bounties_command))
    application.add_handler(CommandHandler("admin", handle_admin_command))

    # ===== NEW: VISUAL COMMAND HANDLERS =====
    if VISUAL_HANDLERS_ENABLED:
        application.add_handler(CommandHandler("stats", handler_stats))
        application.add_handler(CommandHandler("army_chart", handler_army_chart))
        application.add_handler(CommandHandler("resource_chart", handler_resource_chart))
        application.add_handler(CommandHandler("battle_stats", handler_battle_stats))
        application.add_handler(CommandHandler("power_profile", handler_power_profile))

        application.add_handler(CommandHandler("animate_battle", handler_animate_battle))
        application.add_handler(CommandHandler("levelup_anim", handler_levelup_animation))
        application.add_handler(CommandHandler("reward_anim", handler_reward_animation))
        application.add_handler(CommandHandler("train_anim", handler_training_animation))
        application.add_handler(CommandHandler("achievement_anim", handler_achievement_animation))
        application.add_handler(CommandHandler("spin", handler_spin_wheel))

        application.add_handler(CommandHandler("hero_card", handler_hero_card))
        application.add_handler(CommandHandler("kingdom_banner", handler_kingdom_banner))
        application.add_handler(CommandHandler("battle_report", handler_battle_report_card))
        application.add_handler(CommandHandler("spy_report_card", handler_spy_report_card))
        application.add_handler(CommandHandler("compare", handler_compare))
        application.add_handler(CommandHandler("achievements_chart", handler_achievements_chart))
        application.add_handler(CommandHandler("leaderboard_chart", handler_leaderboard_chart))
        application.add_handler(CommandHandler("podium", handler_leaderboard_podium))
        application.add_handler(CommandHandler("notify_test", handler_notification_card))
        application.add_handler(CommandHandler("visual_help", handler_visual_help))

    # ===== CALLBACK HANDLERS =====
    if VISUAL_HANDLERS_ENABLED:
        application.add_handler(CallbackQueryHandler(handler_stats_callback, pattern='^stats_'))

    application.add_handler(CallbackQueryHandler(handle_start_callback, pattern="^(start_game|how_to_play|help_page:|back_welcome)$"))
    application.add_handler(CallbackQueryHandler(process_flag_selection, pattern="^flag:"))
    application.add_handler(CallbackQueryHandler(process_trait_selection, pattern="^trait:"))
    application.add_handler(CallbackQueryHandler(handle_tutorial_callback, pattern="^tutorial_"))
    application.add_handler(CallbackQueryHandler(handle_dashboard_callback, pattern="^(back_dashboard|noop)$"))
    application.add_handler(CallbackQueryHandler(menu_attack, pattern="^menu_attack$"))
    application.add_handler(CallbackQueryHandler(menu_build, pattern="^menu_build$"))
    application.add_handler(CallbackQueryHandler(menu_map, pattern="^menu_map$"))
    application.add_handler(CallbackQueryHandler(menu_alliance, pattern="^menu_alliance$"))
    application.add_handler(CallbackQueryHandler(menu_quests, pattern="^menu_quests$"))
    application.add_handler(CallbackQueryHandler(menu_heroes, pattern="^menu_heroes$"))
    application.add_handler(CallbackQueryHandler(menu_spy, pattern="^menu_spy$"))
    application.add_handler(CallbackQueryHandler(menu_market, pattern="^menu_market$"))
    application.add_handler(CallbackQueryHandler(menu_games, pattern="^menu_games$"))
    application.add_handler(CallbackQueryHandler(menu_leaderboard, pattern="^menu_leaderboard$"))
    application.add_handler(CallbackQueryHandler(menu_settings, pattern="^menu_settings$"))
    application.add_handler(CallbackQueryHandler(menu_survival, pattern="^menu_survival$"))
    application.add_handler(CallbackQueryHandler(handle_build_callback, pattern="^build_"))
    application.add_handler(CallbackQueryHandler(handle_army_callback, pattern="^army_"))
    application.add_handler(CallbackQueryHandler(handle_attack_callback, pattern="^(attack_|battle_|revenge_|raid_)"))
    application.add_handler(CallbackQueryHandler(handle_map_callback, pattern="^map_"))
    application.add_handler(CallbackQueryHandler(handle_alliance_callback, pattern="^(alliance_|join_alliance:)"))
    application.add_handler(CallbackQueryHandler(handle_quest_callback, pattern="^quest_"))
    application.add_handler(CallbackQueryHandler(handle_heroes_callback, pattern="^(hero_|skill_)"))
    application.add_handler(CallbackQueryHandler(handle_spy_callback, pattern="^(spy_|spy_target:)"))
    application.add_handler(CallbackQueryHandler(handle_market_callback, pattern="^market_"))
    application.add_handler(CallbackQueryHandler(handle_games_callback, pattern="^(game_|dice_|spin_|quiz_)"))
    application.add_handler(CallbackQueryHandler(handle_leaderboard_callback, pattern="^lb_"))
    application.add_handler(CallbackQueryHandler(handle_settings_callback, pattern="^settings_"))
    application.add_handler(CallbackQueryHandler(handle_survival_callback, pattern="^survival_"))
    application.add_handler(CallbackQueryHandler(handle_event_callback, pattern="^decision:"))
    
    # ===== TEXT MESSAGES =====
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input))
    
    application.add_error_handler(error_handler)
    
    logger.info("Starting Kingdom Conquest Bot...")
    
    if USE_WEBHOOK:
        application.run_webhook(
            listen="0.0.0.0",
            port=WEBHOOK_PORT,
            webhook_url=WEBHOOK_URL,
        )
    else:
        application.run_polling(
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES,
        )


if __name__ == "__main__":
    main()
