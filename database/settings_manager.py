from typing import Dict, Any, Optional
from .models import db

class SettingsManager:
    @staticmethod
    async def get_user_settings(user_id: int) -> Dict[str, Any]:
        """الحصول على إعدادات المستخدم"""
        try:
            async with db.pool.acquire() as conn:
                row = await conn.fetchrow(
                    'SELECT * FROM user_settings WHERE user_id = $1', user_id
                )
                if row:
                    return dict(row)
                else:
                    # إنشاء إعدادات افتراضية
                    await SettingsManager.create_default_settings(user_id)
                    return await SettingsManager.get_user_settings(user_id)
        except Exception as e:
            print(f"Error getting user settings: {e}")
            return {}
    
    @staticmethod
    async def create_default_settings(user_id: int) -> bool:
        """إنشاء إعدادات افتراضية للمستخدم"""
        try:
            async with db.pool.acquire() as conn:
                await conn.execute('''
                    INSERT INTO user_settings (user_id)
                    VALUES ($1)
                    ON CONFLICT (user_id) DO NOTHING
                ''', user_id)
                return True
        except Exception as e:
            print(f"Error creating default settings: {e}")
            return False
    
    @staticmethod
    async def update_setting(user_id: int, setting_name: str, value: Any) -> bool:
        """تحديث إعداد محدد"""
        try:
            async with db.pool.acquire() as conn:
                # التأكد من وجود الإعدادات
                await SettingsManager.create_default_settings(user_id)
                
                # قائمة الحقول المسموحة لتجنب SQL injection
                allowed_fields = [
                    'notifications_enabled', 'task_notifications', 'error_notifications',
                    'stats_notifications', 'system_notifications', 'dark_mode',
                    'auto_backup', 'backup_frequency', 'chart_type', 'stats_period',
                    'ui_language'
                ]
                
                if setting_name not in allowed_fields:
                    print(f"Invalid setting name: {setting_name}")
                    return False
                
                # تحديث الإعداد
                query = f'''
                    UPDATE user_settings 
                    SET {setting_name} = $1, updated_at = CURRENT_TIMESTAMP 
                    WHERE user_id = $2
                '''
                await conn.execute(query, value, user_id)
                return True
        except Exception as e:
            print(f"Error updating setting: {e}")
            return False
    
    @staticmethod
    async def update_multiple_settings(user_id: int, settings: Dict[str, Any]) -> bool:
        """تحديث عدة إعدادات"""
        try:
            async with db.pool.acquire() as conn:
                # التأكد من وجود الإعدادات
                await SettingsManager.create_default_settings(user_id)
                
                # قائمة الحقول المسموحة
                allowed_fields = [
                    'notifications_enabled', 'task_notifications', 'error_notifications',
                    'stats_notifications', 'system_notifications', 'dark_mode',
                    'auto_backup', 'backup_frequency', 'chart_type', 'stats_period',
                    'ui_language'
                ]
                
                # فلترة الإعدادات المسموحة فقط
                filtered_settings = {k: v for k, v in settings.items() if k in allowed_fields}
                
                if not filtered_settings:
                    return False
                
                # بناء استعلام التحديث
                set_clauses = []
                values = []
                for i, (key, value) in enumerate(filtered_settings.items(), 1):
                    set_clauses.append(f"{key} = ${i}")
                    values.append(value)
                
                values.append(user_id)
                
                query = f'''
                    UPDATE user_settings 
                    SET {", ".join(set_clauses)}, updated_at = CURRENT_TIMESTAMP 
                    WHERE user_id = ${len(values)}
                '''
                
                await conn.execute(query, *values)
                return True
        except Exception as e:
            print(f"Error updating multiple settings: {e}")
            return False
    
    @staticmethod
    async def reset_user_settings(user_id: int) -> bool:
        """إعادة تعيين إعدادات المستخدم للافتراضية"""
        try:
            async with db.pool.acquire() as conn:
                await conn.execute('''
                    DELETE FROM user_settings WHERE user_id = $1
                ''', user_id)
                await SettingsManager.create_default_settings(user_id)
                return True
        except Exception as e:
            print(f"Error resetting user settings: {e}")
            return False
