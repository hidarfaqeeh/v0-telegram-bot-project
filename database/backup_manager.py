import json
import gzip
import hashlib
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from .models import db

class BackupManager:
    @staticmethod
    async def create_backup(user_id: int, backup_name: str, backup_type: str = 'manual',
                          backup_data: Dict[str, Any] = None, 
                          compress: bool = True) -> Optional[int]:
        """إنشاء نسخة احتياطية"""
        try:
            # تحضير البيانات
            if backup_data is None:
                backup_data = await BackupManager._collect_user_data(user_id)
            
            # ضغط البيانات إذا لزم الأمر
            data_json = json.dumps(backup_data, ensure_ascii=False, default=str)
            
            if compress:
                compressed_data = gzip.compress(data_json.encode('utf-8'))
                file_size = len(compressed_data)
                compression_type = 'gzip'
            else:
                compressed_data = data_json.encode('utf-8')
                file_size = len(compressed_data)
                compression_type = 'none'
            
            # حساب checksum
            checksum = hashlib.sha256(compressed_data).hexdigest()
            
            # حفظ في قاعدة البيانات
            async with db.pool.acquire() as conn:
                backup_id = await conn.fetchval('''
                    INSERT INTO backup_files 
                    (user_id, backup_name, backup_type, file_size, backup_data,
                     compression_type, checksum, expires_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    RETURNING id
                ''', user_id, backup_name, backup_type, file_size, backup_data,
                    compression_type, checksum, 
                    datetime.now() + timedelta(days=90))  # انتهاء صلاحية بعد 90 يوم
                
                return backup_id
        except Exception as e:
            print(f"Error creating backup: {e}")
            return None
    
    @staticmethod
    async def _collect_user_data(user_id: int) -> Dict[str, Any]:
        """جمع بيانات المستخدم للنسخة الاحتياطية"""
        try:
            async with db.pool.acquire() as conn:
                # بيانات المستخدم
                user_data = await conn.fetchrow(
                    'SELECT * FROM users WHERE user_id = $1', user_id
                )
                
                # إعدادات المستخدم
                settings_data = await conn.fetchrow(
                    'SELECT * FROM user_settings WHERE user_id = $1', user_id
                )
                
                # المهام
                tasks_data = await conn.fetch(
                    'SELECT * FROM forwarding_tasks WHERE user_id = $1', user_id
                )
                
                # فلاتر المهام
                task_ids = [task['id'] for task in tasks_data]
                filters_data = []
                if task_ids:
                    filters_data = await conn.fetch(
                        'SELECT * FROM task_filters WHERE task_id = ANY($1)', task_ids
                    )
                
                # الإحصائيات
                stats_data = []
                if task_ids:
                    stats_data = await conn.fetch(
                        'SELECT * FROM statistics WHERE task_id = ANY($1)', task_ids
                    )
                
                # جلسة Userbot
                userbot_data = await conn.fetchrow(
                    'SELECT * FROM userbot_sessions WHERE user_id = $1', user_id
                )
                
                return {
                    'user': dict(user_data) if user_data else None,
                    'settings': dict(settings_data) if settings_data else None,
                    'tasks': [dict(task) for task in tasks_data],
                    'filters': [dict(filter_item) for filter_item in filters_data],
                    'statistics': [dict(stat) for stat in stats_data],
                    'userbot': dict(userbot_data) if userbot_data else None,
                    'backup_info': {
                        'created_at': datetime.now().isoformat(),
                        'version': '2.0',
                        'total_tasks': len(tasks_data),
                        'total_filters': len(filters_data)
                    }
                }
        except Exception as e:
            print(f"Error collecting user data: {e}")
            return {}
    
    @staticmethod
    async def get_user_backups(user_id: int) -> List[Dict[str, Any]]:
        """الحصول على نسخ المستخدم الاحتياطية"""
        try:
            async with db.pool.acquire() as conn:
                rows = await conn.fetch('''
                    SELECT id, backup_name, backup_type, file_size, compression_type,
                           created_at, expires_at
                    FROM backup_files 
                    WHERE user_id = $1 
                    ORDER BY created_at DESC
                ''', user_id)
                return [dict(row) for row in rows]
        except Exception as e:
            print(f"Error getting user backups: {e}")
            return []
    
    @staticmethod
    async def delete_backup(backup_id: int, user_id: int) -> bool:
        """حذف نسخة احتياطية"""
        try:
            async with db.pool.acquire() as conn:
                result = await conn.execute(
                    'DELETE FROM backup_files WHERE id = $1 AND user_id = $2',
                    backup_id, user_id
                )
                return result != "DELETE 0"
        except Exception as e:
            print(f"Error deleting backup: {e}")
            return False
    
    @staticmethod
    async def cleanup_expired_backups() -> int:
        """تنظيف النسخ الاحتياطية المنتهية الصلاحية"""
        try:
            async with db.pool.acquire() as conn:
                result = await conn.execute('''
                    DELETE FROM backup_files 
                    WHERE expires_at < CURRENT_TIMESTAMP
                ''')
                return int(result.split()[-1]) if result.split() else 0
        except Exception as e:
            print(f"Error cleaning up expired backups: {e}")
            return 0
