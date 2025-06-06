from typing import Dict, Any, List
from datetime import datetime, date, timedelta
from .models import db

class StatisticsManager:
    @staticmethod
    async def increment_forwarded(task_id: int, bytes_transferred: int = 0, 
                                processing_time_ms: int = 0) -> bool:
        """تسجيل رسالة معاد توجيهها مع تفاصيل إضافية"""
        try:
            async with db.pool.acquire() as conn:
                current_hour = datetime.now().hour
                await conn.execute('''
                    INSERT INTO statistics 
                    (task_id, messages_forwarded, bytes_transferred, processing_time_ms, 
                     last_message_time, date, hour)
                    VALUES ($1, 1, $2, $3, CURRENT_TIMESTAMP, CURRENT_DATE, $4)
                    ON CONFLICT (task_id, date, hour)
                    DO UPDATE SET 
                        messages_forwarded = statistics.messages_forwarded + 1,
                        bytes_transferred = statistics.bytes_transferred + $2,
                        processing_time_ms = statistics.processing_time_ms + $3,
                        last_message_time = CURRENT_TIMESTAMP
                ''', task_id, bytes_transferred, processing_time_ms, current_hour)
                
                # تحديث إجمالي المهمة
                await conn.execute('''
                    UPDATE forwarding_tasks 
                    SET total_forwarded = total_forwarded + 1,
                        last_message_time = CURRENT_TIMESTAMP,
                        success_rate = (total_forwarded::decimal / GREATEST(total_forwarded + total_filtered, 1)) * 100
                    WHERE id = $1
                ''', task_id)
                
                return True
        except Exception as e:
            print(f"Error incrementing forwarded: {e}")
            return False
    
    @staticmethod
    async def increment_filtered(task_id: int, filter_type: str = None) -> bool:
        """تسجيل رسالة مفلترة مع نوع الفلتر"""
        try:
            async with db.pool.acquire() as conn:
                current_hour = datetime.now().hour
                
                # تحديث تفاصيل الفلتر
                filter_breakdown = {}
                if filter_type:
                    filter_breakdown[filter_type] = 1
                
                await conn.execute('''
                    INSERT INTO statistics 
                    (task_id, messages_filtered, filter_breakdown, date, hour)
                    VALUES ($1, 1, $2, CURRENT_DATE, $3)
                    ON CONFLICT (task_id, date, hour)
                    DO UPDATE SET 
                        messages_filtered = statistics.messages_filtered + 1,
                        filter_breakdown = statistics.filter_breakdown || $2
                ''', task_id, filter_breakdown, current_hour)
                
                # تحديث إجمالي المهمة
                await conn.execute('''
                    UPDATE forwarding_tasks 
                    SET total_filtered = total_filtered + 1,
                        success_rate = (total_forwarded::decimal / GREATEST(total_forwarded + total_filtered, 1)) * 100
                    WHERE id = $1
                ''', task_id)
                
                return True
        except Exception as e:
            print(f"Error incrementing filtered: {e}")
            return False
    
    @staticmethod
    async def increment_failed(task_id: int, error_type: str = None) -> bool:
        """تسجيل رسالة فاشلة مع نوع الخطأ"""
        try:
            async with db.pool.acquire() as conn:
                current_hour = datetime.now().hour
                
                # تحديث تفاصيل الخطأ
                error_breakdown = {}
                if error_type:
                    error_breakdown[error_type] = 1
                
                await conn.execute('''
                    INSERT INTO statistics 
                    (task_id, messages_failed, error_breakdown, date, hour)
                    VALUES ($1, 1, $2, CURRENT_DATE, $3)
                    ON CONFLICT (task_id, date, hour)
                    DO UPDATE SET 
                        messages_failed = statistics.messages_failed + 1,
                        error_breakdown = statistics.error_breakdown || $2
                ''', task_id, error_breakdown, current_hour)
                
                # تحديث عداد الأخطاء في المهمة
                await conn.execute('''
                    UPDATE forwarding_tasks 
                    SET error_count = error_count + 1
                    WHERE id = $1
                ''', task_id)
                
                return True
        except Exception as e:
            print(f"Error incrementing failed: {e}")
            return False
    
    @staticmethod
    async def get_task_stats(task_id: int, days: int = 7) -> List[Dict[str, Any]]:
        """Get task statistics for specified days"""
        try:
            async with db.pool.acquire() as conn:
                rows = await conn.fetch('''
                    SELECT * FROM statistics 
                    WHERE task_id = $1 AND date >= CURRENT_DATE - INTERVAL '%s days'
                    ORDER BY date DESC
                ''' % days, task_id)
                return [dict(row) for row in rows]
        except Exception as e:
            print(f"Error getting task stats: {e}")
            return []
    
    @staticmethod
    async def get_user_stats(user_id: int) -> Dict[str, Any]:
        """Get overall statistics for user"""
        try:
            async with db.pool.acquire() as conn:
                result = await conn.fetchrow('''
                    SELECT 
                        COUNT(ft.id) as total_tasks,
                        COUNT(CASE WHEN ft.is_active THEN 1 END) as active_tasks,
                        COALESCE(SUM(s.messages_forwarded), 0) as total_forwarded,
                        COALESCE(SUM(s.messages_filtered), 0) as total_filtered
                    FROM forwarding_tasks ft
                    LEFT JOIN statistics s ON ft.id = s.task_id
                    WHERE ft.user_id = $1
                ''', user_id)
                return dict(result) if result else {}
        except Exception as e:
            print(f"Error getting user stats: {e}")
            return {}

    @staticmethod
    async def get_hourly_stats(task_id: int, date_filter: date = None) -> List[Dict[str, Any]]:
        """الحصول على إحصائيات بالساعة"""
        try:
            async with db.pool.acquire() as conn:
                if date_filter is None:
                    date_filter = date.today()
                
                rows = await conn.fetch('''
                    SELECT * FROM statistics 
                    WHERE task_id = $1 AND date = $2
                    ORDER BY hour
                ''', task_id, date_filter)
                return [dict(row) for row in rows]
        except Exception as e:
            print(f"Error getting hourly stats: {e}")
            return []
    
    @staticmethod
    async def get_performance_metrics(task_id: int, days: int = 7) -> Dict[str, Any]:
        """الحصول على مقاييس الأداء"""
        try:
            async with db.pool.acquire() as conn:
                result = await conn.fetchrow('''
                    SELECT 
                        SUM(messages_forwarded) as total_forwarded,
                        SUM(messages_filtered) as total_filtered,
                        SUM(messages_failed) as total_failed,
                        SUM(bytes_transferred) as total_bytes,
                        AVG(processing_time_ms) as avg_processing_time,
                        COUNT(DISTINCT date) as active_days
                    FROM statistics 
                    WHERE task_id = $1 AND date >= CURRENT_DATE - INTERVAL '%s days'
                ''' % days, task_id)
                
                if result:
                    metrics = dict(result)
                    total_messages = (metrics['total_forwarded'] or 0) + (metrics['total_filtered'] or 0) + (metrics['total_failed'] or 0)
                    
                    if total_messages > 0:
                        metrics['success_rate'] = ((metrics['total_forwarded'] or 0) / total_messages) * 100
                        metrics['filter_rate'] = ((metrics['total_filtered'] or 0) / total_messages) * 100
                        metrics['error_rate'] = ((metrics['total_failed'] or 0) / total_messages) * 100
                    else:
                        metrics['success_rate'] = 0
                        metrics['filter_rate'] = 0
                        metrics['error_rate'] = 0
                    
                    return metrics
                
                return {}
        except Exception as e:
            print(f"Error getting performance metrics: {e}")
            return {}
    
    @staticmethod
    async def get_system_overview() -> Dict[str, Any]:
        """الحصول على نظرة عامة على النظام"""
        try:
            async with db.pool.acquire() as conn:
                # إحصائيات المستخدمين
                users_stats = await conn.fetchrow('''
                    SELECT 
                        COUNT(*) as total_users,
                        COUNT(CASE WHEN is_active THEN 1 END) as active_users,
                        COUNT(CASE WHEN is_admin THEN 1 END) as admin_users
                    FROM users
                ''')
                
                # إحصائيات المهام
                tasks_stats = await conn.fetchrow('''
                    SELECT 
                        COUNT(*) as total_tasks,
                        COUNT(CASE WHEN is_active THEN 1 END) as active_tasks,
                        SUM(total_forwarded) as total_forwarded,
                        SUM(total_filtered) as total_filtered
                    FROM forwarding_tasks
                ''')
                
                # إحصائيات اليوم
                today_stats = await conn.fetchrow('''
                    SELECT 
                        SUM(messages_forwarded) as today_forwarded,
                        SUM(messages_filtered) as today_filtered,
                        SUM(messages_failed) as today_failed
                    FROM statistics 
                    WHERE date = CURRENT_DATE
                ''')
                
                return {
                    'users': dict(users_stats) if users_stats else {},
                    'tasks': dict(tasks_stats) if tasks_stats else {},
                    'today': dict(today_stats) if today_stats else {}
                }
        except Exception as e:
            print(f"Error getting system overview: {e}")
            return {}
