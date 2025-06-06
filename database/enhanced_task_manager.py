import json
from typing import Optional, List, Dict, Any
from datetime import datetime
from .models import db

class EnhancedTaskManager:
    @staticmethod
    async def create_task_with_filters(user_id: int, task_name: str, description: str,
                                     source_chat_id: int, target_chat_id: int, 
                                     task_type: str = 'forward', priority: int = 1,
                                     settings: Dict[str, Any] = None,
                                     filters: List[Dict[str, Any]] = None) -> Optional[int]:
        """إنشاء مهمة مع فلاتر"""
        try:
            if settings is None:
                settings = {}
            if filters is None:
                filters = []
            
            async with db.pool.acquire() as conn:
                async with conn.transaction():
                    # إنشاء المهمة
                    task_id = await conn.fetchval('''
                        INSERT INTO forwarding_tasks 
                        (user_id, task_name, description, source_chat_id, target_chat_id, 
                         task_type, priority, settings)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                        RETURNING id
                    ''', user_id, task_name, description, source_chat_id, target_chat_id, 
                        task_type, priority, json.dumps(settings))
                    
                    # إضافة الفلاتر
                    for filter_data in filters:
                        await conn.execute('''
                            INSERT INTO task_filters 
                            (task_id, filter_category, filter_type, filter_value, filter_config)
                            VALUES ($1, $2, $3, $4, $5)
                        ''', task_id, filter_data.get('category'), filter_data.get('type'),
                            filter_data.get('value'), json.dumps(filter_data.get('config', {})))
                    
                    # تحديث عداد المهام للمستخدم
                    await conn.execute('''
                        UPDATE users 
                        SET total_tasks_created = total_tasks_created + 1 
                        WHERE user_id = $1
                    ''', user_id)
                    
                    return task_id
        except Exception as e:
            print(f"Error creating task with filters: {e}")
            return None
    
    @staticmethod
    async def get_task_with_filters(task_id: int) -> Optional[Dict[str, Any]]:
        """الحصول على مهمة مع فلاترها"""
        try:
            async with db.pool.acquire() as conn:
                # الحصول على المهمة
                task_row = await conn.fetchrow(
                    'SELECT * FROM forwarding_tasks WHERE id = $1', task_id
                )
                
                if not task_row:
                    return None
                
                task = dict(task_row)
                task['settings'] = json.loads(task['settings']) if task['settings'] else {}
                
                # الحصول على الفلاتر
                filters_rows = await conn.fetch(
                    'SELECT * FROM task_filters WHERE task_id = $1 ORDER BY priority, id',
                    task_id
                )
                
                task['filters'] = []
                for filter_row in filters_rows:
                    filter_data = dict(filter_row)
                    filter_data['filter_config'] = json.loads(filter_data['filter_config']) if filter_data['filter_config'] else {}
                    task['filters'].append(filter_data)
                
                return task
        except Exception as e:
            print(f"Error getting task with filters: {e}")
            return None
    
    @staticmethod
    async def add_filter_to_task(task_id: int, filter_category: str, filter_type: str,
                               filter_value: str = None, filter_config: Dict[str, Any] = None,
                               priority: int = 1) -> Optional[int]:
        """إضافة فلتر لمهمة"""
        try:
            async with db.pool.acquire() as conn:
                filter_id = await conn.fetchval('''
                    INSERT INTO task_filters 
                    (task_id, filter_category, filter_type, filter_value, filter_config, priority)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    RETURNING id
                ''', task_id, filter_category, filter_type, filter_value,
                    json.dumps(filter_config or {}), priority)
                
                # تحديث وقت تعديل المهمة
                await conn.execute(
                    'UPDATE forwarding_tasks SET updated_at = CURRENT_TIMESTAMP WHERE id = $1',
                    task_id
                )
                
                return filter_id
        except Exception as e:
            print(f"Error adding filter to task: {e}")
            return None
    
    @staticmethod
    async def update_task_statistics(task_id: int, forwarded: int = 0, filtered: int = 0,
                                   failed: int = 0, processing_time_ms: int = 0) -> bool:
        """تحديث إحصائيات المهمة"""
        try:
            async with db.pool.acquire() as conn:
                async with conn.transaction():
                    # تحديث الإحصائيات اليومية
                    await conn.execute('''
                        INSERT INTO statistics 
                        (task_id, messages_forwarded, messages_filtered, messages_failed, processing_time_ms)
                        VALUES ($1, $2, $3, $4, $5)
                        ON CONFLICT (task_id, date, hour)
                        DO UPDATE SET 
                            messages_forwarded = statistics.messages_forwarded + EXCLUDED.messages_forwarded,
                            messages_filtered = statistics.messages_filtered + EXCLUDED.messages_filtered,
                            messages_failed = statistics.messages_failed + EXCLUDED.messages_failed,
                            processing_time_ms = statistics.processing_time_ms + EXCLUDED.processing_time_ms
                    ''', task_id, forwarded, filtered, failed, processing_time_ms)
                    
                    # تحديث إحصائيات المهمة الإجمالية
                    await conn.execute('''
                        UPDATE forwarding_tasks 
                        SET 
                            total_forwarded = total_forwarded + $2,
                            total_filtered = total_filtered + $3,
                            last_message_time = CASE WHEN $2 > 0 THEN CURRENT_TIMESTAMP ELSE last_message_time END,
                            success_rate = CASE 
                                WHEN (total_forwarded + total_filtered + $2 + $3) > 0 
                                THEN ((total_forwarded + $2) * 100.0) / (total_forwarded + total_filtered + $2 + $3)
                                ELSE 0 
                            END
                        WHERE id = $1
                    ''', task_id, forwarded, filtered)
                    
                    return True
        except Exception as e:
            print(f"Error updating task statistics: {e}")
            return False
