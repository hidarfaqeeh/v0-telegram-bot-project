import asyncpg
from typing import Optional, List, Dict

class UserManager:
    """
    Manages user-related database operations.
    """

    @staticmethod
    async def create_user(user_id: int, username: str, first_name: str, last_name: str) -> bool:
        """Creates a new user in the database."""
        try:
            async with db.pool.acquire() as conn:
                await conn.execute('''
                    INSERT INTO users (user_id, username, first_name, last_name) 
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (user_id) DO NOTHING
                ''', user_id, username, first_name, last_name)
                return True
        except Exception as e:
            print(f"Error creating user: {e}")
            return False

    @staticmethod
    async def get_user(user_id: int) -> Optional[dict]:
        """Retrieves a user from the database by user ID."""
        try:
            async with db.pool.acquire() as conn:
                user = await conn.fetchrow('''
                    SELECT * FROM users WHERE user_id = $1
                ''', user_id)
                return dict(user) if user else None
        except Exception as e:
            print(f"Error getting user: {e}")
            return None

    @staticmethod
    async def update_user(user_id: int, username: str, first_name: str, last_name: str) -> bool:
        """Updates an existing user in the database."""
        try:
            async with db.pool.acquire() as conn:
                await conn.execute('''
                    UPDATE users 
                    SET username = $2, first_name = $3, last_name = $4, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = $1
                ''', user_id, username, first_name, last_name)
                return True
        except Exception as e:
            print(f"Error updating user: {e}")
            return False

    @staticmethod
    async def delete_user(user_id: int) -> bool:
        """Deletes a user from the database."""
        try:
            async with db.pool.acquire() as conn:
                await conn.execute('''
                    DELETE FROM users WHERE user_id = $1
                ''', user_id)
                return True
        except Exception as e:
            print(f"Error deleting user: {e}")
            return False

    @staticmethod
    async def get_all_users() -> List[dict]:
        """Retrieves all users from the database."""
        try:
            async with db.pool.acquire() as conn:
                users = await conn.fetch('''
                    SELECT * FROM users
                ''')
                return [dict(user) for user in users]
        except Exception as e:
            print(f"Error getting all users: {e}")
            return []

    @staticmethod
    async def increment_tasks_created(user_id: int) -> bool:
        """Increments the total_tasks_created count for a user."""
        try:
            async with db.pool.acquire() as conn:
                await conn.execute('''
                    UPDATE users 
                    SET total_tasks_created = total_tasks_created + 1
                    WHERE user_id = $1
                ''', user_id)
                return True
        except Exception as e:
            print(f"Error incrementing tasks created: {e}")
            return False

    @staticmethod
    async def increment_messages_forwarded(user_id: int) -> bool:
        """Increments the total_messages_forwarded count for a user."""
        try:
            async with db.pool.acquire() as conn:
                await conn.execute('''
                    UPDATE users 
                    SET total_messages_forwarded = total_messages_forwarded + 1
                    WHERE user_id = $1
                ''', user_id)
                return True
        except Exception as e:
            print(f"Error incrementing messages forwarded: {e}")
            return False

    @staticmethod
    async def update_user_from_backup(user_id: int, user_data: dict) -> bool:
        """تحديث بيانات المستخدم من النسخة الاحتياطية"""
        try:
            async with db.pool.acquire() as conn:
                await conn.execute('''
                    UPDATE users 
                    SET 
                        username = $2,
                        first_name = $3,
                        last_name = $4,
                        total_tasks_created = $5,
                        total_messages_forwarded = $6,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = $1
                ''', 
                    user_id,
                    user_data.get('username'),
                    user_data.get('first_name'),
                    user_data.get('last_name'),
                    user_data.get('total_tasks_created', 0),
                    user_data.get('total_messages_forwarded', 0)
                )
                return True
        except Exception as e:
            print(f"Error updating user from backup: {e}")
            return False
import database as db
