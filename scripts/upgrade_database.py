import asyncio
import asyncpg
from config import Config

async def upgrade_database():
    """ترقية قاعدة البيانات مع المحافظة على البيانات الحالية"""
    try:
        print("🔄 بدء ترقية قاعدة البيانات...")
        
        # الاتصال بقاعدة البيانات
        conn = await asyncpg.connect(Config.DATABASE_URL)
        print("✅ تم الاتصال بقاعدة البيانات")
        
        # تشغيل ترقية قاعدة البيانات
        from database.models import db
        await db.initialize()
        
        print("✅ تم ترقية قاعدة البيانات بنجاح")
        print("✅ جميع البيانات الحالية محفوظة")
        
        # إنشاء إعدادات افتراضية للمستخدمين الحاليين
        print("🔄 إنشاء إعدادات افتراضية للمستخدمين الحاليين...")
        
        users = await conn.fetch('SELECT user_id FROM users')
        for user in users:
            try:
                await conn.execute('''
                    INSERT INTO user_settings (user_id)
                    VALUES ($1)
                    ON CONFLICT (user_id) DO NOTHING
                ''', user['user_id'])
            except Exception as e:
                print(f"تحذير: لا يمكن إنشاء إعدادات للمستخدم {user['user_id']}: {e}")
        
        print(f"✅ تم إنشاء إعدادات افتراضية لـ {len(users)} مستخدم")
        
        await conn.close()
        print("✅ اكتملت ترقية قاعدة البيانات بنجاح!")
        
    except Exception as e:
        print(f"❌ خطأ في ترقية قاعدة البيانات: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(upgrade_database())
