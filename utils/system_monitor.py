import psutil
import asyncio
from typing import Dict, Any, Tuple
from datetime import datetime, timedelta

class SystemMonitor:
    """مراقب النظام للتحقق من الأداء والحدود"""
    
    @staticmethod
    def get_system_stats() -> Dict[str, Any]:
        """الحصول على إحصائيات النظام"""
        try:
            return {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage('/').percent,
                "network_io": psutil.net_io_counters(),
                "process_count": len(psutil.pids()),
                "timestamp": datetime.now()
            }
        except Exception as e:
            print(f"Error getting system stats: {e}")
            return {}
    
    @staticmethod
    def check_system_health() -> Tuple[bool, str, str]:
        """فحص صحة النظام"""
        try:
            stats = SystemMonitor.get_system_stats()
            
            # فحص استخدام الذاكرة
            if stats.get("memory_percent", 0) > 90:
                return False, "memory_high", "استخدام الذاكرة مرتفع جداً (>90%)"
            
            # فحص استخدام المعالج
            if stats.get("cpu_percent", 0) > 95:
                return False, "cpu_high", "استخدام المعالج مرتفع جداً (>95%)"
            
            # فحص مساحة القرص
            if stats.get("disk_percent", 0) > 95:
                return False, "disk_full", "مساحة القرص ممتلئة (>95%)"
            
            # فحص عدد العمليات
            if stats.get("process_count", 0) > 1000:
                return False, "too_many_processes", "عدد العمليات كثير جداً"
            
            return True, "healthy", "النظام يعمل بشكل طبيعي"
            
        except Exception as e:
            return False, "check_failed", f"فشل في فحص النظام: {e}"
    
    @staticmethod
    async def check_database_health() -> Tuple[bool, str]:
        """فحص صحة قاعدة البيانات"""
        try:
            from database.models import db
            
            start_time = datetime.now()
            
            # اختبار الاتصال
            async with db.pool.acquire() as conn:
                await conn.fetchval('SELECT 1')
            
            response_time = (datetime.now() - start_time).total_seconds()
            
            if response_time > 5:
                return False, f"استجابة قاعدة البيانات بطيئة ({response_time:.2f}s)"
            
            return True, f"قاعدة البيانات تعمل بشكل طبيعي ({response_time:.2f}s)"
            
        except Exception as e:
            return False, f"خطأ في قاعدة البيانات: {e}"
    
    @staticmethod
    async def check_user_limits(user_id: int) -> Tuple[bool, str]:
        """فحص حدود المستخدم"""
        try:
            from database.task_manager import TaskManager
            from database.user_manager import UserManager
            
            # فحص عدد المهام
            user_tasks = await TaskManager.get_user_tasks(user_id)
            if len(user_tasks) >= 50:
                return False, "وصلت للحد الأقصى من المهام (50 مهمة)"
            
            # فحص حالة المستخدم
            user = await UserManager.get_user(user_id)
            if user and not user['is_active']:
                return False, "حسابك محظور من استخدام البوت"
            
            # فحص معدل الطلبات (يمكن تطويره لاحقاً)
            
            return True, "ضمن الحدود المسموحة"
            
        except Exception as e:
            return False, f"خطأ في فحص الحدود: {e}"
    
    @staticmethod
    def get_performance_recommendations() -> list:
        """الحصول على توصيات تحسين الأداء"""
        recommendations = []
        stats = SystemMonitor.get_system_stats()
        
        if stats.get("memory_percent", 0) > 80:
            recommendations.append("تقليل استخدام الذاكرة")
        
        if stats.get("cpu_percent", 0) > 80:
            recommendations.append("تقليل العمليات المكثفة")
        
        if stats.get("disk_percent", 0) > 85:
            recommendations.append("تنظيف مساحة القرص")
        
        return recommendations
