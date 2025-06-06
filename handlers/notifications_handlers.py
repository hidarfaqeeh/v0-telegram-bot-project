from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database.user_manager import UserManager
from database.task_manager import TaskManager
from utils.error_handler import ErrorHandler
from config import Config
import asyncio
from datetime import datetime, timedelta

class NotificationsHandlers:
    @staticmethod
    async def send_system_notification(bot, message: str, admin_only: bool = False):
        """إرسال إشعار نظام لجميع المستخدمين أو المديرين فقط"""
        try:
            users = await UserManager.get_all_users()
            
            if admin_only:
                users = [user for user in users if user['is_admin']]
            
            for user in users:
                if user['is_active']:
                    try:
                        await bot.send_message(
                            chat_id=user['user_id'],
                            text=f"🔔 **إشعار النظام**\n\n{message}",
                            parse_mode='Markdown'
                        )
                        await asyncio.sleep(0.1)  # تجنب حدود الإرسال
                    except Exception as e:
                        print(f"Failed to send notification to {user['user_id']}: {e}")
                        
        except Exception as e:
            print(f"Error sending system notification: {e}")
    
    @staticmethod
    async def send_task_notification(bot, user_id: int, task_name: str, 
                                   notification_type: str, details: str = ""):
        """إرسال إشعار خاص بمهمة"""
        try:
            icons = {
                'started': '▶️',
                'stopped': '⏸️',
                'error': '❌',
                'success': '✅',
                'warning': '⚠️'
            }
            
            icon = icons.get(notification_type, '🔔')
            
            message = f"""
{icon} **إشعار المهمة**

📝 **المهمة:** {task_name}
📊 **الحالة:** {notification_type}
{f"📋 **التفاصيل:** {details}" if details else ""}

⏰ **الوقت:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """
            
            await bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            print(f"Error sending task notification: {e}")
    
    @staticmethod
    async def send_daily_report(bot):
        """إرسال التقرير اليومي للمديرين"""
        try:
            # الحصول على المديرين
            users = await UserManager.get_all_users()
            admins = [user for user in users if user['is_admin'] and user['is_active']]
            
            # إنشاء التقرير اليومي
            today = datetime.now().date()
            
            # إحصائيات عامة
            total_users = len(users)
            active_users = len([u for u in users if u['is_active']])
            new_users_today = len([u for u in users if u['created_at'].date() == today])
            
            # إحصائيات المهام
            all_tasks = await TaskManager.get_active_tasks()
            total_tasks = len(all_tasks)
            
            # إحصائيات الرسائل (تقديرية)
            total_forwarded_today = 0
            total_filtered_today = 0
            
            for task in all_tasks:
                from database.statistics_manager import StatisticsManager
                stats = await StatisticsManager.get_task_stats(task['id'], days=1)
                for stat in stats:
                    if stat['date'] == today:
                        total_forwarded_today += stat['messages_forwarded']
                        total_filtered_today += stat['messages_filtered']
            
            report = f"""
📊 **التقرير اليومي - {today.strftime('%Y-%m-%d')}**

👥 **المستخدمين:**
• إجمالي المستخدمين: {total_users:,}
• المستخدمين النشطين: {active_users:,}
• مستخدمين جدد اليوم: {new_users_today:,}

📋 **المهام:**
• إجمالي المهام النشطة: {total_tasks:,}

📤 **الرسائل اليوم:**
• رسائل موجهة: {total_forwarded_today:,}
• رسائل مرشحة: {total_filtered_today:,}
• إجمالي الرسائل: {total_forwarded_today + total_filtered_today:,}

📈 **الأداء:**
• معدل النجاح: {(total_forwarded_today/(total_forwarded_today + total_filtered_today)*100):.1f}% إذا كان هناك رسائل
            """
            
            # إرسال التقرير للمديرين
            for admin in admins:
                try:
                    await bot.send_message(
                        chat_id=admin['user_id'],
                        text=report,
                        parse_mode='Markdown'
                    )
                except Exception as e:
                    print(f"Failed to send daily report to admin {admin['user_id']}: {e}")
                    
        except Exception as e:
            print(f"Error sending daily report: {e}")
    
    @staticmethod
    async def send_error_notification(bot, error_details: dict):
        """إرسال إشعار خطأ للمديرين"""
        try:
            # الحصول على المديرين
            users = await UserManager.get_all_users()
            admins = [user for user in users if user['is_admin'] and user['is_active']]
            
            message = f"""
❌ **إشعار خطأ**

🔍 **العملية:** {error_details.get('operation', 'غير محدد')}
👤 **المستخدم:** {error_details.get('user_id', 'غير محدد')}
📝 **الخطأ:** {error_details.get('error', 'غير محدد')}
⏰ **الوقت:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

يرجى مراجعة السجلات للمزيد من التفاصيل.
            """
            
            for admin in admins:
                try:
                    await bot.send_message(
                        chat_id=admin['user_id'],
                        text=message,
                        parse_mode='Markdown'
                    )
                except Exception as e:
                    print(f"Failed to send error notification to admin {admin['user_id']}: {e}")
                    
        except Exception as e:
            print(f"Error sending error notification: {e}")
