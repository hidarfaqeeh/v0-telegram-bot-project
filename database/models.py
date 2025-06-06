import asyncpg
import json
from datetime import datetime
from typing import List, Dict, Optional, Any
from config import Config

class DatabaseManager:
    def __init__(self):
        self.pool = None
    
    async def initialize(self):
        """Initialize database connection pool"""
        self.pool = await asyncpg.create_pool(Config.DATABASE_URL)
        await self.create_tables()
    
    async def create_tables(self):
        """Create all necessary database tables"""
        async with self.pool.acquire() as conn:
            # حذف الجداول بالترتيب العكسي لتجنب مشاكل المفاتيح الخارجية
            await conn.execute('DROP TABLE IF EXISTS error_logs CASCADE;')
            await conn.execute('DROP TABLE IF EXISTS userbot_sessions CASCADE;')
            await conn.execute('DROP TABLE IF EXISTS statistics CASCADE;')
            await conn.execute('DROP TABLE IF EXISTS message_filters CASCADE;')
            await conn.execute('DROP TABLE IF EXISTS forwarding_tasks CASCADE;')
            await conn.execute('DROP TABLE IF EXISTS users CASCADE;')
        
            print("✅ Old tables dropped successfully")
        
            # إنشاء الجداول بالترتيب الصحيح
            # 1. Users table - يجب إنشاؤه أولاً
            await conn.execute('''
                CREATE TABLE users (
                    user_id BIGINT PRIMARY KEY,
                    username VARCHAR(255),
                    first_name VARCHAR(255),
                    last_name VARCHAR(255),
                    is_admin BOOLEAN DEFAULT FALSE,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            print("✅ Users table created")
        
            # 2. Forwarding tasks table - بعد إنشاء جدول users
            await conn.execute('''
                CREATE TABLE forwarding_tasks (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    task_name VARCHAR(255) NOT NULL,
                    source_chat_id BIGINT NOT NULL,
                    target_chat_id BIGINT NOT NULL,
                    task_type VARCHAR(20) DEFAULT 'forward',
                    is_active BOOLEAN DEFAULT TRUE,
                    settings JSONB DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                )
            ''')
            print("✅ Forwarding tasks table created")
        
            # 3. Message filters table - بعد إنشاء جدول forwarding_tasks
            await conn.execute('''
                CREATE TABLE message_filters (
                    id SERIAL PRIMARY KEY,
                    task_id INTEGER NOT NULL,
                    filter_type VARCHAR(50) NOT NULL,
                    filter_value TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (task_id) REFERENCES forwarding_tasks(id) ON DELETE CASCADE
                )
            ''')
            print("✅ Message filters table created")
        
            # 4. Statistics table - بعد إنشاء جدول forwarding_tasks
            await conn.execute('''
                CREATE TABLE statistics (
                    id SERIAL PRIMARY KEY,
                    task_id INTEGER NOT NULL,
                    messages_forwarded INTEGER DEFAULT 0,
                    messages_filtered INTEGER DEFAULT 0,
                    last_message_time TIMESTAMP,
                    date DATE DEFAULT CURRENT_DATE,
                    FOREIGN KEY (task_id) REFERENCES forwarding_tasks(id) ON DELETE CASCADE,
                    UNIQUE(task_id, date)
                )
            ''')
            print("✅ Statistics table created")
        
            # 5. Userbot sessions table - بعد إنشاء جدول users
            await conn.execute('''
                CREATE TABLE userbot_sessions (
                    user_id BIGINT PRIMARY KEY,
                    session_data BYTEA,
                    is_active BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                )
            ''')
            print("✅ Userbot sessions table created")

            # 6. Error logs table - مستقل، يمكن إنشاؤه في أي وقت
            await conn.execute('''
                CREATE TABLE error_logs (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT,
                    operation VARCHAR(100),
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            print("✅ Error logs table created")

            # إنشاء الفهارس
            await conn.execute('CREATE INDEX idx_forwarding_tasks_user_id ON forwarding_tasks(user_id);')
            await conn.execute('CREATE INDEX idx_forwarding_tasks_is_active ON forwarding_tasks(is_active);')
            await conn.execute('CREATE INDEX idx_message_filters_task_id ON message_filters(task_id);')
            await conn.execute('CREATE INDEX idx_statistics_task_id ON statistics(task_id);')
            await conn.execute('CREATE INDEX idx_statistics_date ON statistics(date);')
            await conn.execute('CREATE INDEX idx_error_logs_user_id ON error_logs(user_id);')
            await conn.execute('CREATE INDEX idx_error_logs_created_at ON error_logs(created_at);')
        
            print("✅ All indexes created successfully")
            print("✅ Database setup completed successfully")
    
    async def close(self):
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()

# Global database instance
db = DatabaseManager()
