import asyncio
import asyncpg
from config import Config

async def migrate_database():
    """Run database migrations"""
    try:
        conn = await asyncpg.connect(Config.DATABASE_URL)
        
        print("Running database migrations...")
        
        # Migration 1: Add indexes for better performance
        await conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_forwarding_tasks_user_id 
            ON forwarding_tasks(user_id);
        ''')
        
        await conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_forwarding_tasks_source_chat 
            ON forwarding_tasks(source_chat_id);
        ''')
        
        await conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_statistics_task_id 
            ON statistics(task_id);
        ''')
        
        await conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_statistics_date 
            ON statistics(date);
        ''')
        
        print("✅ Indexes created successfully")
        
        # Migration 2: Add new columns if they don't exist
        try:
            await conn.execute('''
                ALTER TABLE forwarding_tasks 
                ADD COLUMN IF NOT EXISTS priority INTEGER DEFAULT 1;
            ''')
            print("✅ Priority column added")
        except Exception as e:
            print(f"Priority column already exists or error: {e}")
        
        try:
            await conn.execute('''
                ALTER TABLE users 
                ADD COLUMN IF NOT EXISTS subscription_type VARCHAR(20) DEFAULT 'free';
            ''')
            print("✅ Subscription type column added")
        except Exception as e:
            print(f"Subscription type column already exists or error: {e}")
        
        await conn.close()
        print("✅ Database migrations completed successfully")
        
    except Exception as e:
        print(f"❌ Error running migrations: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(migrate_database())
