import json
from typing import Optional, List, Dict, Any
from datetime import datetime
from .models import db

class TaskManager:
    @staticmethod
    async def create_task(user_id: int, task_name: str, source_chat_id: int, 
                         target_chat_id: int, task_type: str = 'forward',
                         settings: Dict[str, Any] = None) -> Optional[int]:
        """Create new forwarding task"""
        try:
            if settings is None:
                settings = {}
            
            async with db.pool.acquire() as conn:
                task_id = await conn.fetchval('''
                    INSERT INTO forwarding_tasks 
                    (user_id, task_name, source_chat_id, target_chat_id, task_type, settings)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    RETURNING id
                ''', user_id, task_name, source_chat_id, target_chat_id, task_type, json.dumps(settings))
                return task_id
        except Exception as e:
            print(f"Error creating task: {e}")
            return None
    
    @staticmethod
    async def get_task(task_id: int) -> Optional[Dict[str, Any]]:
        """Get task by ID"""
        try:
            async with db.pool.acquire() as conn:
                row = await conn.fetchrow(
                    'SELECT * FROM forwarding_tasks WHERE id = $1', task_id
                )
                if row:
                    task = dict(row)
                    task['settings'] = json.loads(task['settings']) if task['settings'] else {}
                    return task
                return None
        except Exception as e:
            print(f"Error getting task: {e}")
            return None
    
    @staticmethod
    async def get_user_tasks(user_id: int) -> List[Dict[str, Any]]:
        """Get all tasks for a user"""
        try:
            async with db.pool.acquire() as conn:
                rows = await conn.fetch(
                    'SELECT * FROM forwarding_tasks WHERE user_id = $1 ORDER BY created_at DESC',
                    user_id
                )
                tasks = []
                for row in rows:
                    task = dict(row)
                    task['settings'] = json.loads(task['settings']) if task['settings'] else {}
                    tasks.append(task)
                return tasks
        except Exception as e:
            print(f"Error getting user tasks: {e}")
            return []
    
    @staticmethod
    async def update_task_settings(task_id: int, settings: Dict[str, Any]) -> bool:
        """Update task settings"""
        try:
            async with db.pool.acquire() as conn:
                await conn.execute('''
                    UPDATE forwarding_tasks 
                    SET settings = $1, updated_at = CURRENT_TIMESTAMP 
                    WHERE id = $2
                ''', json.dumps(settings), task_id)
                return True
        except Exception as e:
            print(f"Error updating task settings: {e}")
            return False
    
    @staticmethod
    async def toggle_task(task_id: int, is_active: bool = None) -> bool:
        """Toggle task active status"""
        try:
            async with db.pool.acquire() as conn:
                if is_active is None:
                    # Toggle current status
                    current_status = await conn.fetchval(
                        'SELECT is_active FROM forwarding_tasks WHERE id = $1', task_id
                    )
                    is_active = not current_status
                
                await conn.execute(
                    'UPDATE forwarding_tasks SET is_active = $1 WHERE id = $2',
                    is_active, task_id
                )
                return True
        except Exception as e:
            print(f"Error toggling task: {e}")
            return False
    
    @staticmethod
    async def delete_task(task_id: int) -> bool:
        """Delete task"""
        try:
            async with db.pool.acquire() as conn:
                await conn.execute('DELETE FROM forwarding_tasks WHERE id = $1', task_id)
                return True
        except Exception as e:
            print(f"Error deleting task: {e}")
            return False
    
    @staticmethod
    async def get_active_tasks() -> List[Dict[str, Any]]:
        """Get all active tasks"""
        try:
            async with db.pool.acquire() as conn:
                rows = await conn.fetch(
                    'SELECT * FROM forwarding_tasks WHERE is_active = TRUE'
                )
                tasks = []
                for row in rows:
                    task = dict(row)
                    task['settings'] = json.loads(task['settings']) if task['settings'] else {}
                    tasks.append(task)
                return tasks
        except Exception as e:
            print(f"Error getting active tasks: {e}")
            return []

    @staticmethod
    async def update_media_filters(task_id: int, media_types: List[str]) -> bool:
        """تحديث فلاتر الوسائط"""
        try:
            task = await TaskManager.get_task(task_id)
            if not task:
                return False
            
            settings = task['settings']
            settings['media_filters'] = {
                'enabled': True,
                'allowed_types': media_types
            }
            return await TaskManager.update_task_settings(task_id, settings)
        except Exception as e:
            print(f"Error updating media filters: {e}")
            return False

    @staticmethod
    async def update_text_filters(task_id: int, blocked_words: List[str], 
                                required_words: List[str]) -> bool:
        """تحديث فلاتر النص"""
        try:
            task = await TaskManager.get_task(task_id)
            if not task:
                return False
            
            settings = task['settings']
            settings['blocked_words'] = blocked_words
            settings['required_words'] = required_words
            return await TaskManager.update_task_settings(task_id, settings)
        except Exception as e:
            print(f"Error updating text filters: {e}")
            return False

    @staticmethod
    async def update_advanced_filters(task_id: int, filters: Dict[str, bool]) -> bool:
        """تحديث الفلاتر المتقدمة"""
        try:
            task = await TaskManager.get_task(task_id)
            if not task:
                return False
            
            settings = task['settings']
            settings['advanced_filters'] = filters
            return await TaskManager.update_task_settings(task_id, settings)
        except Exception as e:
            print(f"Error updating advanced filters: {e}")
            return False

    @staticmethod
    async def update_replacements(task_id: int, replacements: Dict[str, str]) -> bool:
        """تحديث قائمة الاستبدالات"""
        try:
            task = await TaskManager.get_task(task_id)
            if not task:
                return False
            
            settings = task['settings']
            settings['replacements'] = replacements
            return await TaskManager.update_task_settings(task_id, settings)
        except Exception as e:
            print(f"Error updating replacements: {e}")
            return False

    @staticmethod
    async def update_delay_settings(task_id: int, delay_config: Dict[str, Any]) -> bool:
        """تحديث إعدادات التأخير"""
        try:
            task = await TaskManager.get_task(task_id)
            if not task:
                return False
            
            settings = task['settings']
            settings['delay'] = delay_config
            return await TaskManager.update_task_settings(task_id, settings)
        except Exception as e:
            print(f"Error updating delay settings: {e}")
            return False

    @staticmethod
    async def update_user_lists(task_id: int, whitelist: List[int], 
                              blacklist: List[int]) -> bool:
        """تحديث القوائم البيضاء والسوداء"""
        try:
            task = await TaskManager.get_task(task_id)
            if not task:
                return False
            
            settings = task['settings']
            settings['whitelist'] = whitelist
            settings['blacklist'] = blacklist
            return await TaskManager.update_task_settings(task_id, settings)
        except Exception as e:
            print(f"Error updating user lists: {e}")
            return False

    @staticmethod
    async def add_to_list(task_id: int, user_id: int, list_type: str) -> bool:
        """إضافة مستخدم لقائمة (whitelist أو blacklist)"""
        try:
            task = await TaskManager.get_task(task_id)
            if not task:
                return False
            
            settings = task['settings']
            current_list = settings.get(list_type, [])
            
            if user_id not in current_list:
                current_list.append(user_id)
                settings[list_type] = current_list
                return await TaskManager.update_task_settings(task_id, settings)
            
            return True
        except Exception as e:
            print(f"Error adding to {list_type}: {e}")
            return False

    @staticmethod
    async def remove_from_list(task_id: int, user_id: int, list_type: str) -> bool:
        """حذف مستخدم من قائمة"""
        try:
            task = await TaskManager.get_task(task_id)
            if not task:
                return False
            
            settings = task['settings']
            current_list = settings.get(list_type, [])
            
            if user_id in current_list:
                current_list.remove(user_id)
                settings[list_type] = current_list
                return await TaskManager.update_task_settings(task_id, settings)
            
            return True
        except Exception as e:
            print(f"Error removing from {list_type}: {e}")
            return False
