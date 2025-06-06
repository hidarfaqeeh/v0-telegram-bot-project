"""
Userbot Handlers - معالجات Userbot
معالجات شاملة لإعداد وإدارة Userbot مع التحقق من الإدخال وحفظ البيانات
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from telethon import TelegramClient
from telethon.errors import (
    ApiIdInvalidError, 
    PhoneNumberInvalidError,
    PhoneCodeInvalidError,
    SessionPasswordNeededError,
    PhoneCodeExpiredError
)

from utils.validators import InputValidator
from utils.decorators import admin_required, error_handler

logger = logging.getLogger(__name__)

# حالات المحادثة
USERBOT_API_ID, USERBOT_API_HASH, USERBOT_PHONE, USERBOT_CODE, USERBOT_PASSWORD = range(5)

class UserbotHandlers:
    """معالجات Userbot"""
    
    # مديرين قاعدة البيانات
    db_manager = None
    task_manager = None
    user_manager = None
    settings_manager = None
    activity_manager = None
    
    @classmethod
    def set_managers(cls, db_manager, task_manager, user_manager, settings_manager, activity_manager):
        """تعيين مديرين قاعدة البيانات"""
        cls.db_manager = db_manager
        cls.task_manager = task_manager
        cls.user_manager = user_manager
        cls.settings_manager = settings_manager
        cls.activity_manager = activity_manager
    
    @staticmethod
    @admin_required
    @error_handler
    async def userbot_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """عرض قائمة Userbot"""
        try:
            query = update.callback_query
            await query.answer()
            
            # الحصول على حالة Userbot
            userbot_settings = await UserbotHandlers.settings_manager.get_userbot_settings()
            
            if userbot_settings and userbot_settings.get('is_connected', False):
                status_text = "🟢 متصل"
                connect_button_text = "🔄 إعادة الاتصال"
                disconnect_button = InlineKeyboardButton("🔴 قطع الاتصال", callback_data="userbot_disconnect")
            else:
                status_text = "🔴 غير متصل"
                connect_button_text = "🔗 الاتصال"
                disconnect_button = None
            
            text = f"""
🤖 **إدارة Userbot**

**الحالة الحالية:** {status_text}

Userbot يسمح للبوت بالوصول إلى المحادثات الخاصة والمجموعات التي لا يمكن للبوت العادي الوصول إليها.

**المميزات:**
• الوصول للمحادثات الخاصة
• إعادة توجيه من المجموعات المقيدة
• سرعة أكبر في المعالجة
• إمكانيات متقدمة

⚠️ **تنبيه:** استخدم بيانات حسابك الشخصي بحذر
            """
            
            keyboard = []
            
            # أزرار الاتصال
            keyboard.append([InlineKeyboardButton(connect_button_text, callback_data="userbot_connect_start")])
            
            if disconnect_button:
                keyboard.append([disconnect_button])
            
            # أزرار المعلومات
            keyboard.extend([
                [InlineKeyboardButton("📊 حالة الاتصال", callback_data="userbot_status")],
                [InlineKeyboardButton("📋 سجل الأنشطة", callback_data="userbot_activity_log")],
                [InlineKeyboardButton("⚙️ إعدادات متقدمة", callback_data="userbot_advanced_settings")],
                [InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="main_menu")]
            ])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"خطأ في عرض قائمة Userbot: {e}")
            await query.edit_message_text("❌ حدث خطأ في عرض قائمة Userbot")
    
    @staticmethod
    @admin_required
    @error_handler
    async def userbot_connect_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """بدء عملية اتصال Userbot"""
        try:
            query = update.callback_query
            await query.answer()
            
            # تسجيل النشاط
            await UserbotHandlers.activity_manager.log_activity(
                user_id=update.effective_user.id,
                action="userbot_connect_start",
                details="بدء عملية اتصال Userbot"
            )
            
            text = """
🔗 **اتصال Userbot**

لاتصال Userbot، نحتاج إلى بيانات API الخاصة بك من Telegram.

**الخطوة 1: الحصول على API ID و API Hash**

1. اذهب إلى: https://my.telegram.org
2. سجل الدخول برقم هاتفك
3. اذهب إلى "API Development Tools"
4. أنشئ تطبيق جديد
5. احصل على API ID و API Hash

**يرجى إدخال API ID الآن:**

⚠️ **تنبيه:** API ID هو رقم مكون من 7-8 أرقام
            """
            
            keyboard = [[InlineKeyboardButton("❌ إلغاء", callback_data="userbot_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
            
            return USERBOT_API_ID
            
        except Exception as e:
            logger.error(f"خطأ في بدء اتصال Userbot: {e}")
            await query.edit_message_text("❌ حدث خطأ في بدء عملية الاتصال")
            return ConversationHandler.END
    
    @staticmethod
    @error_handler
    async def userbot_api_id_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """استقبال API ID"""
        try:
            api_id_str = update.message.text.strip()
            
            # التحقق من صحة API ID
            is_valid, api_id, message = InputValidator.validate_api_id(api_id_str)
            
            if not is_valid:
                await update.message.reply_text(
                    f"{message}\n\n🔄 يرجى إدخال API ID صحيح:",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("❌ إلغاء", callback_data="userbot_menu")
                    ]])
                )
                return USERBOT_API_ID
            
            # حفظ API ID
            context.user_data['userbot_api_id'] = api_id
            
            # تسجيل النشاط
            await UserbotHandlers.activity_manager.log_activity(
                user_id=update.effective_user.id,
                action="userbot_api_id_entered",
                details=f"تم إدخال API ID: {api_id}"
            )
            
            text = f"""
✅ {message}

**الخطوة 2: إدخال API Hash**

يرجى إدخال API Hash الآن:

⚠️ **تنبيه:** API Hash هو نص مكون من 32 حرف (أحرف وأرقام)
            """
            
            keyboard = [[InlineKeyboardButton("❌ إلغاء", callback_data="userbot_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
            
            return USERBOT_API_HASH
            
        except Exception as e:
            logger.error(f"خطأ في استقبال API ID: {e}")
            await update.message.reply_text("❌ حدث خطأ في معالجة API ID")
            return ConversationHandler.END
    
    @staticmethod
    @error_handler
    async def userbot_api_hash_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """استقبال API Hash"""
        try:
            api_hash = update.message.text.strip()
            
            # التحقق من صحة API Hash
            is_valid, message = InputValidator.validate_api_hash(api_hash)
            
            if not is_valid:
                await update.message.reply_text(
                    f"{message}\n\n🔄 يرجى إدخال API Hash صحيح:",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("❌ إلغاء", callback_data="userbot_menu")
                    ]])
                )
                return USERBOT_API_HASH
            
            # حفظ API Hash
            context.user_data['userbot_api_hash'] = api_hash
            
            # التحقق من بيانات API مع تلغرام
            api_id = context.user_data.get('userbot_api_id')
            
            await update.message.reply_text("🔄 جاري التحقق من بيانات API...")
            
            is_valid_api, api_message = await InputValidator.validate_api_credentials_with_telegram(api_id, api_hash)
            
            if not is_valid_api:
                await update.message.reply_text(
                    f"{api_message}\n\n🔄 يرجى التحقق من البيانات والمحاولة مرة أخرى:",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 العودة لـ API ID", callback_data="userbot_connect_start"),
                        InlineKeyboardButton("❌ إلغاء", callback_data="userbot_menu")
                    ]])
                )
                return USERBOT_API_HASH
            
            # تسجيل النشاط
            await UserbotHandlers.activity_manager.log_activity(
                user_id=update.effective_user.id,
                action="userbot_api_hash_entered",
                details="تم إدخال API Hash وتم التحقق من صحة البيانات"
            )
            
            text = f"""
✅ {api_message}

**الخطوة 3: إدخال رقم الهاتف**

يرجى إدخال رقم الهاتف المرتبط بحساب Telegram:

⚠️ **تنبيه:** 
• يجب أن يكون بالصيغة الدولية (مثال: +1234567890)
• هذا هو رقم حسابك الشخصي في Telegram
            """
            
            keyboard = [[InlineKeyboardButton("❌ إلغاء", callback_data="userbot_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
            
            return USERBOT_PHONE
            
        except Exception as e:
            logger.error(f"خطأ في استقبال API Hash: {e}")
            await update.message.reply_text("❌ حدث خطأ في معالجة API Hash")
            return ConversationHandler.END
    
    @staticmethod
    @error_handler
    async def userbot_phone_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """استقبال رقم الهاتف"""
        try:
            phone_str = update.message.text.strip()
            
            # التحقق من صحة رقم الهاتف
            is_valid, phone, message = InputValidator.validate_phone_number(phone_str)
            
            if not is_valid:
                await update.message.reply_text(
                    f"{message}\n\n🔄 يرجى إدخال رقم هاتف صحيح:",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("❌ إلغاء", callback_data="userbot_menu")
                    ]])
                )
                return USERBOT_PHONE
            
            # حفظ رقم الهاتف
            context.user_data['userbot_phone'] = phone
            
            # إرسال كود التحقق
            api_id = context.user_data.get('userbot_api_id')
            api_hash = context.user_data.get('userbot_api_hash')
            
            try:
                await update.message.reply_text("📱 جاري إرسال كود التحقق...")
                
                # إنشاء عميل Telegram
                client = TelegramClient('userbot_session', api_id, api_hash)
                await client.connect()
                
                # إرسال كود التحقق
                sent_code = await client.send_code_request(phone)
                context.user_data['userbot_client'] = client
                context.user_data['userbot_phone_code_hash'] = sent_code.phone_code_hash
                
                # تسجيل النشاط
                await UserbotHandlers.activity_manager.log_activity(
                    user_id=update.effective_user.id,
                    action="userbot_phone_entered",
                    details=f"تم إدخال رقم الهاتف وإرسال كود التحقق: {phone}"
                )
                
                text = f"""
✅ تم إرسال كود التحقق إلى: {phone}

**الخطوة 4: إدخال كود التحقق**

يرجى إدخال الكود المكون من 5 أرقام الذي وصلك عبر Telegram:

⚠️ **تنبيه:** 
• الكود صالح لمدة محدودة
• إذا لم يصلك الكود، تحقق من رقم الهاتف
                """
                
                keyboard = [
                    [InlineKeyboardButton("🔄 إعادة إرسال الكود", callback_data="userbot_resend_code")],
                    [InlineKeyboardButton("❌ إلغاء", callback_data="userbot_menu")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
                
                return USERBOT_CODE
                
            except PhoneNumberInvalidError:
                await update.message.reply_text(
                    "❌ رقم الهاتف غير صحيح أو غير مسجل في Telegram\n\n🔄 يرجى إدخال رقم هاتف صحيح:",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("❌ إلغاء", callback_data="userbot_menu")
                    ]])
                )
                return USERBOT_PHONE
                
            except Exception as e:
                logger.error(f"خطأ في إرسال كود التحقق: {e}")
                await update.message.reply_text(
                    f"❌ خطأ في إرسال كود التحقق: {str(e)}\n\n🔄 يرجى المحاولة مرة أخرى:",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("❌ إلغاء", callback_data="userbot_menu")
                    ]])
                )
                return USERBOT_PHONE
            
        except Exception as e:
            logger.error(f"خطأ في استقبال رقم الهاتف: {e}")
            await update.message.reply_text("❌ حدث خطأ في معالجة رقم الهاتف")
            return ConversationHandler.END
    
    @staticmethod
    @error_handler
    async def userbot_code_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """استقبال كود التحقق"""
        try:
            code_str = update.message.text.strip()
            
            # التحقق من صحة كود التحقق
            is_valid, code, message = InputValidator.validate_verification_code(code_str)
            
            if not is_valid:
                await update.message.reply_text(
                    f"{message}\n\n🔄 يرجى إدخال كود التحقق الصحيح:",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔄 إعادة إرسال الكود", callback_data="userbot_resend_code")],
                        [InlineKeyboardButton("❌ إلغاء", callback_data="userbot_menu")]
                    ])
                )
                return USERBOT_CODE
            
            # محاولة تسجيل الدخول
            client = context.user_data.get('userbot_client')
            phone = context.user_data.get('userbot_phone')
            phone_code_hash = context.user_data.get('userbot_phone_code_hash')
            
            try:
                await update.message.reply_text("🔄 جاري تسجيل الدخول...")
                
                # تسجيل الدخول بالكود
                await client.sign_in(phone=phone, code=code, phone_code_hash=phone_code_hash)
                
                # التحقق من نجاح تسجيل الدخول
                if await client.is_user_authorized():
                    # حفظ بيانات Userbot في قاعدة البيانات
                    userbot_data = {
                        'api_id': context.user_data.get('userbot_api_id'),
                        'api_hash': context.user_data.get('userbot_api_hash'),
                        'phone': phone,
                        'is_connected': True,
                        'connected_at': datetime.now(),
                        'session_string': client.session.save()
                    }
                    
                    await UserbotHandlers.settings_manager.save_userbot_settings(userbot_data)
                    
                    # تسجيل النشاط
                    await UserbotHandlers.activity_manager.log_activity(
                        user_id=update.effective_user.id,
                        action="userbot_connected",
                        details=f"تم اتصال Userbot بنجاح للرقم: {phone}"
                    )
                    
                    # تنظيف البيانات المؤقتة
                    context.user_data.clear()
                    
                    text = """
🎉 **تم اتصال Userbot بنجاح!**

✅ تم تسجيل الدخول وحفظ الجلسة
✅ Userbot جاهز للاستخدام
✅ يمكن الآن الوصول للمحادثات الخاصة

**المميزات المتاحة الآن:**
• إعادة توجيه من المحادثات الخاصة
• الوصول للمجموعات المقيدة
• سرعة أكبر في المعالجة
• إمكانيات متقدمة

🔒 **الأمان:** تم تشفير وحفظ بيانات الجلسة بأمان
                    """
                    
                    keyboard = [
                        [InlineKeyboardButton("📊 عرض حالة Userbot", callback_data="userbot_status")],
                        [InlineKeyboardButton("🔙 العودة لقائمة Userbot", callback_data="userbot_menu")]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
                    
                    return ConversationHandler.END
                
            except PhoneCodeInvalidError:
                await update.message.reply_text(
                    "❌ كود التحقق غير صحيح\n\n🔄 يرجى إدخال الكود الصحيح:",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔄 إعادة إرسال الكود", callback_data="userbot_resend_code")],
                        [InlineKeyboardButton("❌ إلغاء", callback_data="userbot_menu")]
                    ])
                )
                return USERBOT_CODE
                
            except PhoneCodeExpiredError:
                await update.message.reply_text(
                    "❌ انتهت صلاحية كود التحقق\n\n🔄 يرجى طلب كود جديد:",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔄 إعادة إرسال الكود", callback_data="userbot_resend_code")],
                        [InlineKeyboardButton("❌ إلغاء", callback_data="userbot_menu")]
                    ])
                )
                return USERBOT_CODE
                
            except SessionPasswordNeededError:
                # الحساب محمي بكلمة مرور ثنائية
                text = """
🔐 **مطلوب كلمة المرور الثنائية**

حسابك محمي بكلمة مرور ثنائية (2FA).

يرجى إدخال كلمة المرور الثنائية الآن:

⚠️ **تنبيه:** 
• هذه هي كلمة المرور التي أنشأتها لحماية حسابك
• ليست كلمة مرور تلغرام العادية
                """
                
                keyboard = [[InlineKeyboardButton("❌ إلغاء", callback_data="userbot_menu")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
                
                return USERBOT_PASSWORD
                
            except Exception as e:
                logger.error(f"خطأ في تسجيل الدخول: {e}")
                await update.message.reply_text(
                    f"❌ خطأ في تسجيل الدخول: {str(e)}\n\n🔄 يرجى المحاولة مرة أخرى:",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("❌ إلغاء", callback_data="userbot_menu")
                    ]])
                )
                return USERBOT_CODE
            
        except Exception as e:
            logger.error(f"خطأ في استقبال كود التحقق: {e}")
            await update.message.reply_text("❌ حدث خطأ في معالجة كود التحقق")
            return ConversationHandler.END
    
    @staticmethod
    @error_handler
    async def userbot_password_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """استقبال كلمة المرور الثنائية"""
        try:
            password = update.message.text.strip()
            
            if len(password) < 1:
                await update.message.reply_text(
                    "❌ كلمة المرور لا يمكن أن تكون فارغة\n\n🔄 يرجى إدخال كلمة المرور الثنائية:",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("❌ إلغاء", callback_data="userbot_menu")
                    ]])
                )
                return USERBOT_PASSWORD
            
            # محاولة تسجيل الدخول بكلمة المرور
            client = context.user_data.get('userbot_client')
            phone = context.user_data.get('userbot_phone')
            
            try:
                await update.message.reply_text("🔄 جاري التحقق من كلمة المرور...")
                
                # تسجيل الدخول بكلمة المرور
                await client.sign_in(password=password)
                
                # التحقق من نجاح تسجيل الدخول
                if await client.is_user_authorized():
                    # حفظ بيانات Userbot في قاعدة البيانات
                    userbot_data = {
                        'api_id': context.user_data.get('userbot_api_id'),
                        'api_hash': context.user_data.get('userbot_api_hash'),
                        'phone': phone,
                        'is_connected': True,
                        'connected_at': datetime.now(),
                        'session_string': client.session.save(),
                        'has_2fa': True
                    }
                    
                    await UserbotHandlers.settings_manager.save_userbot_settings(userbot_data)
                    
                    # تسجيل النشاط
                    await UserbotHandlers.activity_manager.log_activity(
                        user_id=update.effective_user.id,
                        action="userbot_connected_2fa",
                        details=f"تم اتصال Userbot بنجاح مع 2FA للرقم: {phone}"
                    )
                    
                    # تنظيف البيانات المؤقتة
                    context.user_data.clear()
                    
                    text = """
🎉 **تم اتصال Userbot بنجاح!**

✅ تم تسجيل الدخول مع كلمة المرور الثنائية
✅ تم حفظ الجلسة بأمان
✅ Userbot جاهز للاستخدام

**المميزات المتاحة الآن:**
• إعادة توجيه من المحادثات الخاصة
• الوصول للمجموعات المقيدة
• سرعة أكبر في المعالجة
• إمكانيات متقدمة

🔒 **الأمان:** حسابك محمي بكلمة مرور ثنائية وتم تشفير البيانات
                    """
                    
                    keyboard = [
                        [InlineKeyboardButton("📊 عرض حالة Userbot", callback_data="userbot_status")],
                        [InlineKeyboardButton("🔙 العودة لقائمة Userbot", callback_data="userbot_menu")]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
                    
                    return ConversationHandler.END
                
            except Exception as e:
                logger.error(f"خطأ في كلمة المرور الثنائية: {e}")
                await update.message.reply_text(
                    "❌ كلمة المرور الثنائية غير صحيحة\n\n🔄 يرجى إدخال كلمة المرور الصحيحة:",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("❌ إلغاء", callback_data="userbot_menu")
                    ]])
                )
                return USERBOT_PASSWORD
            
        except Exception as e:
            logger.error(f"خطأ في استقبال كلمة المرور الثنائية: {e}")
            await update.message.reply_text("❌ حدث خطأ في معالجة كلمة المرور")
            return ConversationHandler.END
    
    @staticmethod
    @admin_required
    @error_handler
    async def userbot_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """عرض حالة Userbot"""
        try:
            query = update.callback_query
            await query.answer()
            
            # الحصول على بيانات Userbot
            userbot_settings = await UserbotHandlers.settings_manager.get_userbot_settings()
            
            if not userbot_settings:
                text = """
🔴 **Userbot غير متصل**

لا توجد بيانات اتصال محفوظة.

يرجى الاتصال أولاً لعرض الحالة.
                """
                keyboard = [[InlineKeyboardButton("🔗 الاتصال الآن", callback_data="userbot_connect_start")]]
            
            else:
                # تحضير معلومات الحالة
                phone = userbot_settings.get('phone', 'غير محدد')
                connected_at = userbot_settings.get('connected_at')
                is_connected = userbot_settings.get('is_connected', False)
                has_2fa = userbot_settings.get('has_2fa', False)
                
                if connected_at:
                    if isinstance(connected_at, str):
                        connected_at = datetime.fromisoformat(connected_at)
                    connected_time = connected_at.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    connected_time = 'غير محدد'
                
                status_emoji = "🟢" if is_connected else "🔴"
                status_text = "متصل" if is_connected else "غير متصل"
                
                text = f"""
{status_emoji} **حالة Userbot**

**الحالة:** {status_text}
**رقم الهاتف:** {phone}
**وقت الاتصال:** {connected_time}
**الحماية الثنائية:** {'🔐 مفعلة' if has_2fa else '🔓 غير مفعلة'}

**الإحصائيات:**
• المهام النشطة: {await UserbotHandlers.task_manager.count_active_tasks()}
• الرسائل المعاد توجيهها اليوم: {await UserbotHandlers._get_today_forwarded_count()}
• آخر نشاط: {await UserbotHandlers._get_last_activity_time()}

**المميزات المتاحة:**
✅ الوصول للمحادثات الخاصة
✅ إعادة توجيه من المجموعات المقيدة
✅ معالجة سريعة للرسائل
✅ إمكانيات متقدمة
                """
                
                keyboard = [
                    [InlineKeyboardButton("🔄 تحديث الحالة", callback_data="userbot_status")],
                    [InlineKeyboardButton("📋 سجل الأنشطة", callback_data="userbot_activity_log")],
                    [InlineKeyboardButton("🔴 قطع الاتصال", callback_data="userbot_disconnect")]
                ]
            
            keyboard.append([InlineKeyboardButton("🔙 العودة لقائمة Userbot", callback_data="userbot_menu")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"خطأ في عرض حالة Userbot: {e}")
            await query.edit_message_text("❌ حدث خطأ في عرض حالة Userbot")
    
    @staticmethod
    @admin_required
    @error_handler
    async def userbot_disconnect(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تأكيد قطع اتصال Userbot"""
        try:
            query = update.callback_query
            await query.answer()
            
            text = """
⚠️ **تأكيد قطع الاتصال**

هل أنت متأكد من قطع اتصال Userbot؟

**سيتم:**
• قطع الاتصال مع Telegram
• حذف بيانات الجلسة
• إيقاف جميع المهام المرتبطة بـ Userbot

**لن يتم:**
• حذف المهام المحفوظة
• حذف الإعدادات العامة
• تأثير على البوت العادي

⚠️ **تنبيه:** ستحتاج لإعادة الاتصال مرة أخرى لاستخدام Userbot
            """
            
            keyboard = [
                [InlineKeyboardButton("🔴 نعم، قطع الاتصال", callback_data="confirm_userbot_disconnect")],
                [InlineKeyboardButton("❌ إلغاء", callback_data="userbot_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"خطأ في تأكيد قطع اتصال Userbot: {e}")
            await query.edit_message_text("❌ حدث خطأ في عملية قطع الاتصال")
    
    @staticmethod
    @admin_required
    @error_handler
    async def confirm_userbot_disconnect(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تنفيذ قطع اتصال Userbot"""
        try:
            query = update.callback_query
            await query.answer()
            
            # حذف بيانات Userbot من قاعدة البيانات
            await UserbotHandlers.settings_manager.delete_userbot_settings()
            
            # تسجيل النشاط
            await UserbotHandlers.activity_manager.log_activity(
                user_id=update.effective_user.id,
                action="userbot_disconnected",
                details="تم قطع اتصال Userbot وحذف بيانات الجلسة"
            )
            
            text = """
✅ **تم قطع اتصال Userbot بنجاح**

• تم قطع الاتصال مع Telegram
• تم حذف بيانات الجلسة بأمان
• تم إيقاف المهام المرتبطة بـ Userbot

**البوت العادي يعمل بشكل طبيعي**

يمكنك الاتصال مرة أخرى في أي وقت.
            """
            
            keyboard = [
                [InlineKeyboardButton("🔗 الاتصال مرة أخرى", callback_data="userbot_connect_start")],
                [InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"خطأ في تنفيذ قطع اتصال Userbot: {e}")
            await query.edit_message_text("❌ حدث خطأ في قطع الاتصال")
    
    @staticmethod
    @error_handler
    async def cancel_userbot_setup(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """إلغاء إعداد Userbot"""
        try:
            # تنظيف البيانات المؤقتة
            if 'userbot_client' in context.user_data:
                client = context.user_data['userbot_client']
                try:
                    await client.disconnect()
                except:
                    pass
            
            context.user_data.clear()
            
            text = """
❌ **تم إلغاء إعداد Userbot**

تم إلغاء عملية الاتصال وتنظيف البيانات المؤقتة.

يمكنك المحاولة مرة أخرى في أي وقت.
            """
            
            keyboard = [
                [InlineKeyboardButton("🔗 المحاولة مرة أخرى", callback_data="userbot_connect_start")],
                [InlineKeyboardButton("🔙 العودة لقائمة Userbot", callback_data="userbot_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
            
            return ConversationHandler.END
            
        except Exception as e:
            logger.error(f"خطأ في إلغاء إعداد Userbot: {e}")
            return ConversationHandler.END
    
    @staticmethod
    async def _get_today_forwarded_count() -> int:
        """الحصول على عدد الرسائل المعاد توجيهها اليوم"""
        try:
            # هذه دالة مساعدة - يمكن تطويرها لاحقاً
            return 0
        except:
            return 0
    
    @staticmethod
    async def _get_last_activity_time() -> str:
        """الحصول على وقت آخر نشاط"""
        try:
            # هذه دالة مساعدة - يمكن تطويرها لاحقاً
            return "غير محدد"
        except:
            return "غير محدد"
