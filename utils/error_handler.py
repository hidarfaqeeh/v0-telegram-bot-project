from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

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
