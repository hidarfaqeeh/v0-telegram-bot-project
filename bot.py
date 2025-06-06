import asyncio
import logging
import signal
import sys
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ConversationHandler, filters
from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import TelegramError

# Import handlers
from handlers.main_handlers import MainHandlers
from handlers.task_handlers import TaskHandlers, TASK_NAME, SOURCE_CHAT, TARGET_CHAT, TASK_TYPE
from handlers.admin_handlers import AdminHandlers
from handlers.userbot_handlers import UserbotHandlers
from handlers.message_forwarder import MessageForwarder
from handlers.task_settings_handlers import TaskSettingsHandlers, BLOCKED_WORD_INPUT, REQUIRED_WORD_INPUT, REPLACEMENT_OLD_TEXT, REPLACEMENT_NEW_TEXT, DELAY_TIME_INPUT, WHITELIST_USER_INPUT, BLACKLIST_USER_INPUT, HEADER_TEXT_INPUT, FOOTER_TEXT_INPUT
from handlers.userbot_handlers import USERBOT_API_ID, USERBOT_API_HASH, USERBOT_PHONE, USERBOT_CODE
from utils.error_handler import ErrorHandler

# Import database
from database.models import db

# Import config
from config import Config

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Global variables
application = None
message_forwarder = None
is_running = False

async def initialize_bot():
    """Initialize bot and database"""
    global application, message_forwarder
    
    try:
        # Initialize database
        await db.initialize()
        logger.info("Database initialized")
        
        # Create application
        application = Application.builder().token(Config.BOT_TOKEN).build()
        
        # Initialize application
        await application.initialize()
        
        # Initialize message forwarder
        message_forwarder = MessageForwarder(application.bot)
        application.bot_data['message_forwarder'] = message_forwarder
        
        # Setup handlers
        setup_handlers(application)
        
        # تحميل جلسات Userbot النشطة
        await UserbotHandlers.load_userbot_sessions()
        
        logger.info("Bot initialized successfully")
        
    except Exception as e:
        logger.error(f"Error initializing bot: {e}")
        raise

def setup_handlers(app):
    """Setup all bot handlers"""
    
    # Command handlers
    app.add_handler(CommandHandler("start", MainHandlers.start_command))
    app.add_handler(CommandHandler("help", MainHandlers.help_command))
    app.add_handler(CommandHandler("menu", MainHandlers.main_menu))
    
    # Create task conversation handler
    create_task_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(TaskHandlers.create_task_start, pattern="^create_task$")],
        states={
            TASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, TaskHandlers.task_name_received)],
            SOURCE_CHAT: [MessageHandler(filters.TEXT & ~filters.COMMAND, TaskHandlers.source_chat_received)],
            TARGET_CHAT: [MessageHandler(filters.TEXT & ~filters.COMMAND, TaskHandlers.target_chat_received)],
            TASK_TYPE: [CallbackQueryHandler(TaskHandlers.task_type_selected, pattern="^task_type_")]
        },
        fallbacks=[CallbackQueryHandler(MainHandlers.main_menu, pattern="^main_menu$")],
        per_message=False,
        per_chat=True,
        per_user=True
    )
    app.add_handler(create_task_conv)
    
    # Callback query handlers
    callback_handlers = [
        # Main menu
        ("^main_menu$", MainHandlers.main_menu),
        ("^help$", MainHandlers.help_command),
        ("^statistics$", MainHandlers.statistics_menu),
        
        # Tasks
        ("^tasks_menu$", TaskHandlers.tasks_menu),
        ("^view_tasks$", TaskHandlers.view_tasks),
        ("^task_settings_", TaskHandlers.task_settings),
        ("^toggle_task_", TaskHandlers.toggle_task),
        ("^delete_task_", TaskHandlers.delete_task_confirm),
        ("^confirm_delete_task_", TaskHandlers.delete_task_confirmed),
        
        # Admin
        ("^admin_menu$", AdminHandlers.admin_menu),
        ("^admin_users$", AdminHandlers.manage_users),
        ("^admin_stats$", AdminHandlers.system_statistics),
        
        # Userbot
        ("^userbot_menu$", UserbotHandlers.userbot_menu),
        ("^userbot_connect$", UserbotHandlers.connect_userbot),
        ("^userbot_info$", UserbotHandlers.userbot_info),
        ("^userbot_status$", UserbotHandlers.userbot_status),
    ]
    
    for pattern, handler in callback_handlers:
        app.add_handler(CallbackQueryHandler(handler, pattern=pattern))
    
    # معالجات الإعدادات المتقدمة
    advanced_handlers = [
        # فلاتر الوسائط
        ("^media_filters_", TaskSettingsHandlers.media_filters_menu),
        ("^toggle_media_", TaskSettingsHandlers.toggle_media_type),
        ("^toggle_media_filter_", TaskSettingsHandlers.toggle_advanced_filter),
        ("^select_all_media_", TaskSettingsHandlers.select_all_media),
        ("^deselect_all_media_", TaskSettingsHandlers.deselect_all_media),
        
        # فلاتر النص
        ("^text_filters_", TaskSettingsHandlers.text_filters_menu),
        ("^add_blocked_word_", TaskSettingsHandlers.add_blocked_word_start),
        ("^add_required_word_", TaskSettingsHandlers.add_required_word_start),
        
        # فلاتر متقدمة
        ("^advanced_filters_", TaskSettingsHandlers.advanced_filters_menu),
        ("^toggle_link_filter_", TaskSettingsHandlers.toggle_advanced_filter),
        ("^toggle_mention_filter_", TaskSettingsHandlers.toggle_advanced_filter),
        ("^toggle_forward_filter_", TaskSettingsHandlers.toggle_advanced_filter),
        ("^toggle_keyboard_filter_", TaskSettingsHandlers.toggle_advanced_filter),
        
        # الاستبدال
        ("^replacements_", TaskSettingsHandlers.replacements_menu),
        ("^add_replacement_", TaskSettingsHandlers.add_replacement_start),
        
        # التأخير
        ("^delay_settings_", TaskSettingsHandlers.delay_settings_menu),
        ("^set_delay_", TaskSettingsHandlers.set_delay_start),
        ("^toggle_delay_", TaskSettingsHandlers.toggle_delay),
        ("^quick_delay_", TaskSettingsHandlers.quick_delay_set),
        
        # القوائم البيضاء/السوداء
        ("^user_lists_", TaskSettingsHandlers.user_lists_menu),
        ("^add_whitelist_", TaskSettingsHandlers.add_whitelist_start),
        ("^add_blacklist_", TaskSettingsHandlers.add_blacklist_start),
        
        # الإحصائيات المتقدمة
        ("^task_statistics$", MainHandlers.task_statistics),
        ("^detailed_stats_", MainHandlers.detailed_task_stats),
        
        # Userbot متقدم
        ("^userbot_connect_start$", UserbotHandlers.userbot_connect_start),
        ("^userbot_restart$", UserbotHandlers.restart_userbot),
        ("^userbot_delete$", UserbotHandlers.delete_userbot_confirm),
        ("^confirm_delete_userbot$", UserbotHandlers.delete_userbot_confirmed),
    ]

    for pattern, handler in advanced_handlers:
        app.add_handler(CallbackQueryHandler(handler, pattern=pattern))

    # محادثات الإعدادات المتقدمة
    settings_conversations = [
        # محادثة إضافة كلمة محظورة
        ConversationHandler(
            entry_points=[CallbackQueryHandler(TaskSettingsHandlers.add_blocked_word_start, pattern="^add_blocked_word_")],
            states={
                BLOCKED_WORD_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, TaskSettingsHandlers.blocked_word_received)]
            },
            fallbacks=[CallbackQueryHandler(TaskSettingsHandlers.text_filters_menu, pattern="^text_filters_")],
            per_message=False,
            per_chat=True,
            per_user=True
        ),
        
        # محادثة ربط Userbot
        ConversationHandler(
            entry_points=[CallbackQueryHandler(UserbotHandlers.userbot_connect_start, pattern="^userbot_connect_start$")],
            states={
                USERBOT_API_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, UserbotHandlers.userbot_api_id_received)],
                USERBOT_API_HASH: [MessageHandler(filters.TEXT & ~filters.COMMAND, UserbotHandlers.userbot_api_hash_received)],
                USERBOT_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, UserbotHandlers.userbot_phone_received)],
                USERBOT_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, UserbotHandlers.userbot_code_received)]
            },
            fallbacks=[CallbackQueryHandler(UserbotHandlers.userbot_menu, pattern="^userbot_menu$")],
            per_message=False,
            per_chat=True,
            per_user=True
        ),
    ]

    for conv in settings_conversations:
        app.add_handler(conv)
    
    # Message handler for forwarding
    app.add_handler(
        MessageHandler(filters.ALL & ~filters.COMMAND, MainHandlers.handle_message)
    )
    
    # Error handler
    app.add_error_handler(error_handler)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors"""
    error = context.error
    
    # محاولة معالجة أخطاء تلغرام المعروفة
    if isinstance(error, TelegramError):
        handled = await ErrorHandler.handle_telegram_error(update, context, error)
        if handled:
            return
    
    # تسجيل الخطأ
    await ErrorHandler.log_error(update, context, error, "general_error")
    
    # إرسال رسالة خطأ عامة للمستخدم
    try:
        if update and update.effective_chat:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="❌ حدث خطأ غير متوقع. يرجى المحاولة مرة أخرى."
            )
    except Exception as e:
        logger.error(f"Failed to send error message: {e}")

async def start_bot():
    """Start the bot"""
    global application, message_forwarder, is_running
    
    try:
        # Start application
        await application.start()
        is_running = True
        
        # Start message forwarder
        if message_forwarder:
            await message_forwarder.start_monitoring()
        
        # Choose startup method based on configuration
        if Config.WEBHOOK_URL:
            logger.info("Starting bot with webhook...")
            
            # Set webhook
            await application.bot.set_webhook(
                url=f"{Config.WEBHOOK_URL}/webhook",
                allowed_updates=["message", "callback_query"]
            )
            
            # Start webhook updater
            await application.updater.start_webhook(
                listen="0.0.0.0",
                port=Config.WEBHOOK_PORT,
                url_path="/webhook",
                webhook_url=f"{Config.WEBHOOK_URL}/webhook"
            )
        else:
            logger.info("Starting bot with polling...")
            # Start polling updater
            await application.updater.start_polling(
                allowed_updates=["message", "callback_query"],
                drop_pending_updates=True
            )
        
        logger.info("Bot started successfully")
    
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        raise

async def stop_bot():
    """Stop the bot"""
    global application, message_forwarder, is_running
    
    try:
        is_running = False
        
        # Stop message forwarder
        if message_forwarder:
            try:
                await message_forwarder.stop_monitoring()
                logger.info("Message forwarder stopped")
            except Exception as e:
                logger.error(f"Error stopping message forwarder: {e}")
        
        # Stop updater
        if application and application.updater:
            try:
                await application.updater.stop()
                logger.info("Updater stopped")
            except Exception as e:
                logger.error(f"Error stopping updater: {e}")
        
        # Stop application
        if application:
            try:
                await application.stop()
                logger.info("Application stopped")
            except Exception as e:
                logger.error(f"Error stopping application: {e}")
        
        # Shutdown application
        if application:
            try:
                await application.shutdown()
                logger.info("Application shutdown")
            except Exception as e:
                logger.error(f"Error shutting down application: {e}")
        
        # Close database
        try:
            if hasattr(db, 'pool') and db.pool:
                await db.close()
                logger.info("Database connection closed")
        except Exception as e:
            logger.error(f"Error closing database: {e}")
        
        logger.info("Bot stopped successfully")
    
    except Exception as e:
        logger.error(f"Error during bot shutdown: {e}")

async def main():
    """Main function"""
    try:
        # Initialize bot
        await initialize_bot()
        
        # Start bot
        await start_bot()
        
        # Keep running until interrupted
        while is_running:
            await asyncio.sleep(1)
        
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Stop bot
        await stop_bot()
        logger.info("Bot shutdown complete")

if __name__ == "__main__":
    asyncio.run(main())
