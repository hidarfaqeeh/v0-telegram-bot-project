from typing import Dict, Any, Optional, List
from datetime import datetime
from .models import db

class ActivityManager:
    @staticmethod
    async def log_activity(user_id: int, activity_type: str, activity_category: str,
                          description: str = None, target_type: str = None, 
                          target_id: int = None, old_values: Dict[str, Any] = None,
                          new_values: Dict[str, Any] = None, session_id: int = None,
                          ip_address: str = None, user_agent: str = None,
                          success: bool = True, error_message: str = None,
                          processing_time_ms: int = None) -> Optional[int]:
        """تسجيل نشاط جديد"""
        try:
            async with db.pool.acquire() as conn:
                activity_id = await conn.fetchval('''
                    INSERT INTO activity_logs 
                    (user_id, session_id, activity_type, activity_category, description,
                     target_type, target_id, old_values, new_values, ip_address, 
                     user_agent, success, error_message, processing_time_ms)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
                    RETURNING id
                ''', user_id, session_id, activity_type, activity_category, description,
                    target_type, target_id, old_values, new_values, ip_address,
                    user_agent, success, error_message, processing_time_ms)
                return activity_id
        except Exception as e:
            print(f"Error logging activity: {e}")
            return None
    
    @staticmethod
    async def get_user_activities(user_id: int, limit: int = 100, 
                                activity_type: str = None) -> List[Dict[str, Any]]:
        """الحصول على أنشطة المستخدم"""
        try:
            async with db.pool.acquire() as conn:
                where_clause = "WHERE user_id = $1"
                params = [user_id]
                
                if activity_type:
                    where_clause += " AND activity_type = $2"
                    params.append(activity_type)
                    params.append(limit)
                else:
                    params.append(limit)
                
                rows = await conn.fetch(f'''
                    SELECT * FROM activity_logs 
                    {where_clause}
                    ORDER BY created_at DESC 
                    LIMIT ${len(params)}
                ''', *params)
                return [dict(row) for row in rows]
        except Exception as e:
            print(f"Error getting activities: {e}")
            return []
    
    @staticmethod
    async def get_system_activities(limit: int = 100, 
                                  activity_category: str = None) -> List[Dict[str, Any]]:
        """الحصول على أنشطة النظام"""
        try:
            async with db.pool.acquire() as conn:
                where_clause = ""
                params = []
                
                if activity_category:
                    where_clause = "WHERE activity_category = $1"
                    params.append(activity_category)
                    params.append(limit)
                else:
                    params.append(limit)
                
                rows = await conn.fetch(f'''
                    SELECT * FROM activity_logs 
                    {where_clause}
                    ORDER BY created_at DESC 
                    LIMIT ${len(params)}
                ''', *params)
                return [dict(row) for row in rows]
        except Exception as e:
            print(f"Error getting system activities: {e}")
            return []
    
    @staticmethod
    async def cleanup_old_activities(days: int = 90) -> int:
        """تنظيف الأنشطة القديمة"""
        try:
            async with db.pool.acquire() as conn:
                result = await conn.execute('''
                    DELETE FROM activity_logs 
                    WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '%s days'
                ''' % days)
                return int(result.split()[-1]) if result.split() else 0
        except Exception as e:
            print(f"Error cleaning up activities: {e}")
            return 0
