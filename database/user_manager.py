from typing import Optional, List, Dict, Any
from .models import db

class UserManager:
    @staticmethod
    async def create_or_update_user(user_id: int, username: str = None, 
                                  first_name: str = None, last_name: str = None) -> bool:
        """Create or update user in database"""
        try:
            async with db.pool.acquire() as conn:
                await conn.execute('''
                    INSERT INTO users (user_id, username, first_name, last_name, last_activity)
                    VALUES ($1, $2, $3, $4, CURRENT_TIMESTAMP)
                    ON CONFLICT (user_id) 
                    DO UPDATE SET 
                        username = EXCLUDED.username,
                        first_name = EXCLUDED.first_name,
                        last_name = EXCLUDED.last_name,
                        last_activity = CURRENT_TIMESTAMP
                ''', user_id, username, first_name, last_name)
                return True
        except Exception as e:
            print(f"Error creating/updating user: {e}")
            return False
    
    @staticmethod
    async def get_user(user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        try:
            async with db.pool.acquire() as conn:
                row = await conn.fetchrow(
                    'SELECT * FROM users WHERE user_id = $1', user_id
                )
                return dict(row) if row else None
        except Exception as e:
            print(f"Error getting user: {e}")
            return None
    
    @staticmethod
    async def set_admin(user_id: int, is_admin: bool = True) -> bool:
        """Set user admin status"""
        try:
            async with db.pool.acquire() as conn:
                await conn.execute(
                    'UPDATE users SET is_admin = $1 WHERE user_id = $2',
                    is_admin, user_id
                )
                return True
        except Exception as e:
            print(f"Error setting admin: {e}")
            return False
    
    @staticmethod
    async def is_admin(user_id: int) -> bool:
        """Check if user is admin"""
        try:
            async with db.pool.acquire() as conn:
                result = await conn.fetchval(
                    'SELECT is_admin FROM users WHERE user_id = $1', user_id
                )
                return result or False
        except Exception as e:
            print(f"Error checking admin: {e}")
            return False
    
    @staticmethod
    async def get_all_users() -> List[Dict[str, Any]]:
        """Get all users"""
        try:
            async with db.pool.acquire() as conn:
                rows = await conn.fetch('SELECT * FROM users ORDER BY created_at DESC')
                return [dict(row) for row in rows]
        except Exception as e:
            print(f"Error getting all users: {e}")
            return []
