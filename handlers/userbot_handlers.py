from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import SessionPasswordNeededError, FloodWaitError, PhoneCodeInvalidError, ApiIdInvalidError
from database.user_manager import UserManager
from utils.error_handler import ErrorHandler
from utils.validators import DataValidator
from config import Config
import asyncio

# حالات المحادثة للـ Userbot - تعريف واضح ومنفصل
USERBOT_API_ID = 100
USERBOT_API_HASH = 101
USERBOT_PHONE = 102
USERBOT_CODE = 103
USERBOT_PASSWORD = 104

class UserbotHandlers:
    clients = {}  # Store active userbot clients
    
    @staticmethod
    async def userbot_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show userbot menu"""
        user_id = update.effective_user.id
        
        # Check if user has active userbot session
        has_session = user_id in UserbotHandlers.clients
        
        if has_session:
            keyboard = [
                [
                    InlineKeyboardButton("📊 حالة الـ Userbot", callback_data="userbot_status"),
                    InlineKeyboardButton("🔄 إعادة تشغيل", callback_data="userbot_restart")
                ],
                [
                    InlineKeyboardButton("⚙️ إعدادات Userbot", callback_data="userbot_settings"),
                    InlineKeyboardButton("🗑️ حذف الجلسة", callback_data="userbot_delete")
                ],
                [
                    InlineKeyboardButton("🔙 العودة", callback_data="main_menu")
                ]
            ]
            
            text = """
🤖 **إدارة Userbot**

✅ **الحالة:** متصل ويعمل
🔗 **الجلسة:** نشطة

اختر العملية التي تريد تنفيذها:
            """
        else:
            keyboard = [
                [
                    InlineKeyboardButton("🔗 ربط Userbot جديد", callback_data="userbot_connect"),
                    InlineKeyboardButton("📱 استيراد جلسة", callback_data="userbot_import")
                ],
                [
                    InlineKeyboardButton("ℹ️ ما هو Userbot؟", callback_data="userbot_info"),
                    InlineKeyboardButton("🔙 العودة", callback_data="main_menu")
                ]
            ]
            
            text = """
🤖 **إدارة Userbot**

❌ **الحالة:** غير متصل
🔗 **الجلسة:** غير موجودة

الـ Userbot يسمح بمراقبة المحادثات الخاصة والمجموعات التي لا يمكن للبوت العادي الوصول إليها.
            """
        
        await update.callback_query.edit_message_text(
            text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown'
        )
    
    @staticmethod
    async def connect_userbot(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start userbot connection process"""
        text = """
🔗 **ربط Userbot جديد**

لربط الـ Userbot، ستحتاج إلى:

1️⃣ **API ID** و **API Hash** من my.telegram.org
2️⃣ **رقم الهاتف** المرتبط بحساب تلغرام

⚠️ **تحذير مهم:**
- استخدم حساب منفصل للـ Userbot
- لا تشارك بيانات API مع أي شخص
- قد يتم تقييد الحساب في حالة الاستخدام المفرط

هل تريد المتابعة؟
        """
        
        keyboard = [
            [
                InlineKeyboardButton("✅ نعم، أريد المتابعة", callback_data="userbot_connect_start"),
                InlineKeyboardButton("❌ إلغاء", callback_data="userbot_menu")
            ]
        ]
        
        await update.callback_query.edit_message_text(
            text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown'
        )
    
    @staticmethod
    async def userbot_connect_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """بدء عملية ربط Userbot"""
        # تنظيف البيانات السابقة
        context.user_data.clear()
        
        text = """
🔗 **ربط Userbot جديد**

**الخطوة 1/4:** أرسل **API ID** الخاص بك

💡 يمكنك الحصول على API ID من https://my.telegram.org

⚠️ **مثال:** 1234567
        """
        
        keyboard = [[InlineKeyboardButton("❌ إلغاء", callback_data="userbot_menu")]]
        
        await update.callback_query.edit_message_text(
            text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown'
        )
        
        return USERBOT_API_ID

    @staticmethod
    async def userbot_api_id_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """استقبال API ID"""
        try:
            api_id_text = update.message.text.strip()
            
            # التحقق من صحة API ID
            is_valid, api_id, message = DataValidator.validate_api_id(api_id_text)
            if not is_valid:
                await update.message.reply_text(
                    f"❌ {message}\n\n🔄 يرجى إرسال API ID صحيح:",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("❌ إلغاء", callback_data="userbot_menu")
                    ]])
                )
                return USERBOT_API_ID
            
            # حفظ API ID
            context.user_data['userbot_api_id'] = api_id
            
            text = f"""
✅ **تم حفظ API ID:** `{api_id}`

**الخطوة 2/4:** أرسل **API Hash** الخاص بك

💡 API Hash هو نص مكون من 32 حرف

⚠️ **مثال:** a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
            """
            
            await update.message.reply_text(
                text, 
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("❌ إلغاء", callback_data="userbot_menu")
                ]])
            )
            return USERBOT_API_HASH
            
        except Exception as e:
            await ErrorHandler.log_error(update, context, e, "userbot_api_id_received")
            await update.message.reply_text(
                "❌ حدث خطأ أثناء معالجة API ID. يرجى المحاولة مرة أخرى.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 العودة", callback_data="userbot_menu")
                ]])
            )
            return ConversationHandler.END

    @staticmethod
    async def userbot_api_hash_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """استقبال API Hash"""
        try:
            api_hash = update.message.text.strip()
            
            # التحقق من صحة API Hash
            is_valid, message = DataValidator.validate_api_hash(api_hash)
            if not is_valid:
                await update.message.reply_text(
                    f"❌ {message}\n\n🔄 يرجى إرسال API Hash صحيح:",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("❌ إلغاء", callback_data="userbot_menu")
                    ]])
                )
                return USERBOT_API_HASH
            
            # حفظ API Hash
            context.user_data['userbot_api_hash'] = api_hash
            
            text = f"""
✅ **تم حفظ API Hash:** `{api_hash[:8]}...{api_hash[-8:]}`

**الخطوة 3/4:** أرسل **رقم الهاتف** (مع رمز البلد)

💡 يجب أن يبدأ الرقم بعلامة +

⚠️ **أمثلة:**
• +966501234567 (السعودية)
• +201234567890 (مصر)
• +971501234567 (الإمارات)
            """
            
            await update.message.reply_text(
                text, 
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("❌ إلغاء", callback_data="userbot_menu")
                ]])
            )
            return USERBOT_PHONE
            
        except Exception as e:
            await ErrorHandler.log_error(update, context, e, "userbot_api_hash_received")
            await update.message.reply_text(
                "❌ حدث خطأ أثناء معالجة API Hash. يرجى المحاولة مرة أخرى.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 العودة", callback_data="userbot_menu")
                ]])
            )
            return ConversationHandler.END

    @staticmethod
    async def userbot_phone_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """استقبال رقم الهاتف وإرسال كود التحقق"""
        try:
            phone = update.message.text.strip()
            
            # التحقق من صحة رقم الهاتف
            is_valid, message = DataValidator.validate_phone_number(phone)
            if not is_valid:
                await update.message.reply_text(
                    f"❌ {message}\n\n🔄 يرجى إرسال رقم هاتف صحيح:",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("❌ إلغاء", callback_data="userbot_menu")
                    ]])
                )
                return USERBOT_PHONE
            
            # حفظ رقم الهاتف
            context.user_data['userbot_phone'] = phone
            
            # إرسال رسالة انتظار
            wait_message = await update.message.reply_text(
                "⏳ **جاري إرسال كود التحقق...**\n\nيرجى الانتظار قليلاً...",
                parse_mode='Markdown'
            )
            
            # إنشاء عميل Telethon وإرسال كود التحقق
            try:
                client = TelegramClient(
                    StringSession(),
                    context.user_data['userbot_api_id'],
                    context.user_data['userbot_api_hash']
                )
                
                await client.connect()
                
                # إرسال كود التحقق
                sent_code = await client.send_code_request(phone)
                context.user_data['userbot_client'] = client
                context.user_data['phone_code_hash'] = sent_code.phone_code_hash
                
                # حذف رسالة الانتظار
                await wait_message.delete()
                
                text = f"""
📱 **تم إرسال كود التحقق!**

**الخطوة 4/4:** أرسل **كود التحقق** الذي وصلك على رقم:
`{phone}`

💡 الكود مكون من 5 أرقام عادة

⚠️ **مثال:** 12345
                """
                
                await update.message.reply_text(
                    text, 
                    parse_mode='Markdown',
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("❌ إلغاء", callback_data="userbot_menu")
                    ]])
                )
                return USERBOT_CODE
                
            except ApiIdInvalidError:
                await wait_message.delete()
                await update.message.reply_text(
                    "❌ **API ID أو API Hash غير صحيح**\n\nيرجى التأكد من البيانات والمحاولة مرة أخرى.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 العودة", callback_data="userbot_menu")
                    ]])
                )
                return ConversationHandler.END
                
            except Exception as api_error:
                await wait_message.delete()
                await update.message.reply_text(
                    f"❌ **خطأ في إرسال كود التحقق:**\n`{str(api_error)}`\n\nيرجى المحاولة مرة أخرى.",
                    parse_mode='Markdown',
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 العودة", callback_data="userbot_menu")
                    ]])
                )
                return ConversationHandler.END
            
        except Exception as e:
            await ErrorHandler.log_error(update, context, e, "userbot_phone_received")
            await update.message.reply_text(
                "❌ حدث خطأ أثناء معالجة رقم الهاتف. يرجى المحاولة مرة أخرى.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 العودة", callback_data="userbot_menu")
                ]])
            )
            return ConversationHandler.END

    @staticmethod
    async def userbot_code_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """استقبال كود التحقق وإكمال الربط"""
        try:
            code = update.message.text.strip()
            
            # التحقق من صحة الكود
            if not code.isdigit() or len(code) < 4 or len(code) > 6:
                await update.message.reply_text(
                    "❌ **كود التحقق غير صحيح**\n\nيرجى إرسال الكود المكون من 4-6 أرقام:",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("❌ إلغاء", callback_data="userbot_menu")
                    ]])
                )
                return USERBOT_CODE
            
            client = context.user_data.get('userbot_client')
            if not client:
                await update.message.reply_text(
                    "❌ **انتهت صلاحية الجلسة**\n\nيرجى البدء من جديد.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 العودة", callback_data="userbot_menu")
                    ]])
                )
                return ConversationHandler.END
            
            # إرسال رسالة انتظار
            wait_message = await update.message.reply_text(
                "⏳ **جاري التحقق من الكود...**\n\nيرجى الانتظار...",
                parse_mode='Markdown'
            )
            
            try:
                # محاولة تسجيل الدخول
                await client.sign_in(
                    context.user_data['userbot_phone'],
                    code,
                    phone_code_hash=context.user_data['phone_code_hash']
                )
                
                # حفظ الجلسة في قاعدة البيانات
                session_string = client.session.save()
                user_id = update.effective_user.id
                
                success = await UserbotHandlers.save_userbot_session(
                    user_id, 
                    session_string,
                    context.user_data['userbot_api_id'],
                    context.user_data['userbot_api_hash'],
                    context.user_data['userbot_phone']
                )
                
                if success:
                    # إضافة العميل للقائمة النشطة
                    UserbotHandlers.clients[user_id] = client
                    
                    # الحصول على معلومات الحساب
                    me = await client.get_me()
                    
                    # حذف رسالة الانتظار
                    await wait_message.delete()
                    
                    text = f"""
🎉 **تم ربط Userbot بنجاح!**

👤 **الحساب:** {me.first_name}
📱 **المعرف:** @{me.username or 'بدون معرف'}
🆔 **الرقم:** {me.phone or 'غير متاح'}

✅ يمكنك الآن استخدام Userbot لمراقبة المحادثات الخاصة!
                    """
                    
                    keyboard = [[InlineKeyboardButton("🤖 إدارة Userbot", callback_data="userbot_menu")]]
                    
                else:
                    await wait_message.delete()
                    text = "❌ **فشل في حفظ جلسة Userbot**\n\nيرجى المحاولة مرة أخرى."
                    keyboard = [[InlineKeyboardButton("🔙 العودة", callback_data="userbot_menu")]]
                
                await update.message.reply_text(
                    text, 
                    reply_markup=InlineKeyboardMarkup(keyboard), 
                    parse_mode='Markdown'
                )
                
                # تنظيف البيانات
                context.user_data.clear()
                return ConversationHandler.END
                
            except SessionPasswordNeededError:
                await wait_message.delete()
                await update.message.reply_text(
                    "🔐 **هذا الحساب محمي بكلمة مرور ثنائية**\n\nأرسل كلمة المرور الخاصة بك:",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("❌ إلغاء", callback_data="userbot_menu")
                    ]])
                )
                return USERBOT_PASSWORD
                
            except PhoneCodeInvalidError:
                await wait_message.delete()
                await update.message.reply_text(
                    "❌ **كود التحقق غير صحيح**\n\nيرجى إرسال الكود الصحيح:",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("❌ إلغاء", callback_data="userbot_menu")
                    ]])
                )
                return USERBOT_CODE
                
            except Exception as sign_in_error:
                await wait_message.delete()
                await update.message.reply_text(
                    f"❌ **خطأ في تسجيل الدخول:**\n`{str(sign_in_error)}`",
                    parse_mode='Markdown',
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 العودة", callback_data="userbot_menu")
                    ]])
                )
                return ConversationHandler.END
            
        except Exception as e:
            await ErrorHandler.log_error(update, context, e, "userbot_code_received")
            await update.message.reply_text(
                "❌ حدث خطأ أثناء التحقق من الكود. يرجى المحاولة مرة أخرى.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 العودة", callback_data="userbot_menu")
                ]])
            )
            return ConversationHandler.END

    @staticmethod
    async def userbot_password_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """استقبال كلمة المرور الثنائية"""
        try:
            password = update.message.text.strip()
            client = context.user_data.get('userbot_client')
            
            if not client:
                await update.message.reply_text(
                    "❌ **انتهت صلاحية الجلسة**\n\nيرجى البدء من جديد.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 العودة", callback_data="userbot_menu")
                    ]])
                )
                return ConversationHandler.END
            
            # إرسال رسالة انتظار
            wait_message = await update.message.reply_text(
                "⏳ **جاري التحقق من كلمة المرور...**",
                parse_mode='Markdown'
            )
            
            try:
                # تسجيل الدخول بكلمة المرور
                await client.sign_in(password=password)
                
                # حفظ الجلسة
                session_string = client.session.save()
                user_id = update.effective_user.id
                
                success = await UserbotHandlers.save_userbot_session(
                    user_id, 
                    session_string,
                    context.user_data['userbot_api_id'],
                    context.user_data['userbot_api_hash'],
                    context.user_data['userbot_phone']
                )
                
                if success:
                    UserbotHandlers.clients[user_id] = client
                    me = await client.get_me()
                    
                    await wait_message.delete()
                    
                    text = f"""
🎉 **تم ربط Userbot بنجاح!**

👤 **الحساب:** {me.first_name}
📱 **المعرف:** @{me.username or 'بدون معرف'}

✅ يمكنك الآن استخدام Userbot!
                    """
                    
                    keyboard = [[InlineKeyboardButton("🤖 إدارة Userbot", callback_data="userbot_menu")]]
                    
                else:
                    await wait_message.delete()
                    text = "❌ فشل في حفظ الجلسة"
                    keyboard = [[InlineKeyboardButton("🔙 العودة", callback_data="userbot_menu")]]
                
                await update.message.reply_text(
                    text, 
                    reply_markup=InlineKeyboardMarkup(keyboard), 
                    parse_mode='Markdown'
                )
                
                context.user_data.clear()
                return ConversationHandler.END
                
            except Exception as password_error:
                await wait_message.delete()
                await update.message.reply_text(
                    f"❌ **كلمة المرور غير صحيحة**\n\nيرجى إرسال كلمة المرور الصحيحة:",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("❌ إلغاء", callback_data="userbot_menu")
                    ]])
                )
                return USERBOT_PASSWORD
                
        except Exception as e:
            await ErrorHandler.log_error(update, context, e, "userbot_password_received")
            await update.message.reply_text(
                "❌ حدث خطأ أثناء التحقق من كلمة المرور.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 العودة", callback_data="userbot_menu")
                ]])
            )
            return ConversationHandler.END

    @staticmethod
    async def userbot_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show userbot information"""
        text = """
ℹ️ **ما هو Userbot؟**

الـ **Userbot** هو حساب تلغرام عادي يعمل كبوت، ويتيح لك:

✅ **المميزات:**
• مراقبة المحادثات الخاصة
• الوصول للمجموعات المقيدة
• توجيه الرسائل من أي محادثة
• عدم الحاجة لإضافة البوت للمجموعات

⚠️ **المخاطر:**
• قد يتم تقييد الحساب
• يحتاج بيانات حساسة (API)
• استهلاك أكبر للموارد

🔒 **الأمان:**
• نحن لا نحفظ كلمات المرور
• البيانات مشفرة في قاعدة البيانات
• يمكنك حذف الجلسة في أي وقت

💡 **نصيحة:** استخدم حساب منفصل للـ Userbot
        """
        
        keyboard = [
            [
                InlineKeyboardButton("🔗 ربط Userbot", callback_data="userbot_connect"),
                InlineKeyboardButton("🔙 العودة", callback_data="userbot_menu")
            ]
        ]
        
        await update.callback_query.edit_message_text(
            text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown'
        )
    
    @staticmethod
    async def userbot_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show userbot status"""
        user_id = update.effective_user.id
        
        if user_id not in UserbotHandlers.clients:
            await update.callback_query.answer("❌ لا يوجد userbot متصل")
            return
        
        client = UserbotHandlers.clients[user_id]
        
        try:
            me = await client.get_me()
            
            text = f"""
📊 **حالة Userbot**

✅ **الحالة:** متصل ويعمل
👤 **الحساب:** {me.first_name} (@{me.username or 'بدون معرف'})
📱 **رقم الهاتف:** {me.phone or 'غير متاح'}
🆔 **معرف المستخدم:** `{me.id}`

🔄 **آخر نشاط:** الآن
⚡ **الاتصال:** مستقر
            """
            
        except Exception as e:
            text = f"""
📊 **حالة Userbot**

❌ **الحالة:** خطأ في الاتصال
🔴 **المشكلة:** {str(e)}

يرجى إعادة تشغيل الـ Userbot أو إعادة الاتصال.
            """
        
        keyboard = [
            [
                InlineKeyboardButton("🔄 تحديث", callback_data="userbot_status"),
                InlineKeyboardButton("🔙 العودة", callback_data="userbot_menu")
            ]
        ]
        
        await update.callback_query.edit_message_text(
            text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown'
        )

    @staticmethod
    async def start_userbot_client(user_id: int, session_string: str) -> bool:
        """Start userbot client for user"""
        try:
            if not Config.API_ID or not Config.API_HASH:
                return False
            
            client = TelegramClient(
                StringSession(session_string),
                Config.API_ID,
                Config.API_HASH
            )
            
            await client.start()
            
            if await client.is_user_authorized():
                UserbotHandlers.clients[user_id] = client
                return True
            else:
                await client.disconnect()
                return False
                
        except Exception as e:
            print(f"Error starting userbot client: {e}")
            return False
    
    @staticmethod
    async def stop_userbot_client(user_id: int):
        """Stop userbot client for user"""
        if user_id in UserbotHandlers.clients:
            try:
                await UserbotHandlers.clients[user_id].disconnect()
                del UserbotHandlers.clients[user_id]
            except Exception as e:
                print(f"Error stopping userbot client: {e}")

    @staticmethod
    async def save_userbot_session(user_id: int, session_data: str, api_id: int, api_hash: str, phone: str) -> bool:
        """حفظ جلسة Userbot في قاعدة البيانات"""
        try:
            from database.models import db
            async with db.pool.acquire() as conn:
                await conn.execute('''
                    INSERT INTO userbot_sessions (user_id, session_data, api_id, api_hash, phone_number, is_active)
                    VALUES ($1, $2, $3, $4, $5, TRUE)
                    ON CONFLICT (user_id)
                    DO UPDATE SET 
                        session_data = EXCLUDED.session_data,
                        api_id = EXCLUDED.api_id,
                        api_hash = EXCLUDED.api_hash,
                        phone_number = EXCLUDED.phone_number,
                        is_active = TRUE,
                        last_connected = CURRENT_TIMESTAMP,
                        updated_at = CURRENT_TIMESTAMP
                ''', user_id, session_data.encode(), api_id, api_hash, phone)
                return True
        except Exception as e:
            print(f"Error saving userbot session: {e}")
            return False

    @staticmethod
    async def load_userbot_sessions():
        """تحميل جلسات Userbot النشطة عند بدء البوت"""
        try:
            from database.models import db
            async with db.pool.acquire() as conn:
                rows = await conn.fetch(
                    'SELECT user_id, session_data FROM userbot_sessions WHERE is_active = TRUE'
                )
                
                for row in rows:
                    user_id = row['user_id']
                    session_data = row['session_data'].decode()
                    
                    success = await UserbotHandlers.start_userbot_client(user_id, session_data)
                    if not success:
                        print(f"Failed to start userbot for user {user_id}")
                        
        except Exception as e:
            print(f"Error loading userbot sessions: {e}")

    @staticmethod
    async def restart_userbot(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """إعادة تشغيل Userbot"""
        user_id = update.effective_user.id
        
        try:
            # إيقاف العميل الحالي
            if user_id in UserbotHandlers.clients:
                await UserbotHandlers.clients[user_id].disconnect()
                del UserbotHandlers.clients[user_id]
            
            # تحميل الجلسة من قاعدة البيانات
            from database.models import db
            async with db.pool.acquire() as conn:
                row = await conn.fetchrow(
                    'SELECT session_data FROM userbot_sessions WHERE user_id = $1 AND is_active = TRUE',
                    user_id
                )
                
                if row:
                    session_data = row['session_data'].decode()
                    success = await UserbotHandlers.start_userbot_client(user_id, session_data)
                    
                    if success:
                        await update.callback_query.answer("✅ تم إعادة تشغيل Userbot بنجاح")
                    else:
                        await update.callback_query.answer("❌ فشل في إعادة تشغيل Userbot")
                else:
                    await update.callback_query.answer("❌ لا توجد جلسة محفوظة")
                    
        except Exception as e:
            await update.callback_query.answer(f"❌ خطأ: {e}")

    @staticmethod
    async def delete_userbot_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تأكيد حذف Userbot"""
        text = """
⚠️ **تأكيد حذف Userbot**

هل أنت متأكد من حذف جلسة Userbot؟

⚠️ **تحذير:** سيتم حذف الجلسة نهائياً ولن تتمكن من استعادتها.
        """
        
        keyboard = [
            [
                InlineKeyboardButton("✅ نعم، احذف", callback_data="confirm_delete_userbot"),
                InlineKeyboardButton("❌ إلغاء", callback_data="userbot_menu")
            ]
        ]
        
        await update.callback_query.edit_message_text(
            text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown'
        )

    @staticmethod
    async def delete_userbot_confirmed(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """حذف Userbot بعد التأكيد"""
        user_id = update.effective_user.id
        
        try:
            # إيقاف العميل
            if user_id in UserbotHandlers.clients:
                await UserbotHandlers.clients[user_id].disconnect()
                del UserbotHandlers.clients[user_id]
            
            # حذف من قاعدة البيانات
            from database.models import db
            async with db.pool.acquire() as conn:
                await conn.execute(
                    'DELETE FROM userbot_sessions WHERE user_id = $1',
                    user_id
                )
            
            await update.callback_query.answer("✅ تم حذف Userbot بنجاح")
            await UserbotHandlers.userbot_menu(update, context)
            
        except Exception as e:
            await update.callback_query.answer(f"❌ خطأ في الحذف: {e}")

    @staticmethod
    async def conversation_timeout(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالج انتهاء وقت المحادثة"""
        await update.message.reply_text(
            "⏰ **انتهت مهلة العملية**\n\nيرجى البدء من جديد.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 العودة", callback_data="userbot_menu")
            ]])
        )
        
        # تنظيف البيانات والعميل
        if 'userbot_client' in context.user_data:
            try:
                client = context.user_data['userbot_client']
                await client.disconnect()
            except:
                pass
        
        context.user_data.clear()
        return ConversationHandler.END

    @staticmethod
    async def conversation_fallback(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالج الخروج من المحادثة"""
        # تنظيف البيانات والعميل
        if 'userbot_client' in context.user_data:
            try:
                client = context.user_data['userbot_client']
                await client.disconnect()
            except:
                pass
        
        context.user_data.clear()
        
        # العودة لقائمة Userbot
        await UserbotHandlers.userbot_menu(update, context)
        return ConversationHandler.END
