"""
معالجات المحادثات (Conversation Handlers)
تدير جميع المحادثات التفاعلية مع المستخدمين
"""

from telegram.ext import ConversationHandler, MessageHandler, filters, CommandHandler, CallbackQueryHandler
from handlers.task_handlers import TaskHandlers
from handlers.task_settings_handlers import TaskSettingsHandlers
from handlers.userbot_handlers import UserbotHandlers
from handlers.users_handlers import UsersHandlers

# حالات المحادثة
(TASK_NAME, SOURCE_CHAT, TARGET_CHAT, TASK_SETTINGS,
 BLOCKED_WORD_INPUT, REQUIRED_WORD_INPUT, REPLACEMENT_OLD_TEXT, REPLACEMENT_NEW_TEXT,
 DELAY_TIME_INPUT, WHITELIST_USER_INPUT, BLACKLIST_USER_INPUT,
 USERBOT_API_ID, USERBOT_API_HASH, USERBOT_PHONE,
 USER_SEARCH_INPUT) = range(15)

class ConversationHandlers:
    """معالجات المحادثات"""
    
    @staticmethod
    def get_create_task_conversation():
        """محادثة إنشاء مهمة جديدة"""
        return ConversationHandler(
            entry_points=[CallbackQueryHandler(TaskHandlers.create_task_start, pattern="^create_task$")],
            states={
                TASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, TaskHandlers.task_name_received)],
                SOURCE_CHAT: [MessageHandler(filters.TEXT & ~filters.COMMAND, TaskHandlers.source_chat_received)],
                TARGET_CHAT: [MessageHandler(filters.TEXT & ~filters.COMMAND, TaskHandlers.target_chat_received)],
                TASK_SETTINGS: [MessageHandler(filters.TEXT & ~filters.COMMAND, TaskHandlers.task_settings_received)]
            },
            fallbacks=[
                CommandHandler("cancel", TaskHandlers.cancel_task_creation),
                CallbackQueryHandler(TaskHandlers.cancel_task_creation, pattern="^cancel_task$")
            ],
            map_to_parent={
                ConversationHandler.END: ConversationHandler.END
            }
        )
    
    @staticmethod
    def get_text_filters_conversation():
        """محادثة إدارة فلاتر النص"""
        return ConversationHandler(
            entry_points=[
                CallbackQueryHandler(TaskSettingsHandlers.add_blocked_word_start, pattern="^add_blocked_word_"),
                CallbackQueryHandler(TaskSettingsHandlers.add_required_word_start, pattern="^add_required_word_")
            ],
            states={
                BLOCKED_WORD_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, TaskSettingsHandlers.blocked_word_received)],
                REQUIRED_WORD_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, TaskSettingsHandlers.required_word_received)]
            },
            fallbacks=[
                CommandHandler("cancel", TaskSettingsHandlers.cancel_word_input),
                CallbackQueryHandler(TaskSettingsHandlers.cancel_word_input, pattern="^text_filters_")
            ],
            map_to_parent={
                ConversationHandler.END: ConversationHandler.END
            }
        )
    
    @staticmethod
    def get_replacements_conversation():
        """محادثة إدارة الاستبدالات"""
        return ConversationHandler(
            entry_points=[CallbackQueryHandler(TaskSettingsHandlers.add_replacement_start, pattern="^add_replacement_")],
            states={
                REPLACEMENT_OLD_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, TaskSettingsHandlers.replacement_old_text_received)],
                REPLACEMENT_NEW_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, TaskSettingsHandlers.replacement_new_text_received)]
            },
            fallbacks=[
                CommandHandler("cancel", TaskSettingsHandlers.cancel_replacement_input),
                CallbackQueryHandler(TaskSettingsHandlers.cancel_replacement_input, pattern="^replacements_")
            ],
            map_to_parent={
                ConversationHandler.END: ConversationHandler.END
            }
        )
    
    @staticmethod
    def get_delay_settings_conversation():
        """محادثة إعدادات التأخير"""
        return ConversationHandler(
            entry_points=[CallbackQueryHandler(TaskSettingsHandlers.set_delay_start, pattern="^set_delay_")],
            states={
                DELAY_TIME_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, TaskSettingsHandlers.delay_time_received)]
            },
            fallbacks=[
                CommandHandler("cancel", TaskSettingsHandlers.cancel_delay_input),
                CallbackQueryHandler(TaskSettingsHandlers.cancel_delay_input, pattern="^delay_settings_")
            ],
            map_to_parent={
                ConversationHandler.END: ConversationHandler.END
            }
        )
    
    @staticmethod
    def get_user_lists_conversation():
        """محادثة إدارة قوائم المستخدمين"""
        return ConversationHandler(
            entry_points=[
                CallbackQueryHandler(TaskSettingsHandlers.add_whitelist_start, pattern="
