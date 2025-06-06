from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database.user_manager import UserManager
from database.task_manager import TaskManager
from database.statistics_manager import StatisticsManager
from utils.keyboard_builder import KeyboardBuilder
from config import Config

class AdminHandlers:
    @staticmethod
    async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show admin menu"""
        user_id = update.effective_user.id
        
        if not await UserManager.is_admin(user_id) and user_id != Config.ADMIN_USER_ID:
            await update.callback_query.answer("❌ غير مصرح لك بالوصول لهذه الميزة")
            return
        
        keyboard = [
            [
                InlineKeyboardButton("👥 إدارة المستخدمين", callback_data="admin_users"),
                InlineKeyboardButton("📊 إحصائيات عامة", callback_data="admin_stats")
            ],
            [
                InlineKeyboardButton("🔧 إعدادات النظام", callback_data="admin_settings"),
                InlineKeyboardButton("📋 جميع المهام", callback_data="admin_all_tasks")
            ],
            [
                InlineKeyboardButton("🔙 العودة", callback_data="main_menu")
            ]
        ]
        
        text = """
🔧 **لوحة تحكم المدير**

اختر العملية التي تريد تنفيذها:
        """
        
        await update.callback_query.edit_message_text(
            text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown'
        )
    
    @staticmethod
    async def manage_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Manage users"""
        user_id = update.effective_user.id
        
        if not await UserManager.is_admin(user_id) and user_id != Config.ADMIN_USER_ID:
            await update.callback_query.answer("❌ غير مصرح لك بالوصول لهذه الميزة")
            return
        
        users = await UserManager.get_all_users()
        
        if not users:
            text = "📭 لا يوجد مستخدمين مسجلين"
            keyboard = [[InlineKeyboardButton("🔙 العودة", callback_data="admin_menu")]]
        else:
            text = "👥 **قائمة المستخدمين:**\n\n"
            keyboard = []
            
            for user in users[:10]:  # Show first 10 users
                name = user['first_name'] or user['username'] or f"User {user['user_id']}"
                status = "👑 مدير" if user['is_admin'] else "👤 مستخدم"
                active = "🟢" if user['is_active'] else "🔴"
                
                text += f"{active} {name} - {status}\n"
                text += f"   ID: `{user['user_id']}`\n\n"
                
                keyboard.append([
                    InlineKeyboardButton(
                        f"⚙️ {name}", 
                        callback_data=f"admin_user_{user['user_id']}"
                    )
                ])
            
            keyboard.append([InlineKeyboardButton("🔙 العودة", callback_data="admin_menu")])
        
        await update.callback_query.edit_message_text(
            text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown'
        )
    
    @staticmethod
    async def system_statistics(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show system statistics"""
        user_id = update.effective_user.id
        
        if not await UserManager.is_admin(user_id) and user_id != Config.ADMIN_USER_ID:
            await update.callback_query.answer("❌ غير مصرح لك بالوصول لهذه الميزة")
            return
        
        # Get system stats
        users = await UserManager.get_all_users()
        all_tasks = await TaskManager.get_active_tasks()
        
        total_users = len(users)
        active_users = len([u for u in users if u['is_active']])
        admin_users = len([u for u in users if u['is_admin']])
        total_tasks = len(all_tasks)
        
        text = f"""
📊 **إحصائيات النظام**

👥 **المستخدمين:**
• إجمالي المستخدمين: {total_users}
• المستخدمين النشطين: {active_users}
• المديرين: {admin_users}

📋 **المهام:**
• إجمالي المهام النشطة: {total_tasks}

🤖 **النظام:**
• حالة البوت: 🟢 يعمل
• قاعدة البيانات: 🟢 متصلة
        """
        
        keyboard = [[InlineKeyboardButton("🔙 العودة", callback_data="admin_menu")]]
        
        await update.callback_query.edit_message_text(
            text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown'
        )
