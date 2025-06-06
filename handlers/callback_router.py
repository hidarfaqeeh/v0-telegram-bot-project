"""
نظام توجيه المكالمات (Callback Router)
يدير جميع callback_data ويوجهها للمعالجات المناسبة
"""

from telegram import Update
from telegram.ext import ContextTypes
from handlers.main_handlers import MainHandlers
from handlers.task_handlers import TaskHandlers
from handlers.task_settings_handlers import TaskSettingsHandlers
from handlers.userbot_handlers import UserbotHandlers
from handlers.users_handlers import UsersHandlers
from handlers.settings_handlers import SettingsHandlers
from handlers.charts_handlers import ChartsHandlers
from handlers.notifications_handlers import NotificationsHandlers
from utils.error_handler import ErrorHandler

class CallbackRouter:
    """نظام توجيه المكالمات"""
    
    @staticmethod
    async def route_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """توجيه المكالمة للمعالج المناسب"""
        try:
            callback_data = update.callback_query.data
            
            # القائمة الرئيسية
            if callback_data == "main_menu":
                await MainHandlers.main_menu(update, context)
            elif callback_data == "help":
                await MainHandlers.help_menu(update, context)
            elif callback_data == "statistics":
                await MainHandlers.statistics_menu(update, context)
            elif callback_data == "settings":
                await MainHandlers.settings_menu(update, context)
            
            # إدارة المهام
            elif callback_data == "tasks_menu":
                await TaskHandlers.tasks_menu(update, context)
            elif callback_data == "create_task":
                await TaskHandlers.create_task_start(update, context)
            elif callback_data == "view_tasks":
                await TaskHandlers.view_tasks(update, context)
            elif callback_data == "active_tasks":
                await TaskHandlers.active_tasks(update, context)
            elif callback_data == "inactive_tasks":
                await TaskHandlers.inactive_tasks(update, context)
            
            # إعدادات المهام
            elif callback_data.startswith("task_settings_"):
                await TaskHandlers.task_settings(update, context)
            elif callback_data.startswith("edit_task_"):
                await TaskHandlers.edit_task(update, context)
            elif callback_data.startswith("toggle_task_"):
                await TaskHandlers.toggle_task(update, context)
            elif callback_data.startswith("delete_task_"):
                await TaskHandlers.delete_task_confirm(update, context)
            elif callback_data.startswith("confirm_delete_"):
                await TaskHandlers.delete_task_confirmed(update, context)
            elif callback_data.startswith("task_stats_"):
                await TaskHandlers.task_stats(update, context)
            
            # فلاتر الوسائط
            elif callback_data.startswith("media_filters_"):
                await TaskSettingsHandlers.media_filters_menu(update, context)
            elif callback_data.startswith("toggle_media_"):
                await TaskSettingsHandlers.toggle_media_type(update, context)
            elif callback_data.startswith("select_all_media_"):
                await TaskSettingsHandlers.select_all_media(update, context)
            elif callback_data.startswith("deselect_all_media_"):
                await TaskSettingsHandlers.deselect_all_media(update, context)
            elif callback_data.startswith("toggle_") and "_filter_" in callback_data:
                await TaskSettingsHandlers.toggle_advanced_filter(update, context)
            
            # فلاتر النص
            elif callback_data.startswith("text_filters_"):
                await TaskSettingsHandlers.text_filters_menu(update, context)
            elif callback_data.startswith("add_blocked_word_"):
                await TaskSettingsHandlers.add_blocked_word_start(update, context)
            elif callback_data.startswith("add_required_word_"):
                await TaskSettingsHandlers.add_required_word_start(update, context)
            elif callback_data.startswith("manage_blocked_"):
                await TaskSettingsHandlers.manage_blocked_words(update, context)
            elif callback_data.startswith("manage_required_"):
                await TaskSettingsHandlers.manage_required_words(update, context)
            elif callback_data.startswith("remove_blocked_"):
                await TaskSettingsHandlers.remove_blocked_word(update, context)
            elif callback_data.startswith("remove_required_"):
                await TaskSettingsHandlers.remove_required_word(update, context)
            elif callback_data.startswith("clear_blocked_"):
                await TaskSettingsHandlers.clear_blocked_words(update, context)
            elif callback_data.startswith("clear_required_"):
                await TaskSettingsHandlers.clear_required_words(update, context)
            
            # الفلاتر المتقدمة
            elif callback_data.startswith("advanced_filters_"):
                await TaskSettingsHandlers.advanced_filters_menu(update, context)
            
            # الاستبدالات
            elif callback_data.startswith("replacements_"):
                await TaskSettingsHandlers.replacements_menu(update, context)
            elif callback_data.startswith("add_replacement_"):
                await TaskSettingsHandlers.add_replacement_start(update, context)
            elif callback_data.startswith("manage_replacements_"):
                await TaskSettingsHandlers.manage_replacements(update, context)
            elif callback_data.startswith("remove_replacement_"):
                await TaskSettingsHandlers.remove_replacement(update, context)
            elif callback_data.startswith("clear_replacements_"):
                await TaskSettingsHandlers.clear_all_replacements(update, context)
            
            # إعدادات التأخير
            elif callback_data.startswith("delay_settings_"):
                await TaskSettingsHandlers.delay_settings_menu(update, context)
            elif callback_data.startswith("set_delay_"):
                await TaskSettingsHandlers.set_delay_start(update, context)
            elif callback_data.startswith("toggle_delay_"):
                await TaskSettingsHandlers.toggle_delay(update, context)
            elif callback_data.startswith("quick_delay_"):
                await TaskSettingsHandlers.quick_delay_set(update, context)
            
            # قوائم المستخدمين
            elif callback_data.startswith("user_lists_"):
                await TaskSettingsHandlers.user_lists_menu(update, context)
            elif callback_data.startswith("add_whitelist_"):
                await TaskSettingsHandlers.add_whitelist_start(update, context)
            elif callback_data.startswith("add_blacklist_"):
                await TaskSettingsHandlers.add_blacklist_start(update, context)
            elif callback_data.startswith("manage_whitelist_"):
                await TaskSettingsHandlers.manage_whitelist(update, context)
            elif callback_data.startswith("manage_blacklist_"):
                await TaskSettingsHandlers.manage_blacklist(update, context)
            elif callback_data.startswith("remove_whitelist_"):
                await TaskSettingsHandlers.remove_from_whitelist(update, context)
            elif callback_data.startswith("remove_blacklist_"):
                await TaskSettingsHandlers.remove_from_blacklist(update, context)
            elif callback_data.startswith("clear_whitelist_"):
                await TaskSettingsHandlers.clear_whitelist(update, context)
            elif callback_data.startswith("clear_blacklist_"):
                await TaskSettingsHandlers.clear_blacklist(update, context)
            
            # Userbot
            elif callback_data == "userbot_menu":
                await UserbotHandlers.userbot_menu(update, context)
            elif callback_data == "connect_userbot":
                await UserbotHandlers.userbot_connect_start(update, context)
            elif callback_data.startswith("userbot_info_"):
                await UserbotHandlers.userbot_info(update, context)
            elif callback_data.startswith("userbot_status_"):
                await UserbotHandlers.userbot_status(update, context)
            elif callback_data.startswith("restart_userbot_"):
                await UserbotHandlers.restart_userbot(update, context)
            elif callback_data.startswith("delete_userbot_"):
                await UserbotHandlers.delete_userbot_confirm(update, context)
            elif callback_data.startswith("confirm_delete_userbot_"):
                await UserbotHandlers.delete_userbot_confirmed(update, context)
            
            # إدارة المستخدمين
            elif callback_data == "users_menu":
                await UsersHandlers.users_menu(update, context)
            elif callback_data == "view_all_users":
                await UsersHandlers.view_all_users(update, context)
            elif callback_data == "search_user":
                await UsersHandlers.search_user_start(update, context)
            elif callback_data == "manage_admins":
                await UsersHandlers.manage_admins(update, context)
            elif callback_data == "users_statistics":
                await UsersHandlers.users_statistics(update, context)
            elif callback_data.startswith("manage_user_"):
                await UsersHandlers.manage_user(update, context)
            elif callback_data.startswith("make_admin_"):
                await UsersHandlers.make_admin(update, context)
            elif callback_data.startswith("remove_admin_"):
                await UsersHandlers.remove_admin(update, context)
            elif callback_data.startswith("ban_user_"):
                await UsersHandlers.ban_user(update, context)
            elif callback_data.startswith("unban_user_"):
                await UsersHandlers.unban_user(update, context)
            
            # الإعدادات
            elif callback_data == "notification_settings":
                await SettingsHandlers.notification_settings(update, context)
            elif callback_data == "language_settings":
                await SettingsHandlers.language_settings(update, context)
            elif callback_data == "security_settings":
                await SettingsHandlers.security_settings(update, context)
            elif callback_data == "backup_settings":
                await SettingsHandlers.backup_settings(update, context)
            elif callback_data == "ui_settings":
                await SettingsHandlers.ui_settings(update, context)
            elif callback_data == "stats_settings":
                await SettingsHandlers.stats_settings(update, context)
            
            # النسخ الاحتياطي
            elif callback_data == "create_backup":
                await SettingsHandlers.create_backup(update, context)
            elif callback_data == "restore_backup":
                await SettingsHandlers.restore_backup_start(update, context)
            elif callback_data == "view_backups":
                await SettingsHandlers.view_backups(update, context)
            elif callback_data == "schedule_backup":
                await SettingsHandlers.schedule_backup(update, context)
            elif callback_data == "cloud_backup":
                await SettingsHandlers.cloud_backup(update, context)
            elif callback_data == "delete_old_backups":
                await SettingsHandlers.delete_old_backups(update, context)
            
            # الرسوم البيانية
            elif callback_data == "charts_menu":
                await ChartsHandlers.charts_menu(update, context)
            elif callback_data == "tasks_chart":
                await ChartsHandlers.tasks_chart(update, context)
            elif callback_data == "messages_chart":
                await ChartsHandlers.messages_chart(update, context)
            elif callback_data == "timeline_chart":
                await ChartsHandlers.timeline_chart(update, context)
            elif callback_data == "comprehensive_chart":
                await ChartsHandlers.comprehensive_chart(update, context)
            
            # الإشعارات
            elif callback_data.startswith("toggle_") and "_notifications" in callback_data:
                await SettingsHandlers.toggle_setting(update, context)
            elif callback_data.startswith("set_language_"):
                await SettingsHandlers.toggle_setting(update, context)
            
            # معالجة callback غير معروف
            else:
                await update.callback_query.answer("❌ أمر غير معروف")
                await MainHandlers.main_menu(update, context)
                
        except Exception as e:
            await ErrorHandler.log_error(update, context, e, "callback_router")
            await update.callback_query.answer("❌ حدث خطأ")
            await MainHandlers.main_menu(update, context)
