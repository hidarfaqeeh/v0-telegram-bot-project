import asyncio
import asyncpg
from config import Config

async def setup_database():
    """Setup database and create initial admin user"""
    try:
        # Connect to database
        conn = await asyncpg.connect(Config.DATABASE_URL)
        
        print("✅ Connected to database successfully")
        
        # Create tables (this will be handled by DatabaseManager)
        from database.models import db
        await db.initialize()
        
        print("✅ Database tables created successfully")
        
        # Create initial admin user if specified
        if Config.ADMIN_USER_ID:
            await conn.execute('''
                INSERT INTO users (user_id, username, first_name, is_admin, is_active)
                VALUES ($1, 'admin', 'Admin', TRUE, TRUE)
                ON CONFLICT (user_id) DO UPDATE SET is_admin = TRUE
            ''', Config.ADMIN_USER_ID)
            
            print(f"✅ Admin user {Config.ADMIN_USER_ID} created/updated")
        
        await conn.close()
        print("✅ Database setup completed successfully")
        
    except Exception as e:
        print(f"❌ Error setting up database: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(setup_database())
