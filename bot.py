def setup_handlers(app):
    """Setup all bot handlers"""
    
    # Command handlers
    app.add_handler(CommandHandler("start", MainHandlers.start_command))
    app.add_handler(CommandHandler("help", MainHandlers.help_command))
    app.add_handler(CommandHandler("menu", MainHandlers.main_menu))
    app.add_handler(CommandHandler('caps', caps))
    # إزالة التكرار في معالج start
    # app.add_handler(CommandHandler('start', start))
    
    # Create task conversation handler
    create_task_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(TaskHandlers.create_task_start, pattern="^create_task$")],
        states={
            TASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, TaskHandlers.task_name_received)],
            SOURCE_CHAT: [MessageHandler(filters.TEXT & ~filters.COMMAND, TaskHandlers.source_chat_received)],
            TARGET_CHAT: [MessageHandler(filters.TEXT & ~filters.COMMAND, TaskHandlers.target_chat_received)],
            TASK_TYPE: [CallbackQueryHandler(TaskHandlers.task_type_selected, pattern="^task_type_")]
        },
        fallbacks=[
            CallbackQueryHandler(MainHandlers.main_menu, pattern="^main_menu$"),
            CallbackQueryHandler(TaskHandlers.tasks_menu, pattern="^tasks_menu$")
        ],
        conversation_timeout=300,  # 5 minutes timeout
        per_message=False,
        per_chat=True,
        per_user=True
    )
    app.add_handler(create_task_conv)
    
    # Userbot conversation handler - مُحسَّن ومُصحح
    userbot_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(UserbotHandlers.userbot_connect_start, pattern="^userbot_connect_start$")],
        states={
            USERBOT_API_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, UserbotHandlers.userbot_api_id_received)],
            USERBOT_API_HASH: [MessageHandler(filters.TEXT & ~filters.COMMAND, UserbotHandlers.userbot_api_hash_received)],
            USERBOT_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, UserbotHandlers.userbot_phone_received)],
            USERBOT_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, UserbotHandlers.userbot_code_received)],
            USERBOT_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, UserbotHandlers.userbot_password_received)]
        },
        fallbacks=[
            CallbackQueryHandler(UserbotHandlers.conversation_fallback, pattern="^userbot_menu$"),
            CallbackQueryHandler(UserbotHandlers.conversation_fallback, pattern="^main_menu$"),
            CommandHandler("cancel", UserbotHandlers.conversation_fallback),
            MessageHandler(filters.COMMAND, UserbotHandlers.conversation_fallback)
        ],
        conversation_timeout=600,  # 10 minutes timeout
        per_message=False,
        per_chat=True,
        per_user=True,
        name="userbot_connection",
        persistent=False
    )
    app.add_handler(userbot_conv)
    
    # Task settings conversations - مُحسَّنة
    task_settings_conversations = [
        # محادثة إضافة كلمة محظورة
        ConversationHandler(
            entry_points=[CallbackQueryHandler(TaskSettingsHandlers.add_blocked_word_start, pattern="^add_blocked_word_")],
            states={
                BLOCKED_WORD_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, TaskSettingsHandlers.blocked_word_received)]
            },
            fallbacks=[
                CallbackQueryHandler(TaskSettingsHandlers.text_filters_menu, pattern="^text_filters_"),
                CallbackQueryHandler(MainHandlers.main_menu, pattern="^main_menu$")
            ],
            conversation_timeout=300,
            per_message=False,
            per_chat=True,
            per_user=True
        ),
        
        # محادثة إضافة كلمة مطلوبة
        ConversationHandler(
            entry_points=[CallbackQueryHandler(TaskSettingsHandlers.add_required_word_start, pattern="^add_required_word_")],
            states={
                REQUIRED_WORD_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, TaskSettingsHandlers.required_word_received)]
            },
            fallbacks=[
                CallbackQueryHandler(TaskSettingsHandlers.text_filters_menu, pattern="^text_filters_"),
                CallbackQueryHandler(MainHandlers.main_menu, pattern="^main_menu$")
            ],
            conversation_timeout=300,
            per_message=False,
            per_chat=True,
            per_user=True
        ),
        
        # محادثة إضافة استبدال
        ConversationHandler(
            entry_points=[CallbackQueryHandler(TaskSettingsHandlers.add_replacement_start, pattern="^add_replacement_")],
            states={
                REPLACEMENT_OLD_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, TaskSettingsHandlers.replacement_old_text_received)],
                REPLACEMENT_NEW_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, TaskSettingsHandlers.replacement_new_text_received)]
            },
            fallbacks=[
                CallbackQueryHandler(TaskSettingsHandlers.replacements_menu, pattern="^replacements_"),
                CallbackQueryHandler(MainHandlers.main_menu, pattern="^main_menu$")
            ],
            conversation_timeout=300,
            per_message=False,
            per_chat=True,
            per_user=True
        ),
        
        # محادثة تعيين التأخير
        ConversationHandler(
            entry_points=[CallbackQueryHandler(TaskSettingsHandlers.set_delay_start, pattern="^set_delay_")],
            states={
                DELAY_TIME_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, TaskSettingsHandlers.delay_time_received)]
            },
            fallbacks=[
                CallbackQueryHandler(TaskSettingsHandlers.delay_settings_menu, pattern="^delay_settings_"),
                CallbackQueryHandler(MainHandlers.main_menu, pattern="^main_menu$")
            ],
            conversation_timeout=300,
            per_message=False,
            per_chat=True,
            per_user=True
        ),
        
        # محادثة إضافة للقائمة البيضاء
        ConversationHandler(
            entry_points=[CallbackQueryHandler(TaskSettingsHandlers.add_whitelist_start, pattern="^add_whitelist_")],
            states={
                WHITELIST_USER_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, TaskSettingsHandlers.whitelist_user_received)]
            },
            fallbacks=[
                CallbackQueryHandler(TaskSettingsHandlers.user_lists_menu, pattern="^user_lists_"),
                CallbackQueryHandler(MainHandlers.main_menu, pattern="^main_menu$")
            ],
            conversation_timeout=300,
            per_message=False,
            per_chat=True,
            per_user=True
        ),
        
        # محادثة إضافة للقائمة السوداء
        ConversationHandler(
            entry_points=[CallbackQueryHandler(TaskSettingsHandlers.add_blacklist_start, pattern="^add_blacklist_")],
            states={
                BLACKLIST_USER_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, TaskSettingsHandlers.blacklist_user_received)]
            },
            fallbacks=[
                CallbackQueryHandler(TaskSettingsHandlers.user_lists_menu, pattern="^user_lists_"),
                CallbackQueryHandler(MainHandlers.main_menu, pattern="^main_menu$")
            ],
            conversation_timeout=300,
            per_message=False,
            per_chat=True,
            per_user=True
        ),
        
        # محادثة البحث عن مستخدم
        ConversationHandler(
            entry_points=[CallbackQueryHandler(UsersHandlers.search_user, pattern="^search_user$")],
            states={
                SEARCH_USER_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, UsersHandlers.search_user_input)]
            },
            fallbacks=[
                CallbackQueryHandler(MainHandlers.users_menu, pattern="^users_menu$"),
                CallbackQueryHandler(MainHandlers.main_menu, pattern="^main_menu$")
            ],
            conversation_timeout=300,
            per_message=False,
            per_chat=True,
            per_user=True
        ),
    ]

    for conv in task_settings_conversations:
        app.add_handler(conv)
    
    # Callback query handlers - مُنظمة ومُحسَّنة
    callback_handlers = [
        # Main menu
        ("^main_menu$", MainHandlers.main_menu),
        ("^help$", MainHandlers.help_command),
        ("^statistics$", MainHandlers.statistics_menu),
        ("^settings$", MainHandlers.settings_menu),
        ("^users_menu$", MainHandlers.users_menu),
        ("^charts$", ChartsHandlers.charts_menu),
        
        # Tasks
        ("^tasks_menu$", TaskHandlers.tasks_menu),
        ("^view_tasks$", TaskHandlers.view_tasks),
        ("^active_tasks$", TaskHandlers.active_tasks),
        ("^inactive_tasks$", TaskHandlers.inactive_tasks),
        ("^task_settings_", TaskHandlers.task_settings),
        ("^edit_task_", TaskHandlers.edit_task),
        ("^task_stats_", TaskHandlers.task_stats),
        ("^toggle_task_", TaskHandlers.toggle_task),
        ("^delete_task_", TaskHandlers.delete_task_confirm),
        ("^confirm_delete_task_", TaskHandlers.delete_task_confirmed),
        
        # Admin
        ("^admin_menu$", AdminHandlers.admin_menu),
        ("^admin_users$", AdminHandlers.manage_users),
        ("^admin_stats$", AdminHandlers.system_statistics),
        
        # Users Management
        ("^view_all_users$", UsersHandlers.view_all_users),
        ("^manage_user_", UsersHandlers.manage_user),
        ("^manage_admins$", UsersHandlers.manage_admins),
        ("^make_admin_", UsersHandlers.make_admin),
        ("^remove_admin_", UsersHandlers.remove_admin),
        ("^ban_user_", UsersHandlers.ban_user),
        ("^unban_user_", UsersHandlers.unban_user),
        ("^users_statistics$", UsersHandlers.users_statistics),
        
        # Settings
        ("^notification_settings$", SettingsHandlers.notification_settings),
        ("^language_settings$", SettingsHandlers.language_settings),
        ("^security_settings$", SettingsHandlers.security_settings),
        ("^backup_settings$", SettingsHandlers.backup_settings),
        ("^ui_settings$", SettingsHandlers.ui_settings),
        ("^stats_settings$", SettingsHandlers.stats_settings),
        ("^create_backup$", SettingsHandlers.create_backup),
        ("^view_backups$", SettingsHandlers.view_backups),
        
        # Charts
        ("^tasks_chart$", ChartsHandlers.tasks_chart),
        ("^messages_chart$", ChartsHandlers.messages_chart),
        ("^timeline_chart$", ChartsHandlers.timeline_chart),
        ("^comprehensive_chart$", ChartsHandlers.comprehensive_chart),
        
        # Userbot - مُحسَّنة
        ("^userbot_menu$", UserbotHandlers.userbot_menu),
        ("^userbot_connect$", UserbotHandlers.connect_userbot),
        ("^userbot_info$", UserbotHandlers.userbot_info),
        ("^userbot_status$", UserbotHandlers.userbot_status),
        ("^userbot_restart$", UserbotHandlers.restart_userbot),
        ("^userbot_delete$", UserbotHandlers.delete_userbot_confirm),
        ("^confirm_delete_userbot$", UserbotHandlers.delete_userbot_confirmed),
        
        # Task Settings - مُحسَّنة
        ("^media_filters_", TaskSettingsHandlers.media_filters_menu),
        ("^toggle_media_", TaskSettingsHandlers.toggle_media_type),
        ("^toggle_media_filter_", TaskSettingsHandlers.toggle_advanced_filter),
        ("^select_all_media_", TaskSettingsHandlers.select_all_media),
        ("^deselect_all_media_", TaskSettingsHandlers.deselect_all_media),
        
        # Text filters
        ("^text_filters_", TaskSettingsHandlers.text_filters_menu),
        ("^manage_blocked_", TaskSettingsHandlers.manage_blocked_words),
        ("^manage_required_", TaskSettingsHandlers.manage_required_words),
        ("^remove_blocked_", TaskSettingsHandlers.remove_blocked_word),
        ("^remove_required_", TaskSettingsHandlers.remove_required_word),
        
        # Advanced filters
        ("^advanced_filters_", TaskSettingsHandlers.advanced_filters_menu),
        ("^toggle_link_filter_", TaskSettingsHandlers.toggle_advanced_filter),
        ("^toggle_mention_filter_", TaskSettingsHandlers.toggle_advanced_filter),
        ("^toggle_forward_filter_", TaskSettingsHandlers.toggle_advanced_filter),
        ("^toggle_keyboard_filter_", TaskSettingsHandlers.toggle_advanced_filter),
        
        # Replacements
        ("^replacements_", TaskSettingsHandlers.replacements_menu),
        ("^manage_replacements_", TaskSettingsHandlers.manage_replacements),
        ("^remove_replacement_", TaskSettingsHandlers.remove_replacement),
        
        # Delay settings
        ("^delay_settings_", TaskSettingsHandlers.delay_settings_menu),
        ("^toggle_delay_", TaskSettingsHandlers.toggle_delay),
        ("^quick_delay_", TaskSettingsHandlers.quick_delay_set),
        
        # User lists
        ("^user_lists_", TaskSettingsHandlers.user_lists_menu),
        ("^manage_whitelist_", TaskSettingsHandlers.manage_whitelist),
        ("^manage_blacklist_", TaskSettingsHandlers.manage_blacklist),
        ("^remove_whitelist_", TaskSettingsHandlers.remove_whitelist_user),
        ("^remove_blacklist_", TaskSettingsHandlers.remove_blacklist_user),
        
        # Statistics
        ("^task_statistics$", MainHandlers.task_statistics),
        ("^detailed_stats_", MainHandlers.detailed_task_stats),
    ]

    # إضافة معالجات CallbackQuery الفردية
    for pattern, handler in callback_handlers:
        app.add_handler(CallbackQueryHandler(handler, pattern=pattern))
    
    # معالج الملفات للنسخ الاحتياطية
    app.add_handler(MessageHandler(
        filters.Document.FileExtension("json"), 
        SettingsHandlers.restore_backup_file_received
    ))
    
    # Message handler for forwarding - يجب أن يكون آخر معالج للرسائل
    app.add_handler(
        MessageHandler(filters.ALL & ~filters.COMMAND, MainHandlers.handle_message)
    )
    
    # Message handlers - يجب أن يكون قبل معالج التوجيه
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), echo))
    
    # استبدال جميع معالجات CallbackQuery بمعالج واحد - تم تعطيله لتجنب التضارب
    # app.add_handler(CallbackQueryHandler(CallbackRouter.route_callback))
    
    # Error handler
    app.add_error_handler(error_handler)

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
        
        # إغلاق جلسات Userbot
        try:
            for user_id, client in list(UserbotHandlers.clients.items()):
                try:
                    await UserbotHandlers.stop_userbot_client(user_id)
                except Exception as e:
                    logger.error(f"Error stopping userbot client for user {user_id}: {e}")
            logger.info("All userbot clients stopped")
        except Exception as e:
            logger.error(f"Error stopping userbot clients: {e}")
        
        logger.info("Bot stopped successfully")
    
    except Exception as e:
        logger.error(f"Error during bot shutdown: {e}")

async def initialize_bot():
    """Initialize bot and database"""
    global application, message_forwarder
    
    try:
        # Initialize database
        try:
            await db.initialize()
            logger.info("Database initialized")
        except Exception as db_error:
            logger.error(f"Error initializing database: {db_error}")
            raise Exception(f"Failed to initialize database: {db_error}")
        
        # Create application
        if not Config.BOT_TOKEN:
            raise ValueError("BOT_TOKEN is not set in environment variables")
            
        application = Application.builder().token(Config.BOT_TOKEN).build()
        
        # Initialize application
        await application.initialize()
        
        # Initialize message forwarder
        message_forwarder = MessageForwarder(application.bot)
        application.bot_data['message_forwarder'] = message_forwarder
        
        # Setup handlers
        setup_handlers(application)
        
        # تحميل جلسات Userbot النشطة
        try:
            await UserbotHandlers.load_userbot_sessions()
            logger.info("Userbot sessions loaded successfully")
        except Exception as userbot_error:
            logger.warning(f"Error loading userbot sessions: {userbot_error}")
            # لا نرفع استثناء هنا لأن هذا ليس خطأ حرجاً
        
        logger.info("Bot initialized successfully")
        
    except Exception as e:
        logger.error(f"Error initializing bot: {e}")
        raise

async def main():
    """Main function مع الأنظمة المحسنة"""
    try:
        # فحص بسيط للمتطلبات الأساسية
        if not BOT_TOKEN:
            logger.error("BOT_TOKEN غير موجود. يرجى إعداد متغير البيئة BOT_TOKEN.")
            return
        
        # فحص وجود ملفات أساسية
        required_files = [
            "config.py",
            "handlers/main_handlers.py",
            "handlers/task_handlers.py",
            "handlers/userbot_handlers.py",
            "database/models.py"
        ]
        
        missing_files = []
        for file in required_files:
            if not os.path.exists(file):
                missing_files.append(file)
        
        if missing_files:
            logger.error(f"الملفات المطلوبة غير موجودة: {', '.join(missing_files)}")
            return
        
        logger.info("جميع الملفات الأساسية موجودة")
        
        # Initialize bot
        try:
            await initialize_bot()
        except Exception as init_error:
            logger.error(f"فشل في تهيئة البوت: {init_error}")
            return
        
        # بدء أنظمة المراقبة والنسخ الاحتياطي
        try:
            from utils.auto_backup import AutoBackupSystem
            from utils.system_monitor import SystemMonitor
            
            # فحص صحة النظام عند البدء
            is_healthy, health_code, health_message = SystemMonitor.check_system_health()
            if not is_healthy:
                logger.warning(f"System health warning: {health_message}")
            
            # فحص صحة قاعدة البيانات
            db_healthy, db_message = await SystemMonitor.check_database_health()
            if not db_healthy:
                logger.error(f"Database health error: {db_message}")
                raise Exception(f"Database not healthy: {db_message}")
            
            logger.info(f"System health check: {health_message}")
            logger.info(f"Database health check: {db_message}")
            
            # بدء النسخ الاحتياطي التلقائي في الخلفية
            asyncio.create_task(AutoBackupSystem.schedule_auto_backup())
            logger.info("Auto backup system started")
        except ImportError as import_error:
            logger.warning(f"Could not import monitoring modules: {import_error}")
            logger.warning("Monitoring and backup systems will not be available")
        except Exception as monitor_error:
            logger.warning(f"Error starting monitoring systems: {monitor_error}")
            logger.warning("Continuing without monitoring systems")
        
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
        
        # إشعار المديرين بالخطأ الحرج
        try:
            from utils.notification_system import NotificationSystem
            await NotificationSystem.send_admin_notification(
                f"خطأ حرج في البوت: {e}",
                "error",
                urgent=True
            )
        except Exception as notify_error:
            logger.error(f"Failed to send admin notification: {notify_error}")
    finally:
        # Stop bot
        await stop_bot()
        logger.info("Bot shutdown complete")
