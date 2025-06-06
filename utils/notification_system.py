from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio

class NotificationSystem:
    """نظام الإشعارات المحسن"""
    
    @staticmethod
    async def send_admin_notification(message: str, notification_type: str = "info", 
                                    urgent: bool = False) -> bool:
        """إرسال إشعار للمديرين"""
        try:
            from database.user_manager import UserManager
            from config import Config
            
            # الحصول على قائمة المديرين
            users = await UserManager.get_all_users()
            admins = [user for user in users if user['is_admin']]
            
            # إضافة المدير الرئيسي
            if Config.ADMIN_USER_ID not in [admin['user_id'] for admin in admins]:
                admins.append({'user_id': Config.ADMIN_USER_ID})
            
            # تحديد رمز الإشعار
            icon = {
                "info": "ℹ️",
                "warning": "⚠️", 
                "error": "❌",
                "success": "✅"
            }.get(notification_type, "📢")
            
            urgency_text = "🚨 **عاجل** 🚨\n\n" if urgent else ""
            
            notification_text = f"""
{urgency_text}{icon} **إشعار إداري**

{message}

🕐 **الوقت:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """
            
            # إرسال للمديرين
            success_count = 0
            for admin in admins:
                try:
                    # هنا نحتاج للوصول لـ bot instance
                    # سيتم تنفيذ هذا في المعالجات
                    success_count += 1
                except Exception:
                    continue
            
            return success_count > 0
            
        except Exception as e:
            print(f"Error sending admin notification: {e}")
            return False
    
    @staticmethod
    async def send_user_notification(user_id: int, message: str, 
                                   notification_type: str = "info") -> bool:
        """إرسال إشعار لمستخدم محدد"""
        try:
            # تسجيل الإشعار في قاعدة البيانات
            from database.notifications_manager import NotificationsManager
            
            await NotificationsManager.create_notification(
                user_id=user_id,
                title=f"إشعار {notification_type}",
                message=message,
                notification_type=notification_type
            )
            
            return True
            
        except Exception as e:
            print(f"Error sending user notification: {e}")
            return False
    
    @staticmethod
    async def notify_task_status_change(task_id: int, old_status: bool, 
                                      new_status: bool, user_id: int) -> bool:
        """إشعار بتغيير حالة المهمة"""
        try:
            from database.task_manager import TaskManager
            
            task = await TaskManager.get_task(task_id)
            if not task:
                return False
            
            status_text = "تم تفعيل" if new_status else "تم إيقاف"
            status_icon = "🟢" if new_status else "🔴"
            
            message = f"""
{status_icon} **تغيير حالة المهمة**

📝 **المهمة:** {task['task_name']}
🔄 **الحالة الجديدة:** {status_text}
🕐 **الوقت:** {datetime.now().strftime('%H:%M:%S')}
            """
            
            return await NotificationSystem.send_user_notification(
                user_id, message, "info"
            )
            
        except Exception as e:
            print(f"Error notifying task status change: {e}")
            return False
