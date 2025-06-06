from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import SessionPasswordNeededError, FloodWaitError
from database.user_manager import UserManager
from config import Config
import asyncio

# حالات المحادثة للـ Userbot
USERBOT_API_ID, USERBOT_API_HASH, USERBOT_PHONE, USERBOT_CODE = range(4)

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
    async def userbot_connect_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """بدء عملية ربط Userbot"""
        text = """
🔗 **ربط Userbot جديد**

أرسل **API ID** الخاص بك:

💡 يمكنك الحصول على API ID من https://my.telegram.org
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
            api_id = int(update.message.text)
            context.user_data['userbot_api_id'] = api_id
            
            text = """
✅ تم حفظ API ID

أرسل **API Hash** الخاص بك:
            """
            
            await update.message.reply_text(text, parse_mode='Markdown')
            return USERBOT_API_HASH
            
        except ValueError:
            await update.message.reply_text("❌ يرجى إرسال رقم صحيح لـ API ID")
            return USERBOT_API_ID

    @staticmethod
    async def userbot_api_hash_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """استقبال API Hash"""
        api_hash = update.message.text.strip()
        
        # التحقق من صحة API Hash
        if len(api_hash) != 32:
            await update.message.reply_text("❌ API Hash يجب أن يكون 32 حرف")
            return USERBOT_API_HASH
        
        context.user_data['userbot_api_hash'] = api_hash
        
        text = """
✅ تم حفظ API Hash

أرسل **رقم الهاتف** (مع رمز البلد):

مثال: +966501234567
        """
        
        await update.message.reply_text(text, parse_mode='Markdown')
        return USERBOT_PHONE

    @staticmethod
    async def userbot_phone_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """استقبال رقم الهاتف وإرسال كود التحقق"""
        phone = update.message.text.strip()
        context.user_data['userbot_phone'] = phone
        
        # إنشاء عميل Telethon وإرسال كود التحقق
        try:
            client = TelegramClient(
                StringSession(),
                context.user_data['userbot_api_id'],
                context.user_data['userbot_api_hash']
            )
            
            await client.connect()
            await client.send_code_request(phone)
            context.user_data['userbot_client'] = client
            
            text = """
📱 **تم إرسال كود التحقق**

أرسل **كود التحقق** الذي وصلك:
            """
            
            await update.message.reply_text(text, parse_mode='Markdown')
            return USERBOT_CODE
            
        except Exception as e:
            await update.message.reply_text(f"❌ خطأ في إرسال كود التحقق: {e}")
            return ConversationHandler.END

    @staticmethod
    async def userbot_code_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """استقبال كود التحقق وإكمال الربط"""
        code = update.message.text.strip()
        client = context.user_data['userbot_client']
        
        try:
            await client.sign_in(
                context.user_data['userbot_phone'],
                code
            )
            
            # حفظ الجلسة في قاعدة البيانات
            session_string = client.session.save()
            user_id = update.effective_user.id
            
            # حفظ في قاعدة البيانات
            success = await UserbotHandlers.save_userbot_session(user_id, session_string)
            
            if success:
                # إضافة العميل للقائمة النشطة
                UserbotHandlers.clients[user_id] = client
                
                # الحصول على معلومات الحساب
                me = await client.get_me()
                
                text = f"""
✅ **تم ربط Userbot بنجاح!**

👤 **الحساب:** {me.first_name}
📱 **المعرف:** @{me.username or 'بدون معرف'}
🆔 **الرقم:** {me.phone or 'غير متاح'}

🎉 يمكنك الآن استخدام Userbot لمراقبة المحادثات الخاصة!
                """
                
                keyboard = [[InlineKeyboardButton("🤖 إدارة Userbot", callback_data="userbot_menu")]]
                
            else:
                text = "❌ فشل في حفظ جلسة Userbot"
                keyboard = [[InlineKeyboardButton("🔙 العودة", callback_data="userbot_menu")]]
            
            await update.message.reply_text(
                text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown'
            )
            
            return ConversationHandler.END
            
        except SessionPasswordNeededError:
            await update.message.reply_text(
                "❌ هذا الحساب محمي بكلمة مرور ثنائية. يرجى تعطيل الحماية الثنائية مؤقتاً."
            )
            return ConversationHandler.END
            
        except Exception as e:
            await update.message.reply_text(f"❌ خطأ في التحقق: {e}")
            return ConversationHandler.END

    @staticmethod
    async def save_userbot_session(user_id: int, session_data: str) -> bool:
        """حفظ جلسة Userbot في قاعدة البيانات"""
        try:
            from database.models import db
            async with db.pool.acquire() as conn:
                await conn.execute('''
                    INSERT INTO userbot_sessions (user_id, session_data, is_active)
                    VALUES ($1, $2, TRUE)
                    ON CONFLICT (user_id)
                    DO UPDATE SET 
                        session_data = EXCLUDED.session_data,
                        is_active = TRUE,
                        updated_at = CURRENT_TIMESTAMP
                ''', user_id, session_data.encode())
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
