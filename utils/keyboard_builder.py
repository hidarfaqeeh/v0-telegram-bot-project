from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from typing import List, Dict, Any

class KeyboardBuilder:
    @staticmethod
    def main_menu() -> InlineKeyboardMarkup:
        """Build main menu keyboard"""
        keyboard = [
            [
                InlineKeyboardButton("📋 إدارة المهام", callback_data="tasks_menu"),
                InlineKeyboardButton("📊 الإحصائيات", callback_data="statistics")
            ],
            [
                InlineKeyboardButton("⚙️ الإعدادات", callback_data="settings"),
                InlineKeyboardButton("👥 إدارة المستخدمين", callback_data="users_menu")
            ],
            [
                InlineKeyboardButton("🤖 Userbot", callback_data="userbot_menu"),
                InlineKeyboardButton("ℹ️ المساعدة", callback_data="help")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def tasks_menu() -> InlineKeyboardMarkup:
        """Build tasks menu keyboard"""
        keyboard = [
            [
                InlineKeyboardButton("➕ إنشاء مهمة جديدة", callback_data="create_task"),
                InlineKeyboardButton("📋 عرض المهام", callback_data="view_tasks")
            ],
            [
                InlineKeyboardButton("⚡ المهام النشطة", callback_data="active_tasks"),
                InlineKeyboardButton("⏸️ المهام المتوقفة", callback_data="inactive_tasks")
            ],
            [
                InlineKeyboardButton("🔙 العودة", callback_data="main_menu")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def task_settings_menu(task_id: int) -> InlineKeyboardMarkup:
        """Build task settings menu"""
        keyboard = [
            [
                InlineKeyboardButton("📝 تعديل الإعدادات", callback_data=f"edit_task_{task_id}"),
                InlineKeyboardButton("🔄 تبديل الحالة", callback_data=f"toggle_task_{task_id}")
            ],
            [
                InlineKeyboardButton("🎯 فلاتر الوسائط", callback_data=f"media_filters_{task_id}"),
                InlineKeyboardButton("🔍 فلاتر النص", callback_data=f"text_filters_{task_id}")
            ],
            [
                InlineKeyboardButton("⚡ فلاتر متقدمة", callback_data=f"advanced_filters_{task_id}"),
                InlineKeyboardButton("👥 القوائم البيضاء/السوداء", callback_data=f"user_lists_{task_id}")
            ],
            [
                InlineKeyboardButton("🔄 الاستبدال", callback_data=f"replacements_{task_id}"),
                InlineKeyboardButton("⏰ التأخير", callback_data=f"delay_settings_{task_id}")
            ],
            [
                InlineKeyboardButton("📊 الإحصائيات", callback_data=f"task_stats_{task_id}"),
                InlineKeyboardButton("🗑️ حذف المهمة", callback_data=f"delete_task_{task_id}")
            ],
            [
                InlineKeyboardButton("🔙 العودة", callback_data="tasks_menu")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def confirmation_keyboard(action: str, item_id: int) -> InlineKeyboardMarkup:
        """Build confirmation keyboard"""
        keyboard = [
            [
                InlineKeyboardButton("✅ نعم", callback_data=f"confirm_{action}_{item_id}"),
                InlineKeyboardButton("❌ لا", callback_data=f"cancel_{action}_{item_id}")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def back_keyboard(callback_data: str) -> InlineKeyboardMarkup:
        """Build simple back keyboard"""
        keyboard = [
            [InlineKeyboardButton("🔙 العودة", callback_data=callback_data)]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def pagination_keyboard(current_page: int, total_pages: int, 
                          callback_prefix: str) -> InlineKeyboardMarkup:
        """Build pagination keyboard"""
        keyboard = []
        
        # Navigation buttons
        nav_buttons = []
        if current_page > 1:
            nav_buttons.append(
                InlineKeyboardButton("⬅️", callback_data=f"{callback_prefix}_{current_page-1}")
            )
        
        nav_buttons.append(
            InlineKeyboardButton(f"{current_page}/{total_pages}", callback_data="noop")
        )
        
        if current_page < total_pages:
            nav_buttons.append(
                InlineKeyboardButton("➡️", callback_data=f"{callback_prefix}_{current_page+1}")
            )
        
        keyboard.append(nav_buttons)
        
        return InlineKeyboardMarkup(keyboard)
