import asyncio
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database.models import db
from handlers.userbot_handlers import UserbotHandlers
from config import Config

async def complete_setup():
    """إعداد شامل للبوت"""
    try:
        print("🚀 بدء الإعداد الشامل للبوت...")
        
        # 1. تهيئة قاعدة البيانات
        print("📊 تهيئة قاعدة البيانات...")
        await db.initialize()
        print("✅ تم إنشاء قاعدة البيانات والجداول")
        
        # 2. إنشاء المدير الرئيسي
        if Config.ADMIN_USER_ID:
            async with db.pool.acquire() as conn:
                await conn.execute('''
                    INSERT INTO users (user_id, username, first_name, is_admin, is_active)
                    VALUES ($1, 'admin', 'Admin', TRUE, TRUE)
                    ON CONFLICT (user_id) DO UPDATE SET is_admin = TRUE
                ''', Config.ADMIN_USER_ID)
            print(f"✅ تم إنشاء المدير الرئيسي: {Config.ADMIN_USER_ID}")
        
        # 3. تحميل جلسات Userbot النشطة
        print("🤖 تحميل جلسات Userbot...")
        await UserbotHandlers.load_userbot_sessions()
        print("✅ تم تحميل جلسات Userbot")
        
        # 4. إنشاء فهارس إضافية لتحسين الأداء
        print("⚡ إنشاء فهارس الأداء...")
        async with db.pool.acquire() as conn:
            # فهارس إضافية
            await conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_forwarding_tasks_active 
                ON forwarding_tasks(is_active) WHERE is_active = TRUE;
            ''')
            
            await conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_statistics_task_date 
                ON statistics(task_id, date);
            ''')
            
            await conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_users_active 
                ON users(is_active) WHERE is_active = TRUE;
            ''')
        
        print("✅ تم إنشاء فهارس الأداء")
        
        # 5. إنشاء بيانات تجريبية (اختياري)
        print("📝 إنشاء بيانات تجريبية...")
        await create_sample_data()
        print("✅ تم إنشاء البيانات التجريبية")
        
        print("\n🎉 تم إكمال الإعداد بنجاح!")
        print("=" * 50)
        print("📋 ملخص الإعداد:")
        print("✅ قاعدة البيانات: جاهزة")
        print("✅ الجداول: تم إنشاؤها")
        print("✅ الفهارس: تم إنشاؤها")
        print("✅ المدير الرئيسي: تم تعيينه")
        print("✅ جلسات Userbot: تم تحميلها")
        print("✅ البيانات التجريبية: تم إنشاؤها")
        print("\n🚀 البوت جاهز للتشغيل!")
        
    except Exception as e:
        print(f"❌ خطأ في الإعداد: {e}")
        raise

async def create_sample_data():
    """إنشاء بيانات تجريبية"""
    try:
        async with db.pool.acquire() as conn:
            # إنشاء مستخدم تجريبي
            await conn.execute('''
                INSERT INTO users (user_id, username, first_name, is_admin, is_active)
                VALUES (123456789, 'test_user', 'مستخدم تجريبي', FALSE, TRUE)
                ON CONFLICT (user_id) DO NOTHING
            ''')
            
            # إنشاء مهمة تجريبية
            task_id = await conn.fetchval('''
                INSERT INTO forwarding_tasks 
                (user_id, task_name, source_chat_id, target_chat_id, task_type, settings, is_active)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT DO NOTHING
                RETURNING id
            ''', 123456789, 'مهمة تجريبية', -1001234567890, -1009876543210, 'forward', '{}', False)
            
            # إنشاء إحصائيات تجريبية
            if task_id:
                await conn.execute('''
                    INSERT INTO statistics (task_id, messages_forwarded, messages_filtered, date)
                    VALUES ($1, 50, 10, CURRENT_DATE - INTERVAL '1 day')
                    ON CONFLICT (task_id, date) DO NOTHING
                ''', task_id)
                
                await conn.execute('''
                    INSERT INTO statistics (task_id, messages_forwarded, messages_filtered, date)
                    VALUES ($1, 75, 15, CURRENT_DATE)
                    ON CONFLICT (task_id, date) DO NOTHING
                ''', task_id)
        
    except Exception as e:
        print(f"تحذير: فشل في إنشاء البيانات التجريبية: {e}")

if __name__ == "__main__":
    asyncio.run(complete_setup())
