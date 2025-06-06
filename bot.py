#!/usr/bin/env python3
"""
Telegram Forwarder Bot - Main Bot File
نظام بوت تلغرام لإعادة توجيه الرسائل مع لوحة تحكم متقدمة
"""

import asyncio
import logging
import os
import sys
from datetime import datetime
from typing import Dict, Any

from telegram import Update, BotCommand
from telegram.ext import (
    Application, 
    CommandHandler, 
    CallbackQueryHandler, 
    MessageHandler, 
    ConversationHandler,
    filters,
    ContextTypes
)

# استيراد المعالجات
from handlers.main_handlers import MainHandlers
from handlers.task_handlers import TaskHandlers
from handlers.userbot_handlers import UserbotHandlers
from handlers.users_handlers import UsersHandlers
from handlers.settings_handlers import SettingsHandlers
from handlers.charts_handlers import ChartsHandlers
from handlers.task_settings_handlers import TaskSettingsHandlers

# استيراد قواعد البيانات
from database.database_manager import DatabaseManager
from database.task_manager import TaskManager
from database.user_manager import UserManager
from database.settings_manager import SettingsManager
from database.activity_manager import ActivityManager

# استيراد المرافق
from utils.config import Config
from utils.logger import setup_logger
from utils.validators import InputValidator

# إعداد التسجيل
logger = setup_logger(__name__)

# حالات المحادثة - Task Management
TASK_NAME, SOURCE_CHAT, TARGET_CHAT, TASK_SETTINGS = range(4)
EDIT_TASK_NAME, EDIT_SOURCE_CHAT, EDIT_TARGET_CHAT = range(4, 7)

# حالات المحادثة - Userbot
USERBOT_API_ID, USERBOT_API_HASH, USERBOT_PHONE, USERBOT_CODE, USERBOT_PASSWORD = range(7, 12)

# حالات المحادثة - Users Management
ADD_ADMIN_ID, REMOVE_ADMIN_ID, SEARCH_USER_ID, BAN_USER_ID, UNBAN_USER_ID = range(12, 17)

# حالات المحادثة - Settings
SETTING_VALUE_INPUT = 17

class TelegramForwarderBot:
    """الكلاس الرئيسي لبوت إعادة التوجيه"""
    
    def __init__(self):
        """تهيئة البوت"""
        self.config = Config()
        self.application = None
        self.db_manager = None
        self.task_manager = None
        self.user_manager = None
        self.settings_manager = None
        self.activity_manager = None
        
    async def initialize_database(self):
        """تهيئة قاعدة البيانات"""
        try:
            self.db_manager = DatabaseManager()
            await self.db_manager.initialize()
            
            # تهيئة المديرين
            self.task_manager = TaskManager(self.db_manager)
            self.user_manager = UserManager(self.db_manager)
            self.settings_manager = SettingsManager(self.db_manager)
            self.activity_manager = ActivityManager(self.db_manager)
            
            logger.info("✅ تم تهيئة قاعدة البيانات بنجاح")
            
        except Exception as e:
            logger.error(f"❌ خطأ في تهيئة قاعدة البيانات: {e}")
            raise
    
    def setup_conversation_handlers(self) -> list:
        """إعداد معالجات المحادثة"""
        
        # معالج محادثة إنشاء المهام
        task_creation_handler = ConversationHandler(
            entry_points=[
                CallbackQueryHandler(TaskHandlers.create_task_start, pattern="^create_task$")
            ],
            states={
                TASK_NAME: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND, 
                        TaskHandlers.task_name_received
                    )
                ],
                SOURCE_CHAT: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND, 
                        TaskHandlers.source_chat_received
                    )
                ],
                TARGET_CHAT: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND, 
                        TaskHandlers.target_chat_received
                    )
                ],
                TASK_SETTINGS: [
                    CallbackQueryHandler(TaskHandlers.task_settings_received, pattern="^task_setting_")
                ]
            },
            fallbacks=[
                CallbackQueryHandler(MainHandlers.main_menu, pattern="^main_menu$"),
                CommandHandler('cancel', TaskHandlers.cancel_task_creation)
            ],
            name="task_creation",
            persistent=True
        )
        
        # معالج محادثة تعديل المهام
        task_edit_handler = ConversationHandler(
            entry_points=[
                CallbackQueryHandler(TaskHandlers.edit_task_start, pattern="^edit_task_")
            ],
            states={
                EDIT_TASK_NAME: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND, 
                        TaskHandlers.edit_task_name_received
                    )
                ],
                EDIT_SOURCE_CHAT: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND, 
                        TaskHandlers.edit_source_chat_received
                    )
                ],
                EDIT_TARGET_CHAT: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND, 
                        TaskHandlers.edit_target_chat_received
                    )
                ]
            },
            fallbacks=[
                CallbackQueryHandler(TaskHandlers.tasks_menu, pattern="^tasks_menu$"),
                CommandHandler('cancel', TaskHandlers.cancel_task_edit)
            ],
            name="task_edit",
            persistent=True
        )
        
        # معالج محادثة Userbot
        userbot_handler = ConversationHandler(
            entry_points=[
                CallbackQueryHandler(UserbotHandlers.userbot_connect_start, pattern="^userbot_connect_start$")
            ],
            states={
                USERBOT_API_ID: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND, 
                        UserbotHandlers.userbot_api_id_received
                    )
                ],
                USERBOT_API_HASH: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND, 
                        UserbotHandlers.userbot_api_hash_received
                    )
                ],
                USERBOT_PHONE: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND, 
                        UserbotHandlers.userbot_phone_received
                    )
                ],
                USERBOT_CODE: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND, 
                        UserbotHandlers.userbot_code_received
                    )
                ],
                USERBOT_PASSWORD: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND, 
                        UserbotHandlers.userbot_password_received
                    )
                ]
            },
            fallbacks=[
                CallbackQueryHandler(UserbotHandlers.userbot_menu, pattern="^userbot_menu$"),
                CommandHandler('cancel', UserbotHandlers.cancel_userbot_setup)
            ],
            name="userbot_setup",
            persistent=True
        )
        
        # معالج محادثة إدارة المستخدمين
        users_management_handler = ConversationHandler(
            entry_points=[
                CallbackQueryHandler(UsersHandlers.add_admin_start, pattern="^add_admin$"),
                CallbackQueryHandler(UsersHandlers.remove_admin_start, pattern="^remove_admin$"),
                CallbackQueryHandler(UsersHandlers.search_user_start, pattern="^search_user$"),
                CallbackQueryHandler(UsersHandlers.ban_user_start, pattern="^ban_user$"),
                CallbackQueryHandler(UsersHandlers.unban_user_start, pattern="^unban_user$")
            ],
            states={
                ADD_ADMIN_ID: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND, 
                        UsersHandlers.add_admin_id_received
                    )
                ],
                REMOVE_ADMIN_ID: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND, 
                        UsersHandlers.remove_admin_id_received
                    )
                ],
                SEARCH_USER_ID: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND, 
                        UsersHandlers.search_user_id_received
                    )
                ],
                BAN_USER_ID: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND, 
                        UsersHandlers.ban_user_id_received
                    )
                ],
                UNBAN_USER_ID: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND, 
                        UsersHandlers.unban_user_id_received
                    )
                ]
            },
            fallbacks=[
                CallbackQueryHandler(UsersHandlers.users_menu, pattern="^users_menu$"),
                CommandHandler('cancel', UsersHandlers.cancel_user_management)
            ],
            name="users_management",
            persistent=True
        )
        
        # معالج محادثة الإعدادات
        settings_handler = ConversationHandler(
            entry_points=[
                CallbackQueryHandler(SettingsHandlers.setting_input_start, pattern="^setting_input_")
            ],
            states={
                SETTING_VALUE_INPUT: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND, 
                        SettingsHandlers.setting_value_received
                    )
                ]
            },
            fallbacks=[
                CallbackQueryHandler(SettingsHandlers.settings_menu, pattern="^settings_menu$"),
                CommandHandler('cancel', SettingsHandlers.cancel_setting_input)
            ],
            name="settings_input",
            persistent=True
        )
        
        return [
            task_creation_handler,
            task_edit_handler,
            userbot_handler,
            users_management_handler,
            settings_handler
        ]
    
    def setup_handlers(self):
        """إعداد معالجات البوت"""
        
        # الأوامر الأساسية
        self.application.add_handler(CommandHandler("start", MainHandlers.start))
        self.application.add_handler(CommandHandler("help", MainHandlers.help_command))
        self.application.add_handler(CommandHandler("status", MainHandlers.status))
        self.application.add_handler(CommandHandler("admin", MainHandlers.admin_panel))
        
        # معالجات المحادثة
        conversation_handlers = self.setup_conversation_handlers()
        for handler in conversation_handlers:
            self.application.add_handler(handler)
        
        # معالجات الأزرار الرئيسية
        self.application.add_handler(CallbackQueryHandler(MainHandlers.main_menu, pattern="^main_menu$"))
        self.application.add_handler(CallbackQueryHandler(MainHandlers.admin_panel, pattern="^admin_panel$"))
        
        # معالجات المهام
        self.application.add_handler(CallbackQueryHandler(TaskHandlers.tasks_menu, pattern="^tasks_menu$"))
        self.application.add_handler(CallbackQueryHandler(TaskHandlers.view_tasks, pattern="^view_tasks$"))
        self.application.add_handler(CallbackQueryHandler(TaskHandlers.task_details, pattern="^task_details_"))
        self.application.add_handler(CallbackQueryHandler(TaskHandlers.toggle_task, pattern="^toggle_task_"))
        self.application.add_handler(CallbackQueryHandler(TaskHandlers.delete_task, pattern="^delete_task_"))
        self.application.add_handler(CallbackQueryHandler(TaskHandlers.confirm_delete_task, pattern="^confirm_delete_task_"))
        
        # معالجات إعدادات المهام
        self.application.add_handler(CallbackQueryHandler(TaskSettingsHandlers.task_settings_menu, pattern="^task_settings_"))
        self.application.add_handler(CallbackQueryHandler(TaskSettingsHandlers.media_filters_menu, pattern="^media_filters_"))
        self.application.add_handler(CallbackQueryHandler(TaskSettingsHandlers.toggle_media_filter, pattern="^toggle_media_"))
        self.application.add_handler(CallbackQueryHandler(TaskSettingsHandlers.text_filters_menu, pattern="^text_filters_"))
        self.application.add_handler(CallbackQueryHandler(TaskSettingsHandlers.add_keyword_filter, pattern="^add_keyword_"))
        self.application.add_handler(CallbackQueryHandler(TaskSettingsHandlers.remove_keyword_filter, pattern="^remove_keyword_"))
        self.application.add_handler(CallbackQueryHandler(TaskSettingsHandlers.time_filters_menu, pattern="^time_filters_"))
        self.application.add_handler(CallbackQueryHandler(TaskSettingsHandlers.set_time_filter, pattern="^set_time_"))
        
        # معالجات Userbot
        self.application.add_handler(CallbackQueryHandler(UserbotHandlers.userbot_menu, pattern="^userbot_menu$"))
        self.application.add_handler(CallbackQueryHandler(UserbotHandlers.userbot_status, pattern="^userbot_status$"))
        self.application.add_handler(CallbackQueryHandler(UserbotHandlers.userbot_disconnect, pattern="^userbot_disconnect$"))
        self.application.add_handler(CallbackQueryHandler(UserbotHandlers.confirm_userbot_disconnect, pattern="^confirm_userbot_disconnect$"))
        
        # معالجات المستخدمين
        self.application.add_handler(CallbackQueryHandler(UsersHandlers.users_menu, pattern="^users_menu$"))
        self.application.add_handler(CallbackQueryHandler(UsersHandlers.view_users, pattern="^view_users$"))
        self.application.add_handler(CallbackQueryHandler(UsersHandlers.view_admins, pattern="^view_admins$"))
        self.application.add_handler(CallbackQueryHandler(UsersHandlers.view_banned_users, pattern="^view_banned_users$"))
        self.application.add_handler(CallbackQueryHandler(UsersHandlers.user_details, pattern="^user_details_"))
        
        # معالجات الإعدادات
        self.application.add_handler(CallbackQueryHandler(SettingsHandlers.settings_menu, pattern="^settings_menu$"))
        self.application.add_handler(CallbackQueryHandler(SettingsHandlers.general_settings, pattern="^general_settings$"))
        self.application.add_handler(CallbackQueryHandler(SettingsHandlers.notification_settings, pattern="^notification_settings$"))
        self.application.add_handler(CallbackQueryHandler(SettingsHandlers.security_settings, pattern="^security_settings$"))
        self.application.add_handler(CallbackQueryHandler(SettingsHandlers.toggle_setting, pattern="^toggle_setting_"))
        
        # معالجات الرسوم البيانية
        self.application.add_handler(CallbackQueryHandler(ChartsHandlers.charts_menu, pattern="^charts_menu$"))
        self.application.add_handler(CallbackQueryHandler(ChartsHandlers.tasks_chart, pattern="^tasks_chart$"))
        self.application.add_handler(CallbackQueryHandler(ChartsHandlers.users_chart, pattern="^users_chart$"))
        self.application.add_handler(CallbackQueryHandler(ChartsHandlers.activity_chart, pattern="^activity_chart$"))
        self.application.add_handler(CallbackQueryHandler(ChartsHandlers.performance_chart, pattern="^performance_chart$"))
        
        # معالج الرسائل العامة (يجب أن يكون الأخير)
        self.application.add_handler(MessageHandler(filters.ALL, MainHandlers.handle_message))
        
        logger.info("✅ تم إعداد جميع معالجات البوت")
    
    async def setup_bot_commands(self):
        """إعداد أوامر البوت"""
        commands = [
            BotCommand("start", "بدء استخدام البوت"),
            BotCommand("help", "عرض المساعدة"),
            BotCommand("status", "حالة البوت"),
            BotCommand("admin", "لوحة الإدارة"),
        ]
        
        await self.application.bot.set_my_commands(commands)
        logger.info("✅ تم إعداد أوامر البوت")
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالج الأخطاء العام"""
        logger.error(f"❌ خطأ في البوت: {context.error}")
        
        if update and update.effective_user:
            try:
                await context.bot.send_message(
                    chat_id=update.effective_user.id,
                    text="❌ حدث خطأ غير متوقع. يرجى المحاولة مرة أخرى."
                )
            except Exception as e:
                logger.error(f"❌ خطأ في إرسال رسالة الخطأ: {e}")
    
    async def post_init(self, application: Application):
        """إعدادات ما بعد التهيئة"""
        await self.initialize_database()
        await self.setup_bot_commands()
        
        # تمرير المديرين للمعالجات
        MainHandlers.set_managers(
            self.db_manager, self.task_manager, self.user_manager, 
            self.settings_manager, self.activity_manager
        )
        TaskHandlers.set_managers(
            self.db_manager, self.task_manager, self.user_manager, 
            self.settings_manager, self.activity_manager
        )
        UserbotHandlers.set_managers(
            self.db_manager, self.task_manager, self.user_manager, 
            self.settings_manager, self.activity_manager
        )
        UsersHandlers.set_managers(
            self.db_manager, self.task_manager, self.user_manager, 
            self.settings_manager, self.activity_manager
        )
        SettingsHandlers.set_managers(
            self.db_manager, self.task_manager, self.user_manager, 
            self.settings_manager, self.activity_manager
        )
        ChartsHandlers.set_managers(
            self.db_manager, self.task_manager, self.user_manager, 
            self.settings_manager, self.activity_manager
        )
        TaskSettingsHandlers.set_managers(
            self.db_manager, self.task_manager, self.user_manager, 
            self.settings_manager, self.activity_manager
        )
        
        logger.info("✅ تم إعداد البوت بالكامل")
    
    async def run(self):
        """تشغيل البوت"""
        try:
            # إنشاء التطبيق
            self.application = (
                Application.builder()
                .token(self.config.BOT_TOKEN)
                .post_init(self.post_init)
                .build()
            )
            
            # إعداد المعالجات
            self.setup_handlers()
            
            # إعداد معالج الأخطاء
            self.application.add_error_handler(self.error_handler)
            
            logger.info("🚀 بدء تشغيل البوت...")
            
            # تشغيل البوت
            await self.application.run_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True
            )
            
        except Exception as e:
            logger.error(f"❌ خطأ في تشغيل البوت: {e}")
            raise

async def main():
    """الدالة الرئيسية"""
    try:
        bot = TelegramForwarderBot()
        await bot.run()
    except KeyboardInterrupt:
        logger.info("🛑 تم إيقاف البوت بواسطة المستخدم")
    except Exception as e:
        logger.error(f"❌ خطأ في البوت: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
