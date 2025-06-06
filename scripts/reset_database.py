import asyncio
import asyncpg
from config import Config

async def reset_database():
    """Reset database by dropping and recreating all tables"""
    try:
        conn = await asyncpg.connect(Config.DATABASE_URL)
        
        print("🔄 Resetting database...")
        
        # حذف جميع الجداول بالترتيب الصحيح
        tables_to_drop = [
            'error_logs',
            'userbot_sessions', 
            'statistics',
            'message_filters',
            'forwarding_tasks',
            'users'
        ]
        
        for table in tables_to_drop:
            try:
                await conn.execute(f'DROP TABLE IF EXISTS {table} CASCADE;')
                print(f"✅ Dropped table: {table}")
            except Exception as e:
                print(f"⚠️ Error dropping {table}: {e}")
        
        print("✅ All tables dropped successfully")
        
        # إعادة إنشاء الجداول
        from database.models import db
        await db.initialize()
        
        # إنشاء مستخدم مدير إذا كان محدد
        if Config.ADMIN_USER_ID:
            await conn.execute('''
                INSERT INTO users (user_id, username, first_name, is_admin, is_active)
                VALUES ($1, 'admin', 'Admin', TRUE, TRUE)
            ''', Config.ADMIN_USER_ID)
            print(f"✅ Admin user {Config.ADMIN_USER_ID} created")
        
        await conn.close()
        print("🎉 Database reset completed successfully!")
        
    except Exception as e:
        print(f"❌ Error resetting database: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(reset_database())
