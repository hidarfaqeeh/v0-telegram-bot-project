import json
from typing import Optional, List, Dict, Any, Tuple
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

    # Enhanced methods from enhanced_task_manager.py
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

    @staticmethod
    async def validate_task_creation(user_id: int, task_name: str, source_chat_id: int, target_chat_id: int) -> Tuple[bool, str]:
        """التحقق من إمكانية إنشاء المهمة"""
        try:
            async with db.pool.acquire() as conn:
                # التحقق من عدد المهام للمستخدم
                task_count = await conn.fetchval(
                    'SELECT COUNT(*) FROM forwarding_tasks WHERE user_id = $1', user_id
                )
                
                if task_count >= 50:  # حد أقصى 50 مهمة لكل مستخدم
                    return False, "❌ وصلت للحد الأقصى من المهام (50 مهمة)"
                
                # التحقق من تكرار اسم المهمة
                existing_name = await conn.fetchval(
                    'SELECT id FROM forwarding_tasks WHERE user_id = $1 AND task_name = $2',
                    user_id, task_name
                )
                
                if existing_name:
                    return False, f"❌ يوجد مهمة بنفس الاسم '{task_name}' مسبقاً"
                
                # التحقق من تكرار المصدر والهدف
                existing_route = await conn.fetchval(
                    'SELECT id FROM forwarding_tasks WHERE user_id = $1 AND source_chat_id = $2 AND target_chat_id = $3',
                    user_id, source_chat_id, target_chat_id
                )
                
                if existing_route:
                    return False, "❌ يوجد مهمة بنفس المصدر والهدف مسبقاً"
                
                # التحقق من أن المصدر مختلف عن الهدف
                if source_chat_id == target_chat_id:
                    return False, "❌ لا يمكن أن يكون المصدر والهدف نفس المحادثة"
                
                return True, "✅ يمكن إنشاء المهمة"
                
        except Exception as e:
            print(f"Error validating task creation: {e}")
            return False, "❌ خطأ في التحقق من البيانات"

    @staticmethod
    async def create_task_with_validation(user_id: int, task_name: str, source_chat_id: int, 
                                        target_chat_id: int, task_type: str = 'forward',
                                        settings: Dict[str, Any] = None) -> Tuple[Optional[int], str]:
        """إنشاء مهمة مع التحقق الشامل"""
        try:
            # التحقق من صحة البيانات
            from utils.validators import DataValidator
            
            # التحقق من اسم المهمة
            is_valid, message = DataValidator.validate_task_name_advanced(task_name, user_id)
            if not is_valid:
                return None, message
            
            # التحقق من معرفات المحادثات
            is_valid, _, message, _ = DataValidator.validate_chat_id_advanced(str(source_chat_id))
            if not is_valid:
                return None, f"خطأ في محادثة المصدر: {message}"
            
            is_valid, _, message, _ = DataValidator.validate_chat_id_advanced(str(target_chat_id))
            if not is_valid:
                return None, f"خطأ في محادثة الهدف: {message}"
            
            # التحقق من إمكانية إنشاء المهمة
            can_create, validation_message = await TaskManager.validate_task_creation(
                user_id, task_name, source_chat_id, target_chat_id
            )
            if not can_create:
                return None, validation_message
            
            # التحقق من الإعدادات
            if settings:
                is_valid, message = DataValidator.validate_settings_integrity(settings)
                if not is_valid:
                    return None, message
            
            # إنشاء المهمة
            task_id = await TaskManager.create_task(
                user_id, task_name, source_chat_id, target_chat_id, task_type, settings
            )
            
            if task_id:
                # تسجيل النشاط
                from database.activity_manager import ActivityManager
                await ActivityManager.log_activity(
                    user_id=user_id,
                    activity_type="task_created",
                    activity_category="task_management",
                    description=f"تم إنشاء مهمة جديدة: {task_name}",
                    target_type="task",
                    target_id=task_id,
                    new_values={
                        "task_name": task_name,
                        "source_chat_id": source_chat_id,
                        "target_chat_id": target_chat_id,
                        "task_type": task_type
                    }
                )
                
                return task_id, "✅ تم إنشاء المهمة بنجاح"
            else:
                return None, "❌ فشل في إنشاء المهمة"
                
        except Exception as e:
            print(f"Error creating task with validation: {e}")
            return None, "❌ حدث خطأ أثناء إنشاء المهمة"

    @staticmethod
    async def update_text_filters_with_validation(task_id: int, blocked_words: List[str], 
                                                required_words: List[str], user_id: int) -> Tuple[bool, str]:
        """تحديث فلاتر النص مع التحقق"""
        try:
            from utils.validators import DataValidator
            
            # التحقق من كل كلمة محظورة
            for word in blocked_words:
                is_valid, message = DataValidator.validate_word_advanced(word, blocked_words)
                if not is_valid:
                    return False, f"خطأ في الكلمة المحظورة '{word}': {message}"
            
            # التحقق من كل كلمة مطلوبة
            for word in required_words:
                is_valid, message = DataValidator.validate_word_advanced(word, required_words)
                if not is_valid:
                    return False, f"خطأ في الكلمة المطلوبة '{word}': {message}"
            
            # التحقق من التضارب
            conflicts = set(blocked_words) & set(required_words)
            if conflicts:
                return False, f"❌ تضارب في الكلمات: {', '.join(conflicts)}"
            
            # الحصول على القيم القديمة للتسجيل
            task = await TaskManager.get_task(task_id)
            old_blocked = task['settings'].get('blocked_words', [])
            old_required = task['settings'].get('required_words', [])  [])
            old_required = task['settings'].get('required_words', [])
            
            # تحديث الفلاتر
            success = await TaskManager.update_text_filters(task_id, blocked_words, required_words)
            
            if success:
                # تسجيل النشاط
                from database.activity_manager import ActivityManager
                await ActivityManager.log_activity(
                    user_id=user_id,
                    activity_type="text_filters_updated",
                    activity_category="task_settings",
                    description=f"تم تحديث فلاتر النص للمهمة {task_id}",
                    target_type="task",
                    target_id=task_id,
                    old_values={
                        "blocked_words": old_blocked,
                        "required_words": old_required
                    },
                    new_values={
                        "blocked_words": blocked_words,
                        "required_words": required_words
                    }
                )
                
                return True, "✅ تم تحديث فلاتر النص بنجاح"
            else:
                return False, "❌ فشل في تحديث فلاتر النص"
                
        except Exception as e:
            print(f"Error updating text filters: {e}")
            return False, "❌ حدث خطأ أثناء تحديث الفلاتر"
