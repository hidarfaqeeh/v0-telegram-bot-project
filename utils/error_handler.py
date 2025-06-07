import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.error import TelegramError, BadRequest, Forbidden, NetworkError, TimedOut, ChatMigrated

logger = logging.getLogger(__name__)

class ErrorHandler:
    @staticmethod
    async def handle_validation_error(update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                    error_message: str, suggested_action: str = None) -> bool:
        """معالجة أخطاء التحقق من البيانات"""
        try:
            user_friendly_message = f"❌ **خطأ في البيانات**\n\n{error_message}"
            
            if suggested_action:
                user_friendly_message += f"\n\n💡 **الحل المقترح:**\n{suggested_action}"
            
            keyboard = [[InlineKeyboardButton("🔙 العودة", callback_data="main_menu")]]
            
            if update.callback_query:
                await update.callback_query.edit_message_text(
                    user_friendly_message,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text(
                    user_friendly_message,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='Markdown'
                )
            
            return True
            
        except Exception as e:
            print(f"Error handling validation error: {e}")
            return False

    @staticmethod
    async def handle_database_error(update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                  operation: str) -> bool:
        """معالجة أخطاء قاعدة البيانات"""
        try:
            user_friendly_message = f"""
❌ **خطأ في قاعدة البيانات**

حدث خطأ أثناء {operation}.

💡 **الحلول المقترحة:**
• انتظر قليلاً ثم حاول مرة أخرى
• تأكد من اتصالك بالإنترنت
• إذا استمر الخطأ، تواصل مع المدير

🔄 **يمكنك المحاولة مرة أخرى الآن**
            """
            
            keyboard = [
                [InlineKeyboardButton("🔄 محاولة مرة أخرى", callback_data="main_menu")],
                [InlineKeyboardButton("📞 تواصل مع المدير", callback_data="contact_admin")]
            ]
            
            if update.callback_query:
                await update.callback_query.edit_message_text(
                    user_friendly_message,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text(
                    user_friendly_message,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='Markdown'
                )
            
            return True
            
        except Exception as e:
            print(f"Error handling database error: {e}")
            return False

    @staticmethod
    async def handle_permission_error(update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                    required_permission: str) -> bool:
        """معالجة أخطاء الصلاحيات"""
        try:
            user_friendly_message = f"""
🚫 **غير مصرح لك بهذه العملية**

تحتاج إلى صلاحية: **{required_permission}**

💡 **للحصول على الصلاحيات:**
• تواصل مع المدير الرئيسي
• تأكد من أن حسابك نشط وغير محظور

🏠 يمكنك العودة للقائمة الرئيسية واستخدام الميزات المتاحة لك.
            """
            
            keyboard = [
                [InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main_menu")],
                [InlineKeyboardButton("📞 تواصل مع المدير", callback_data="contact_admin")]
            ]
            
            if update.callback_query:
                await update.callback_query.edit_message_text(
                    user_friendly_message,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text(
                    user_friendly_message,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='Markdown'
                )
            
            return True
            
        except Exception as e:
            print(f"Error handling permission error: {e}")
            return False

    @staticmethod
    async def handle_system_overload(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """معالجة حمولة النظام الزائدة"""
        try:
            user_friendly_message = f"""
⚠️ **النظام مشغول حالياً**

النظام يعالج عدد كبير من الطلبات في الوقت الحالي.

💡 **يرجى:**
• الانتظار بضع دقائق
• تجنب إرسال طلبات متكررة
• المحاولة مرة أخرى لاحقاً

🔄 **سيعود النظام للعمل الطبيعي قريباً**
            """
            
            keyboard = [
                [InlineKeyboardButton("🔄 محاولة مرة أخرى", callback_data="main_menu")],
                [InlineKeyboardButton("📊 حالة النظام", callback_data="system_status")]
            ]
            
            if update.callback_query:
                await update.callback_query.edit_message_text(
                    user_friendly_message,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text(
                    user_friendly_message,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='Markdown'
                )
            
            return True
            
        except Exception as e:
            print(f"Error handling system overload: {e}")
            return False

    @staticmethod
    async def handle_telegram_error(update, context, error):
        """معالجة أخطاء تلغرام المحددة"""
        try:
            if isinstance(error, BadRequest):
                if "Message is not modified" in str(error):
                    return True  # تجاهل هذا الخطأ
                elif "Chat not found" in str(error):
                    await ErrorHandler.handle_chat_not_found(update, context)
                    return True
                elif "User not found" in str(error):
                    await ErrorHandler.handle_user_not_found(update, context)
                    return True
            
            elif isinstance(error, Forbidden):
                await ErrorHandler.handle_forbidden_error(update, context)
                return True
            
            elif isinstance(error, NetworkError):
                await ErrorHandler.handle_network_error(update, context)
                return True
            
            elif isinstance(error, TimedOut):
                await ErrorHandler.handle_timeout_error(update, context)
                return True
            
            elif isinstance(error, ChatMigrated):
                await ErrorHandler.handle_chat_migrated(update, context, error)
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error in telegram error handler: {e}")
            return False
    
    @staticmethod
    async def log_error(update, context, error, error_type="general"):
        """تسجيل الخطأ في قاعدة البيانات"""
        try:
            from database.models import db
            
            user_id = None
            if update and update.effective_user:
                user_id = update.effective_user.id
            
            error_data = {
                'user_id': user_id,
                'error_type': error_type,
                'error_message': str(error),
                'stack_trace': str(error.__traceback__) if hasattr(error, '__traceback__') else None,
                'update_data': str(update) if update else None,
                'context_data': str(context.user_data) if context and hasattr(context, 'user_data') else None,
                'timestamp': datetime.now()
            }
            
            async with db.pool.acquire() as conn:
                await conn.execute('''
                    INSERT INTO error_logs (user_id, error_type, error_message, stack_trace, context_data, created_at)
                    VALUES ($1, $2, $3, $4, $5, $6)
                ''', user_id, error_type, str(error), error_data['stack_trace'], 
                error_data['context_data'], error_data['timestamp'])
            
            logger.error(f"Error logged: {error_type} - {error}")
            
        except Exception as e:
            logger.error(f"Failed to log error to database: {e}")
    
    @staticmethod
    async def handle_chat_not_found(update, context):
        """معالجة خطأ عدم وجود المحادثة"""
        message = "❌ المحادثة غير موجودة أو لا يمكن الوصول إليها"
        await ErrorHandler.send_error_message(update, context, message)
    
    @staticmethod
    async def handle_user_not_found(update, context):
        """معالجة خطأ عدم وجود المستخدم"""
        message = "❌ المستخدم غير موجود أو لا يمكن الوصول إليه"
        await ErrorHandler.send_error_message(update, context, message)
    
    @staticmethod
    async def handle_forbidden_error(update, context):
        """معالجة خطأ عدم وجود صلاحيات"""
        message = "❌ البوت لا يملك الصلاحيات اللازمة لهذه العملية"
        await ErrorHandler.send_error_message(update, context, message)
    
    @staticmethod
    async def handle_network_error(update, context):
        """معالجة خطأ الشبكة"""
        message = "❌ خطأ في الاتصال. يرجى المحاولة مرة أخرى"
        await ErrorHandler.send_error_message(update, context, message)
    
    @staticmethod
    async def handle_timeout_error(update, context):
        """معالجة خطأ انتهاء المهلة"""
        message = "❌ انتهت مهلة الاتصال. يرجى المحاولة مرة أخرى"
        await ErrorHandler.send_error_message(update, context, message)
    
    @staticmethod
    async def handle_chat_migrated(update, context, error):
        """معالجة ترحيل المحادثة"""
        message = f"❌ تم ترحيل المحادثة إلى معرف جديد: {error.new_chat_id}"
        await ErrorHandler.send_error_message(update, context, message)
    
    @staticmethod
    async def send_error_message(update, context, message):
        """إرسال رسالة خطأ للمستخدم"""
        try:
            if update and update.effective_chat:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=message
                )
        except Exception as e:
            logger.error(f"Failed to send error message: {e}")
