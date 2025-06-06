from typing import Dict, Any, List
from datetime import datetime, date
from .models import db

class StatisticsManager:
    @staticmethod
    async def increment_forwarded(task_id: int) -> bool:
        """Increment forwarded messages count"""
        try:
            async with db.pool.acquire() as conn:
                await conn.execute('''
                    INSERT INTO statistics (task_id, messages_forwarded, last_message_time, date)
                    VALUES ($1, 1, CURRENT_TIMESTAMP, CURRENT_DATE)
                    ON CONFLICT (task_id, date)
                    DO UPDATE SET 
                        messages_forwarded = statistics.messages_forwarded + 1,
                        last_message_time = CURRENT_TIMESTAMP
                ''', task_id)
                return True
        except Exception as e:
            print(f"Error incrementing forwarded: {e}")
            return False
    
    @staticmethod
    async def increment_filtered(task_id: int) -> bool:
        """Increment filtered messages count"""
        try:
            async with db.pool.acquire() as conn:
                await conn.execute('''
                    INSERT INTO statistics (task_id, messages_filtered, date)
                    VALUES ($1, 1, CURRENT_DATE)
                    ON CONFLICT (task_id, date)
                    DO UPDATE SET messages_filtered = statistics.messages_filtered + 1
                ''', task_id)
                return True
        except Exception as e:
            print(f"Error incrementing filtered: {e}")
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
