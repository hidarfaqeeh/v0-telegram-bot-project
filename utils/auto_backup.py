import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

class AutoBackupSystem:
    """نظام النسخ الاحتياطي التلقائي"""
    
    @staticmethod
    async def create_full_backup() -> Tuple[bool, str, Optional[str]]:
        """إنشاء نسخة احتياطية كاملة"""
        try:
            from database.models import db
            
            backup_data = {
                "timestamp": datetime.now().isoformat(),
                "version": "1.0",
                "tables": {}
            }
            
            # قائمة الجداول للنسخ الاحتياطي
            tables = [
                "users", "forwarding_tasks", "message_statistics", 
                "activity_logs", "userbot_sessions", "notifications"
            ]
            
            async with db.pool.acquire() as conn:
                for table in tables:
                    try:
                        # الحصول على بيانات الجدول
                        rows = await conn.fetch(f"SELECT * FROM {table}")
                        backup_data["tables"][table] = [dict(row) for row in rows]
                    except Exception as e:
                        print(f"Error backing up table {table}: {e}")
                        continue
            
            # حفظ النسخة الاحتياطية
            backup_filename = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            backup_path = f"/tmp/{backup_filename}"
            
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2, default=str)
            
            return True, "تم إنشاء النسخة الاحتياطية بنجاح", backup_path
            
        except Exception as e:
            return False, f"فشل في إنشاء النسخة الاحتياطية: {e}", None
    
    @staticmethod
    async def schedule_auto_backup():
        """جدولة النسخ الاحتياطي التلقائي"""
        while True:
            try:
                # إنشاء نسخة احتياطية كل 24 ساعة
                await asyncio.sleep(24 * 60 * 60)  # 24 ساعة
                
                success, message, backup_path = await AutoBackupSystem.create_full_backup()
                
                if success:
                    # إشعار المديرين
                    from utils.notification_system import NotificationSystem
                    await NotificationSystem.send_admin_notification(
                        f"تم إنشاء نسخة احتياطية تلقائية بنجاح\n\nالملف: {backup_path}",
                        "success"
                    )
                else:
                    # إشعار بالفشل
                    await NotificationSystem.send_admin_notification(
                        f"فشل في إنشاء النسخة الاحتياطية التلقائية\n\nالخطأ: {message}",
                        "error",
                        urgent=True
                    )
                    
            except Exception as e:
                print(f"Error in auto backup scheduler: {e}")
                await asyncio.sleep(60 * 60)  # إعادة المحاولة بعد ساعة
    
    @staticmethod
    async def cleanup_old_backups(days_to_keep: int = 7):
        """تنظيف النسخ الاحتياطية القديمة"""
        try:
            import os
            import glob
            
            backup_dir = "/tmp"
            backup_pattern = os.path.join(backup_dir, "backup_*.json")
            backup_files = glob.glob(backup_pattern)
            
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            deleted_count = 0
            for backup_file in backup_files:
                try:
                    file_time = datetime.fromtimestamp(os.path.getctime(backup_file))
                    if file_time < cutoff_date:
                        os.remove(backup_file)
                        deleted_count += 1
                except Exception as e:
                    print(f"Error deleting backup file {backup_file}: {e}")
            
            return deleted_count
            
        except Exception as e:
            print(f"Error cleaning up old backups: {e}")
            return 0
