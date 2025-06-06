from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from .models import db

class NotificationsManager:
    @staticmethod
    async def create_notification(user_id: int, notification_type: str, title: str, 
                                message: str, data: Dict[str, Any] = None, 
                                priority: int = 1, scheduled_at: datetime = None) -> Optional[int]:
        """إنشاء إشعار جديد"""
        try:
            async with db.pool.acquire() as conn:
                notification_id = await conn.fetchval('''
                    INSERT INTO notifications 
                    (user_id, notification_type, title, message, data, priority, scheduled_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    RETURNING id
                ''', user_id, notification_type, title, message, 
                    data or {}, priority, scheduled_at)
                return notification_id
        except Exception as e:
            print(f"Error creating notification: {e}")
            return None
    
    @staticmethod
    async def get_user_notifications(user_id: int, unread_only: bool = False, 
                                   limit: int = 50) -> List[Dict[str, Any]]:
        """الحصول على إشعارات المستخدم"""
        try:
            async with db.pool.acquire() as conn:
                where_clause = "WHERE user_id = $1"
                if unread_only:
                    where_clause += " AND is_read = FALSE"
                
                rows = await conn.fetch(f'''
                    SELECT * FROM notifications 
                    {where_clause}
                    ORDER BY created_at DESC 
                    LIMIT $2
                ''', user_id, limit)
                return [dict(row) for row in rows]
        except Exception as e:
            print(f"Error getting notifications: {e}")
            return []
    
    @staticmethod
    async def mark_as_read(notification_id: int) -> bool:
        """تمييز الإشعار كمقروء"""
        try:
            async with db.pool.acquire() as conn:
                await conn.execute(
                    'UPDATE notifications SET is_read = TRUE WHERE id = $1',
                    notification_id
                )
                return True
        except Exception as e:
            print(f"Error marking notification as read: {e}")
            return False
    
    @staticmethod
    async def mark_as_sent(notification_id: int) -> bool:
        """تمييز الإشعار كمُرسل"""
        try:
            async with db.pool.acquire() as conn:
                await conn.execute('''
                    UPDATE notifications 
                    SET is_sent = TRUE, sent_at = CURRENT_TIMESTAMP 
                    WHERE id = $1
                ''', notification_id)
                return True
        except Exception as e:
            print(f"Error marking notification as sent: {e}")
            return False
    
    @staticmethod
    async def get_pending_notifications() -> List[Dict[str, Any]]:
        """الحصول على الإشعارات المعلقة للإرسال"""
        try:
            async with db.pool.acquire() as conn:
                rows = await conn.fetch('''
                    SELECT * FROM notifications 
                    WHERE is_sent = FALSE 
                    AND (scheduled_at IS NULL OR scheduled_at <= CURRENT_TIMESTAMP)
                    AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
                    ORDER BY priority DESC, created_at ASC
                    LIMIT 100
                ''')
                return [dict(row) for row in rows]
        except Exception as e:
            print(f"Error getting pending notifications: {e}")
            return []
    
    @staticmethod
    async def cleanup_old_notifications(days: int = 30) -> int:
        """تنظيف الإشعارات القديمة"""
        try:
            async with db.pool.acquire() as conn:
                result = await conn.execute('''
                    DELETE FROM notifications 
                    WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '%s days'
                    AND is_read = TRUE
                ''' % days)
                return int(result.split()[-1]) if result.split() else 0
        except Exception as e:
            print(f"Error cleaning up notifications: {e}")
            return 0
    
    @staticmethod
    async def create_system_notification(title: str, message: str, 
                                       admin_only: bool = False) -> int:
        """إنشاء إشعار نظام لجميع المستخدمين أو المديرين فقط"""
        try:
            from .user_manager import UserManager
            users = await UserManager.get_all_users()
            
            if admin_only:
                users = [user for user in users if user.get('is_admin', False)]
            
            count = 0
            for user in users:
                if user.get('is_active', True):
                    notification_id = await NotificationsManager.create_notification(
                        user_id=user['user_id'],
                        notification_type='system',
                        title=title,
                        message=message,
                        priority=2
                    )
                    if notification_id:
                        count += 1
            
            return count
        except Exception as e:
            print(f"Error creating system notification: {e}")
            return 0
