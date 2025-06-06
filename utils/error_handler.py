import logging
from typing import Optional, Dict, Any
from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import TelegramError, BadRequest, Forbidden, NetworkError

logger = logging.getLogger(__name__)

class ErrorHandler:
    @staticmethod
    async def handle_telegram_error(update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                  error: TelegramError) -> bool:
        """معالجة أخطاء تلغرام"""
        error_msg = str(error).lower()
        
        if "chat not found" in error_msg:
            await ErrorHandler.send_error_message(
                update, "❌ المحادثة غير موجودة أو البوت غير مضاف إليها"
            )
            return True
            
        elif "bot was blocked" in error_msg:
            await ErrorHandler.send_error_message(
                update, "❌ تم حظر البوت من قبل المستخدم"
            )
            return True
            
        elif "not enough rights" in error_msg:
            await ErrorHandler.send_error_message(
                update, "❌ البوت لا يملك صلاحيات كافية في المحادثة"
            )
            return True
            
        elif "message too long" in error_msg:
            await ErrorHandler.send_error_message(
                update, "❌ الرسالة طويلة جداً"
            )
            return True
            
        elif "flood control" in error_msg or "too many requests" in error_msg:
            await ErrorHandler.send_error_message(
                update, "❌ تم إرسال رسائل كثيرة جداً. يرجى الانتظار قليلاً"
            )
            return True
        
        return False
    
    @staticmethod
    async def handle_database_error(operation: str, error: Exception) -> Dict[str, Any]:
        """معالجة أخطاء قاعدة البيانات"""
        error_msg = str(error).lower()
        
        if "connection" in error_msg:
            logger.error(f"Database connection error in {operation}: {error}")
            return {
                "success": False,
                "error": "خطأ في الاتصال بقاعدة البيانات",
                "retry": True
            }
            
        elif "unique violation" in error_msg:
            logger.warning(f"Unique constraint violation in {operation}: {error}")
            return {
                "success": False,
                "error": "البيانات موجودة مسبقاً",
                "retry": False
            }
            
        elif "foreign key" in error_msg:
            logger.error(f"Foreign key constraint in {operation}: {error}")
            return {
                "success": False,
                "error": "خطأ في ربط البيانات",
                "retry": False
            }
        
        else:
            logger.error(f"Unknown database error in {operation}: {error}")
            return {
                "success": False,
                "error": "خطأ غير معروف في قاعدة البيانات",
                "retry": True
            }
    
    @staticmethod
    async def send_error_message(update: Update, message: str):
        """إرسال رسالة خطأ للمستخدم"""
        try:
            if update.callback_query:
                await update.callback_query.answer(message, show_alert=True)
            elif update.message:
                await update.message.reply_text(message)
        except Exception as e:
            logger.error(f"Failed to send error message: {e}")
    
    @staticmethod
    async def log_error(update: Update, context: ContextTypes.DEFAULT_TYPE, 
                       error: Exception, operation: str = "Unknown"):
        """تسجيل الأخطاء مع تفاصيل السياق"""
        user_id = update.effective_user.id if update.effective_user else "Unknown"
        chat_id = update.effective_chat.id if update.effective_chat else "Unknown"
        
        logger.error(
            f"Error in {operation} - User: {user_id}, Chat: {chat_id}, Error: {error}",
            exc_info=True
        )
        
        # حفظ الخطأ في قاعدة البيانات للمراجعة
        await ErrorHandler.save_error_to_db(user_id, operation, str(error))
    
    @staticmethod
    async def save_error_to_db(user_id: int, operation: str, error_msg: str):
        """حفظ الخطأ في قاعدة البيانات"""
        try:
            from database.models import db
            async with db.pool.acquire() as conn:
                await conn.execute('''
                    INSERT INTO error_logs (user_id, operation, error_message, created_at)
                    VALUES ($1, $2, $3, CURRENT_TIMESTAMP)
                ''', user_id, operation, error_msg)
        except Exception as e:
            logger.error(f"Failed to save error to database: {e}")
    
    @staticmethod
    async def retry_operation(operation, max_retries: int = 3, delay: float = 1.0):
        """إعادة المحاولة التلقائية للعمليات"""
        import asyncio
        
        for attempt in range(max_retries):
            try:
                return await operation()
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                await asyncio.sleep(delay * (2 ** attempt))  # تأخير متزايد
        
        return None
