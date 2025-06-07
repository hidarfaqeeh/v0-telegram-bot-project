import asyncpg
import json
from datetime import datetime
from typing import List, Dict, Optional, Any
from config import Config
import logging

# Initialize logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

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
            # التحقق من وجود الجداول الأساسية أولاً
            try:
                # التحقق من وجود جدول المستخدمين
                users_exists = await conn.fetchval(
                    "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'users')"
                )
            
                if not users_exists:
                    logger.info("Creating users table")
                    await conn.execute('''
                        CREATE TABLE users (
                            user_id BIGINT PRIMARY KEY,
                            username VARCHAR(255),
                            first_name VARCHAR(255),
                            last_name VARCHAR(255),
                            is_admin BOOLEAN DEFAULT FALSE,
                            is_active BOOLEAN DEFAULT TRUE,
                            is_banned BOOLEAN DEFAULT FALSE,
                            ban_reason TEXT,
                            last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            subscription_type VARCHAR(20) DEFAULT 'free',
                            language_code VARCHAR(10) DEFAULT 'ar',
                            timezone VARCHAR(50) DEFAULT 'UTC',
                            total_tasks_created INTEGER DEFAULT 0,
                            total_messages_forwarded BIGINT DEFAULT 0
                        )
                    ''')
            
                # التحقق من وجود جدول المهام
                tasks_exists = await conn.fetchval(
                    "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'forwarding_tasks')"
                )
            
                if not tasks_exists:
                    logger.info("Creating forwarding_tasks table")
                    await conn.execute('''
                        CREATE TABLE forwarding_tasks (
                            id SERIAL PRIMARY KEY,
                            user_id BIGINT NOT NULL,
                            task_name VARCHAR(255) NOT NULL,
                            source_chat_id BIGINT NOT NULL,
                            target_chat_id BIGINT NOT NULL,
                            task_type VARCHAR(50) NOT NULL,
                            is_active BOOLEAN DEFAULT TRUE,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            description TEXT,
                            priority INTEGER DEFAULT 1,
                            last_message_time TIMESTAMP,
                            total_forwarded BIGINT DEFAULT 0,
                            total_filtered BIGINT DEFAULT 0,
                            error_count INTEGER DEFAULT 0,
                            success_rate DECIMAL(5,2) DEFAULT 0.00,
                            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                        )
                    ''')
            
                # التحقق من وجود جدول الإحصائيات
                stats_exists = await conn.fetchval(
                    "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'statistics')"
                )
            
                if not stats_exists:
                    logger.info("Creating statistics table")
                    await conn.execute('''
                        CREATE TABLE statistics (
                            id SERIAL PRIMARY KEY,
                            task_id INTEGER NOT NULL,
                            date DATE NOT NULL,
                            hour INTEGER DEFAULT EXTRACT(HOUR FROM CURRENT_TIMESTAMP),
                            messages_forwarded INTEGER DEFAULT 0,
                            messages_filtered INTEGER DEFAULT 0,
                            messages_failed INTEGER DEFAULT 0,
                            bytes_transferred BIGINT DEFAULT 0,
                            processing_time_ms INTEGER DEFAULT 0,
                            filter_breakdown JSONB DEFAULT '{}',
                            error_breakdown JSONB DEFAULT '{}',
                            FOREIGN KEY (task_id) REFERENCES forwarding_tasks(id) ON DELETE CASCADE,
                            CONSTRAINT statistics_task_id_date_hour_key UNIQUE(task_id, date, hour)
                        )
                    ''')
            
                # التحقق من وجود جدول سجلات الأخطاء
                error_logs_exists = await conn.fetchval(
                    "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'error_logs')"
                )
            
                if not error_logs_exists:
                    logger.info("Creating error_logs table")
                    await conn.execute('''
                        CREATE TABLE error_logs (
                            id SERIAL PRIMARY KEY,
                            user_id BIGINT,
                            error_type VARCHAR(50) DEFAULT 'general',
                            error_category VARCHAR(50) DEFAULT 'system',
                            error_message TEXT,
                            error_code VARCHAR(20),
                            stack_trace TEXT,
                            context_data JSONB,
                            severity VARCHAR(20) DEFAULT 'error',
                            is_resolved BOOLEAN DEFAULT FALSE,
                            resolved_at TIMESTAMP,
                            resolved_by BIGINT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            task_id INTEGER,
                            session_id INTEGER
                        )
                    ''')
            
                # التحقق من وجود جدول جلسات Userbot
                userbot_sessions_exists = await conn.fetchval(
                    "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'userbot_sessions')"
                )
            
                if not userbot_sessions_exists:
                    logger.info("Creating userbot_sessions table")
                    await conn.execute('''
                        CREATE TABLE userbot_sessions (
                            user_id BIGINT PRIMARY KEY,
                            session_data BYTEA NOT NULL,
                            is_active BOOLEAN DEFAULT TRUE,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            api_id INTEGER,
                            api_hash VARCHAR(255),
                            phone_number VARCHAR(20),
                            last_connected TIMESTAMP,
                            connection_errors INTEGER DEFAULT 0,
                            session_info JSONB DEFAULT '{}',
                            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                        )
                    ''')
            
                logger.info("Basic tables checked/created")
            
            except Exception as e:
                logger.error(f"Error creating basic tables: {e}")
                raise
        
            # الآن نقوم بتحسين الجداول الموجودة وإنشاء الجداول الجديدة
            try:
                # 1. تحسين جدول Users الحالي (إضافة حقول جديدة فقط)
                try:
                    await conn.execute('''
                        ALTER TABLE users ADD COLUMN IF NOT EXISTS subscription_type VARCHAR(20) DEFAULT 'free';
                    ''')
                    await conn.execute('''
                        ALTER TABLE users ADD COLUMN IF NOT EXISTS language_code VARCHAR(10) DEFAULT 'ar';
                    ''')
                    await conn.execute('''
                        ALTER TABLE users ADD COLUMN IF NOT EXISTS timezone VARCHAR(50) DEFAULT 'UTC';
                    ''')
                    await conn.execute('''
                        ALTER TABLE users ADD COLUMN IF NOT EXISTS total_tasks_created INTEGER DEFAULT 0;
                    ''')
                    await conn.execute('''
                        ALTER TABLE users ADD COLUMN IF NOT EXISTS total_messages_forwarded BIGINT DEFAULT 0;
                    ''')
                    logger.info("✅ Users table enhanced")
                except Exception as e:
                    logger.warning(f"Users table already enhanced or error: {e}")
        
                # 2. إنشاء جدول إعدادات المستخدمين (جديد)
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS user_settings (
                        user_id BIGINT PRIMARY KEY,
                        notifications_enabled BOOLEAN DEFAULT TRUE,
                        task_notifications BOOLEAN DEFAULT TRUE,
                        error_notifications BOOLEAN DEFAULT TRUE,
                        stats_notifications BOOLEAN DEFAULT FALSE,
                        system_notifications BOOLEAN DEFAULT TRUE,
                        dark_mode BOOLEAN DEFAULT FALSE,
                        auto_backup BOOLEAN DEFAULT FALSE,
                        backup_frequency VARCHAR(20) DEFAULT 'weekly',
                        chart_type VARCHAR(20) DEFAULT 'bar',
                        stats_period INTEGER DEFAULT 7,
                        ui_language VARCHAR(10) DEFAULT 'ar',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                    )
                ''')
                logger.info("✅ User settings table created")
        
                # 3. إنشاء جدول الجلسات النشطة (جديد)
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS active_sessions (
                        id SERIAL PRIMARY KEY,
                        user_id BIGINT NOT NULL,
                        session_token VARCHAR(255) UNIQUE NOT NULL,
                        device_info JSONB,
                        ip_address INET,
                        user_agent TEXT,
                        is_active BOOLEAN DEFAULT TRUE,
                        last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        expires_at TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                    )
                ''')
                logger.info("✅ Active sessions table created")
        
                # 4. تحسين جدول المهام الحالي (إضافة حقول جديدة فقط)
                try:
                    await conn.execute('''
                        ALTER TABLE forwarding_tasks ADD COLUMN IF NOT EXISTS description TEXT;
                    ''')
                    await conn.execute('''
                        ALTER TABLE forwarding_tasks ADD COLUMN IF NOT EXISTS priority INTEGER DEFAULT 1;
                    ''')
                    await conn.execute('''
                        ALTER TABLE forwarding_tasks ADD COLUMN IF NOT EXISTS last_message_time TIMESTAMP;
                    ''')
                    await conn.execute('''
                        ALTER TABLE forwarding_tasks ADD COLUMN IF NOT EXISTS total_forwarded BIGINT DEFAULT 0;
                    ''')
                    await conn.execute('''
                        ALTER TABLE forwarding_tasks ADD COLUMN IF NOT EXISTS total_filtered BIGINT DEFAULT 0;
                    ''')
                    await conn.execute('''
                        ALTER TABLE forwarding_tasks ADD COLUMN IF NOT EXISTS error_count INTEGER DEFAULT 0;
                    ''')
                    await conn.execute('''
                        ALTER TABLE forwarding_tasks ADD COLUMN IF NOT EXISTS success_rate DECIMAL(5,2) DEFAULT 0.00;
                    ''')
                    logger.info("✅ Forwarding tasks table enhanced")
                except Exception as e:
                    logger.warning(f"Forwarding tasks table already enhanced or error: {e}")
        
                # 5. تحسين جدول الفلاتر الحالي (إعادة تسمية وتحسين)
                try:
                    # إعادة تسمية الجدول إذا كان موجوداً
                    await conn.execute('''
                        ALTER TABLE message_filters RENAME TO task_filters;
                    ''')
                    logger.info("✅ Message filters table renamed to task_filters")
                except:
                    # إنشاء جدول جديد إذا لم يكن موجوداً
                    await conn.execute('''
                        CREATE TABLE IF NOT EXISTS task_filters (
                            id SERIAL PRIMARY KEY,
                            task_id INTEGER NOT NULL,
                            filter_category VARCHAR(50) NOT NULL,
                            filter_type VARCHAR(50) NOT NULL,
                            filter_value TEXT,
                            filter_config JSONB DEFAULT '{}',
                            is_active BOOLEAN DEFAULT TRUE,
                            priority INTEGER DEFAULT 1,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (task_id) REFERENCES forwarding_tasks(id) ON DELETE CASCADE
                        )
                    ''')
                    logger.info("✅ Task filters table created")
            
                # إضافة حقول جديدة لجدول الفلاتر
                try:
                    await conn.execute('''
                        ALTER TABLE task_filters ADD COLUMN IF NOT EXISTS filter_category VARCHAR(50) DEFAULT 'text';
                    ''')
                    await conn.execute('''
                        ALTER TABLE task_filters ADD COLUMN IF NOT EXISTS filter_config JSONB DEFAULT '{}';
                    ''')
                    await conn.execute('''
                        ALTER TABLE task_filters ADD COLUMN IF NOT EXISTS priority INTEGER DEFAULT 1;
                    ''')
                    await conn.execute('''
                        ALTER TABLE task_filters ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
                    ''')
                    logger.info("✅ Task filters table enhanced")
                except Exception as e:
                    logger.warning(f"Task filters already enhanced or error: {e}")
        
                # 6. تحسين جدول الإحصائيات الحالي
                try:
                    await conn.execute('''
                        ALTER TABLE statistics ADD COLUMN IF NOT EXISTS hour INTEGER DEFAULT EXTRACT(HOUR FROM CURRENT_TIMESTAMP);
                    ''')
                    await conn.execute('''
                        ALTER TABLE statistics ADD COLUMN IF NOT EXISTS messages_failed INTEGER DEFAULT 0;
                    ''')
                    await conn.execute('''
                        ALTER TABLE statistics ADD COLUMN IF NOT EXISTS bytes_transferred BIGINT DEFAULT 0;
                    ''')
                    await conn.execute('''
                        ALTER TABLE statistics ADD COLUMN IF NOT EXISTS processing_time_ms INTEGER DEFAULT 0;
                    ''')
                    await conn.execute('''
                        ALTER TABLE statistics ADD COLUMN IF NOT EXISTS filter_breakdown JSONB DEFAULT '{}';
                    ''')
                    await conn.execute('''
                        ALTER TABLE statistics ADD COLUMN IF NOT EXISTS error_breakdown JSONB DEFAULT '{}';
                    ''')
                
                    # تحديث القيد الفريد ليشمل الساعة
                    await conn.execute('''
                        ALTER TABLE statistics DROP CONSTRAINT IF EXISTS statistics_task_id_date_key;
                    ''')
                    await conn.execute('''
                        ALTER TABLE statistics ADD CONSTRAINT statistics_task_id_date_hour_key 
                        UNIQUE(task_id, date, hour);
                    ''')
                    logger.info("✅ Statistics table enhanced")
                except Exception as e:
                    logger.warning(f"Statistics table already enhanced or error: {e}")
        
                # 7. تحسين جدول جلسات Userbot الحالي
                try:
                    await conn.execute('''
                        ALTER TABLE userbot_sessions ADD COLUMN IF NOT EXISTS api_id INTEGER;
                    ''')
                    await conn.execute('''
                        ALTER TABLE userbot_sessions ADD COLUMN IF NOT EXISTS api_hash VARCHAR(255);
                    ''')
                    await conn.execute('''
                        ALTER TABLE userbot_sessions ADD COLUMN IF NOT EXISTS phone_number VARCHAR(20);
                    ''')
                    await conn.execute('''
                        ALTER TABLE userbot_sessions ADD COLUMN IF NOT EXISTS last_connected TIMESTAMP;
                    ''')
                    await conn.execute('''
                        ALTER TABLE userbot_sessions ADD COLUMN IF NOT EXISTS connection_errors INTEGER DEFAULT 0;
                    ''')
                    await conn.execute('''
                        ALTER TABLE userbot_sessions ADD COLUMN IF NOT EXISTS session_info JSONB DEFAULT '{}';
                    ''')
                    logger.info("✅ Userbot sessions table enhanced")
                except Exception as e:
                    logger.warning(f"Userbot sessions already enhanced or error: {e}")

                # 8. إنشاء جدول الإشعارات (جديد)
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS notifications (
                        id SERIAL PRIMARY KEY,
                        user_id BIGINT,
                        notification_type VARCHAR(50) NOT NULL,
                        title VARCHAR(255) NOT NULL,
                        message TEXT NOT NULL,
                        data JSONB DEFAULT '{}',
                        is_read BOOLEAN DEFAULT FALSE,
                        is_sent BOOLEAN DEFAULT FALSE,
                        priority INTEGER DEFAULT 1,
                        scheduled_at TIMESTAMP,
                        sent_at TIMESTAMP,
                        expires_at TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                    )
                ''')
                logger.info("✅ Notifications table created")

                # 9. إنشاء جدول النسخ الاحتياطية (جديد)
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS backup_files (
                        id SERIAL PRIMARY KEY,
                        user_id BIGINT NOT NULL,
                        backup_name VARCHAR(255) NOT NULL,
                        backup_type VARCHAR(50) DEFAULT 'manual',
                        file_path TEXT,
                        file_size BIGINT,
                        backup_data JSONB,
                        compression_type VARCHAR(20) DEFAULT 'gzip',
                        checksum VARCHAR(255),
                        is_encrypted BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        expires_at TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                    )
                ''')
                logger.info("✅ Backup files table created")

                # 10. إنشاء جدول سجل الأنشطة (جديد)
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS activity_logs (
                        id SERIAL PRIMARY KEY,
                        user_id BIGINT,
                        session_id INTEGER,
                        activity_type VARCHAR(50) NOT NULL,
                        activity_category VARCHAR(50) NOT NULL,
                        description TEXT,
                        target_type VARCHAR(50),
                        target_id INTEGER,
                        old_values JSONB,
                        new_values JSONB,
                        ip_address INET,
                        user_agent TEXT,
                        success BOOLEAN DEFAULT TRUE,
                        error_message TEXT,
                        processing_time_ms INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL,
                        FOREIGN KEY (session_id) REFERENCES active_sessions(id) ON DELETE SET NULL
                    )
                ''')
                logger.info("✅ Activity logs table created")

                # 11. تحسين جدول سجلات الأخطاء الحالي
                try:
                    await conn.execute('''
                        ALTER TABLE error_logs ADD COLUMN IF NOT EXISTS task_id INTEGER;
                    ''')
                    await conn.execute('''
                        ALTER TABLE error_logs ADD COLUMN IF NOT EXISTS session_id INTEGER;
                    ''')
                    await conn.execute('''
                        ALTER TABLE error_logs ADD COLUMN IF NOT EXISTS error_type VARCHAR(50) DEFAULT 'general';
                    ''')
                    await conn.execute('''
                        ALTER TABLE error_logs ADD COLUMN IF NOT EXISTS error_category VARCHAR(50) DEFAULT 'system';
                    ''')
                    await conn.execute('''
                        ALTER TABLE error_logs ADD COLUMN IF NOT EXISTS error_code VARCHAR(20);
                    ''')
                    await conn.execute('''
                        ALTER TABLE error_logs ADD COLUMN IF NOT EXISTS stack_trace TEXT;
                    ''')
                    await conn.execute('''
                        ALTER TABLE error_logs ADD COLUMN IF NOT EXISTS context_data JSONB;
                    ''')
                    await conn.execute('''
                        ALTER TABLE error_logs ADD COLUMN IF NOT EXISTS severity VARCHAR(20) DEFAULT 'error';
                    ''')
                    await conn.execute('''
                        ALTER TABLE error_logs ADD COLUMN IF NOT EXISTS is_resolved BOOLEAN DEFAULT FALSE;
                    ''')
                    await conn.execute('''
                        ALTER TABLE error_logs ADD COLUMN IF NOT EXISTS resolved_at TIMESTAMP;
                    ''')
                    await conn.execute('''
                        ALTER TABLE error_logs ADD COLUMN IF NOT EXISTS resolved_by BIGINT;
                    ''')
                
                    # إضافة المفاتيح الخارجية الجديدة
                    await conn.execute('''
                        ALTER TABLE error_logs ADD CONSTRAINT IF NOT EXISTS fk_error_logs_task_id 
                        FOREIGN KEY (task_id) REFERENCES forwarding_tasks(id) ON DELETE SET NULL;
                    ''')
                    await conn.execute('''
                        ALTER TABLE error_logs ADD CONSTRAINT IF NOT EXISTS fk_error_logs_session_id 
                        FOREIGN KEY (session_id) REFERENCES active_sessions(id) ON DELETE SET NULL;
                    ''')
                    logger.info("✅ Error logs table enhanced")
                except Exception as e:
                    logger.warning(f"Error logs already enhanced or error: {e}")

                # إنشاء الفهارس المحسّنة (فقط إذا لم تكن موجودة)
                indexes = [
                    # Users indexes
                    'CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active) WHERE is_active = TRUE;',
                    'CREATE INDEX IF NOT EXISTS idx_users_is_admin ON users(is_admin) WHERE is_admin = TRUE;',
                    'CREATE INDEX IF NOT EXISTS idx_users_last_activity ON users(last_activity);',
                    'CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);',
                
                    # User settings indexes
                    'CREATE INDEX IF NOT EXISTS idx_user_settings_notifications ON user_settings(notifications_enabled);',
                
                    # Active sessions indexes
                    'CREATE INDEX IF NOT EXISTS idx_active_sessions_user_id ON active_sessions(user_id);',
                    'CREATE INDEX IF NOT EXISTS idx_active_sessions_is_active ON active_sessions(is_active) WHERE is_active = TRUE;',
                    'CREATE INDEX IF NOT EXISTS idx_active_sessions_expires_at ON active_sessions(expires_at);',
                
                    # Forwarding tasks indexes
                    'CREATE INDEX IF NOT EXISTS idx_forwarding_tasks_user_id ON forwarding_tasks(user_id);',
                    'CREATE INDEX IF NOT EXISTS idx_forwarding_tasks_is_active ON forwarding_tasks(is_active) WHERE is_active = TRUE;',
                    'CREATE INDEX IF NOT EXISTS idx_forwarding_tasks_source_chat ON forwarding_tasks(source_chat_id);',
                    'CREATE INDEX IF NOT EXISTS idx_forwarding_tasks_target_chat ON forwarding_tasks(target_chat_id);',
                    'CREATE INDEX IF NOT EXISTS idx_forwarding_tasks_priority ON forwarding_tasks(priority);',
                    'CREATE INDEX IF NOT EXISTS idx_forwarding_tasks_updated_at ON forwarding_tasks(updated_at);',
                
                    # Task filters indexes
                    'CREATE INDEX IF NOT EXISTS idx_task_filters_task_id ON task_filters(task_id);',
                    'CREATE INDEX IF NOT EXISTS idx_task_filters_category ON task_filters(filter_category);',
                    'CREATE INDEX IF NOT EXISTS idx_task_filters_type ON task_filters(filter_type);',
                    'CREATE INDEX IF NOT EXISTS idx_task_filters_is_active ON task_filters(is_active) WHERE is_active = TRUE;',
                
                    # Statistics indexes
                    'CREATE INDEX IF NOT EXISTS idx_statistics_task_id ON statistics(task_id);',
                    'CREATE INDEX IF NOT EXISTS idx_statistics_date ON statistics(date);',
                    'CREATE INDEX IF NOT EXISTS idx_statistics_task_date ON statistics(task_id, date);',
                    'CREATE INDEX IF NOT EXISTS idx_statistics_hour ON statistics(date, hour);',
                
                    # Userbot sessions indexes
                    'CREATE INDEX IF NOT EXISTS idx_userbot_sessions_is_active ON userbot_sessions(is_active) WHERE is_active = TRUE;',
                    'CREATE INDEX IF NOT EXISTS idx_userbot_sessions_last_connected ON userbot_sessions(last_connected);',
                
                    # Notifications indexes
                    'CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);',
                    'CREATE INDEX IF NOT EXISTS idx_notifications_type ON notifications(notification_type);',
                    'CREATE INDEX IF NOT EXISTS idx_notifications_is_read ON notifications(is_read) WHERE is_read = FALSE;',
                    'CREATE INDEX IF NOT EXISTS idx_notifications_is_sent ON notifications(is_sent);',
                    'CREATE INDEX IF NOT EXISTS idx_notifications_scheduled_at ON notifications(scheduled_at);',
                    'CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON notifications(created_at);',
                
                    # Backup files indexes
                    'CREATE INDEX IF NOT EXISTS idx_backup_files_user_id ON backup_files(user_id);',
                    'CREATE INDEX IF NOT EXISTS idx_backup_files_type ON backup_files(backup_type);',
                    'CREATE INDEX IF NOT EXISTS idx_backup_files_created_at ON backup_files(created_at);',
                    'CREATE INDEX IF NOT EXISTS idx_backup_files_expires_at ON backup_files(expires_at);',
                
                    # Activity logs indexes
                    'CREATE INDEX IF NOT EXISTS idx_activity_logs_user_id ON activity_logs(user_id);',
                    'CREATE INDEX IF NOT EXISTS idx_activity_logs_type ON activity_logs(activity_type);',
                    'CREATE INDEX IF NOT EXISTS idx_activity_logs_category ON activity_logs(activity_category);',
                    'CREATE INDEX IF NOT EXISTS idx_activity_logs_created_at ON activity_logs(created_at);',
                    'CREATE INDEX IF NOT EXISTS idx_activity_logs_success ON activity_logs(success);',
                
                    # Error logs indexes
                    'CREATE INDEX IF NOT EXISTS idx_error_logs_user_id ON error_logs(user_id);',
                    'CREATE INDEX IF NOT EXISTS idx_error_logs_task_id ON error_logs(task_id);',
                    'CREATE INDEX IF NOT EXISTS idx_error_logs_type ON error_logs(error_type);',
                    'CREATE INDEX IF NOT EXISTS idx_error_logs_category ON error_logs(error_category);',
                    'CREATE INDEX IF NOT EXISTS idx_error_logs_severity ON error_logs(severity);',
                    'CREATE INDEX IF NOT EXISTS idx_error_logs_is_resolved ON error_logs(is_resolved) WHERE is_resolved = FALSE;',
                    'CREATE INDEX IF NOT EXISTS idx_error_logs_created_at ON error_logs(created_at);'
                ]
            
                for index_sql in indexes:
                    try:
                        await conn.execute(index_sql)
                    except Exception as e:
                        logger.warning(f"Index already exists or error: {e}")
        
                logger.info("✅ All indexes created/updated successfully")
                logger.info("✅ Database enhancement completed successfully - All existing functionality preserved!")
            
            except Exception as e:
                logger.error(f"Error during database enhancement: {e}")
                raise
    
    async def close(self):
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()

# Global database instance
db = DatabaseManager()
