"""
Kingdom Conquest Bot - Main Entry Point.
Sets up Telegram handlers and starts the async event loop.
Requires: python-telegram-bot v20+, aiosqlite, Pillow
"""
import logging
import os
import sys

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ─── Import all handlers ───
from handlers.start import (
    handle_start, handle_callback as start_callback,
    process_kingdom_name, process_alliance_name,
    process_flag_choice, process_hero_name,
)
from handlers.dashboard import handle_dashboard
from handlers.attack import handle_attack, handle_attack_callback
from handlers.build import handle_build, handle_build_callback
from handlers.army import handle_army, handle_army_callback
from handlers.map_system import handle_map, handle_map_callback
from handlers.quests import handle_quests, handle_quest_callback
from handlers.alliance import handle_alliance, handle_alliance_callback
from handlers.heroes import handle_heroes, handle_heroes_callback
from handlers.spy import handle_spy, handle_spy_callback
from handlers.games import handle_games, handle_games_callback
from handlers.leaderboard import handle_leaderboard, handle_leaderboard_callback
from handlers.bounty import handle_bounty_command, handle_bounties_command, menu_bounty
from handlers.events import handle_event_callback
from handlers.settings import handle_settings, handle_settings_callback
from handlers.admin import handle_admin_command
from tasks.scheduler import GameScheduler

# Scheduler instance
scheduler = GameScheduler()


def main():
    TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
    
    application = Application.builder().token(TOKEN).build()
    
    # Store scheduler in bot_data for access across handlers
    application.bot_data['scheduler'] = scheduler
    scheduler.set_bot(application.bot)

    # ─── Command Handlers ───
    application.add_handler(CommandHandler("start", handle_start))
    application.add_handler(CommandHandler("dashboard", handle_dashboard))
    application.add_handler(CommandHandler("attack", handle_attack))
    application.add_handler(CommandHandler("build", handle_build))
    application.add_handler(CommandHandler("army", handle_army))
    application.add_handler(CommandHandler("map", handle_map))
    application.add_handler(CommandHandler("quests", handle_quests))
    application.add_handler(CommandHandler("alliance", handle_alliance))
    application.add_handler(CommandHandler("hero", handle_heroes))
    application.add_handler(CommandHandler("spy", handle_spy))
    application.add_handler(CommandHandler("games", handle_games))
    application.add_handler(CommandHandler("leaderboard", handle_leaderboard))
    application.add_handler(CommandHandler("bounty", handle_bounty_command))
    application.add_handler(CommandHandler("bounties", handle_bounties_command))
    application.add_handler(CommandHandler("settings", handle_settings))
    application.add_handler(CommandHandler("admin", handle_admin_command))

    # ─── Callback Query Router ───
    # FIXED: Removed PatternCallbackHandler (doesn't exist in python-telegram-bot v20+)
    # Using CallbackQueryHandler with pattern parameter instead
    application.add_handler(CallbackQueryHandler(handle_all_callbacks))

    # ─── Message Handlers (text input flows) ───
    # Process text inputs for kingdom name, alliance name, hero name, flag choice
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_text_messages
    ))

    # ─── Error Handler ───
    application.add_error_handler(error_handler)

    # Start scheduler
    application.job_queue.run_once(lambda c: scheduler.start(), when=5)

    logger.info("🤖 Kingdom Conquest Bot started!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


async def handle_all_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Central callback router - routes callbacks to appropriate handlers."""
    query = update.callback_query
    if not query or not query.data:
        return
    
    data = query.data
    
    try:
        # Start menu callbacks
        if data == "menu_start":
            await start_callback(update, context)
        elif data == "menu_kingdom":
            await start_callback(update, context)
        elif data == "create_kingdom":
            await start_callback(update, context)
        elif data == "choose_flag":
            await start_callback(update, context)
        elif data == "menu_help":
            await start_callback(update, context)
        elif data.startswith("help_page_"):
            await start_callback(update, context)
        elif data.startswith("flag_"):
            await process_flag_choice(update, context)
        elif data == "back_dashboard":
            await start_callback(update, context)
        # Attack callbacks
        elif data.startswith("menu_attack") or data.startswith("attack_"):
            await handle_attack_callback(update, context)
        # Build callbacks
        elif data.startswith("menu_build") or data.startswith("build_"):
            await handle_build_callback(update, context)
        # Army callbacks
        elif data.startswith("menu_army") or data.startswith("army_") or data.startswith("train_"):
            await handle_army_callback(update, context)
        # Map callbacks
        elif data.startswith("menu_map") or data.startswith("map_") or data.startswith("scout_tile"):
            await handle_map_callback(update, context)
        # Quest callbacks
        elif data.startswith("menu_quests") or data.startswith("quest_"):
            await handle_quest_callback(update, context)
        # Alliance callbacks
        elif data.startswith("menu_alliance") or data.startswith("alliance_") or data.startswith("join_alliance:"):
            await handle_alliance_callback(update, context)
        # Hero callbacks
        elif data.startswith("menu_heroes") or data.startswith("hero_") or data.startswith("skill_"):
            await handle_heroes_callback(update, context)
        # Spy callbacks
        elif data.startswith("menu_spy") or data.startswith("spy_"):
            await handle_spy_callback(update, context)
        # Games callbacks
        elif data.startswith("menu_games") or data.startswith("game_") or data.startswith("dice_") or data.startswith("spin_") or data.startswith("quiz_"):
            await handle_games_callback(update, context)
        # Leaderboard callbacks
        elif data.startswith("menu_leaderboard") or data.startswith("lb_"):
            await handle_leaderboard_callback(update, context)
        # Bounty callbacks
        elif data == "menu_bounty":
            await menu_bounty(update, context)
        # Event/decision callbacks
        elif data.startswith("decision:"):
            await handle_event_callback(update, context)
        # Settings callbacks
        elif data.startswith("menu_settings") or data.startswith("settings_"):
            await handle_settings_callback(update, context)
        else:
            await query.answer("Unknown action", show_alert=True)
    except Exception as e:
        logger.error(f"Callback error: {e}", exc_info=True)
        try:
            await query.edit_message_text(
                "❌ <b>Something went wrong!</b>\n\nPlease try again.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🏠 Dashboard", callback_data="back_dashboard")],
                ]),
                parse_mode='HTML'
            )
        except Exception:
            pass


async def handle_text_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages for multi-step flows."""
    user_id = update.effective_user.id
    
    # Check if user is in a creation flow
    if context.user_data.get('creating_kingdom'):
        await process_kingdom_name(update, context)
        return
    elif context.user_data.get('creating_alliance'):
        await process_alliance_name(update, context)
        return
    elif context.user_data.get('naming_hero'):
        await process_hero_name(update, context)
        return
    
    # Default: echo or ignore
    await update.message.reply_text(
        "❓ Unknown command! Use /dashboard to open the game menu.",
        parse_mode='HTML'
    )


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors gracefully."""
    logger.error(f"Exception while handling an update: {context.error}", exc_info=context.error)
    
    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "❌ <b>An error occurred!</b>\n\nPlease try again later.",
                parse_mode='HTML'
            )
        except Exception:
            pass


if __name__ == "__main__":
    main()
