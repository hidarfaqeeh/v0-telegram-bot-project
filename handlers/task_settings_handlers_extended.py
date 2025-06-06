# امتداد لمعالجات الإعدادات المتقدمة
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from database.task_manager import TaskManager
from utils.validators import DataValidator
from utils.error_handler import ErrorHandler

# إضافة المعالجات المتبقية لـ TaskSettingsHandlers
class TaskSettingsHandlersExtended:
    @staticmethod
    async def select_all_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تحديد جميع أنواع الوسائط"""
        try:
            task_id = int(update.callback_query.data.split('_')[-1])
            
            from config import Config
            success = await TaskManager.update_media_filters(task_id, Config.SUPPORTED_MEDIA_TYPES.copy())
            
            if success:
                await update.callback_query.answer("✅ تم تحديد جميع أنواع الوسائط")
                # إعادة عرض القائمة
                context.user_data['callback_data'] = f"media_filters_{task_id}"
                from handlers.task_settings_handlers import TaskSettingsHandlers
                await TaskSettingsHandlers.media_filters_menu(update, context)
            else:
                await update.callback_query.answer("❌ فشل في التحديث")
                
        except Exception as e:
            await ErrorHandler.log_error(update, context, e, "select_all_media")
            await update.callback_query.answer("❌ حدث خطأ")
    
    @staticmethod
    async def deselect_all_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """إلغاء تحديد جميع أنواع الوسائط"""
        try:
            task_id = int(update.callback_query.data.split('_')[-1])
            
            success = await TaskManager.update_media_filters(task_id, [])
            
            if success:
                await update.callback_query.answer("✅ تم إلغاء تحديد جميع أنواع الوسائط")
                # إعادة عرض القائمة
                context.user_data['callback_data'] = f"media_filters_{task_id}"
                from handlers.task_settings_handlers import TaskSettingsHandlers
                await TaskSettingsHandlers.media_filters_menu(update, context)
            else:
                await update.callback_query.answer("❌ فشل في التحديث")
                
        except Exception as e:
            await ErrorHandler.log_error(update, context, e, "deselect_all_media")
            await update.callback_query.answer("❌ حدث خطأ")
    
    @staticmethod
    async def add_required_word_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """بدء إضافة كلمة مطلوبة"""
        try:
            task_id = int(update.callback_query.data.split('_')[-1])
            context.user_data['current_task_id'] = task_id
            context.user_data['word_type'] = 'required'
            
            text = """
➕ **إضافة كلمة مطلوبة**

أرسل الكلمة أو العبارة المطلوبة:

💡 الرسائل التي لا تحتوي على هذه الكلمة سيتم تجاهلها
            """
            
            keyboard = [[InlineKeyboardButton("❌ إلغاء", callback_data=f"text_filters_{task_id}")]]
            
            await update.callback_query.edit_message_text(
                text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown'
            )
            
            from handlers.task_settings_handlers import REQUIRED_WORD_INPUT
            return REQUIRED_WORD_INPUT
            
        except Exception as e:
            await ErrorHandler.log_error(update, context, e, "add_required_word_start")
            await update.callback_query.answer("❌ حدث خطأ")
            return ConversationHandler.END
    
    @staticmethod
    async def required_word_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """استقبال الكلمة المطلوبة"""
        try:
            word = update.message.text.strip()
            task_id = context.user_data.get('current_task_id')
            
            # التحقق من صحة الكلمة
            is_valid, message = DataValidator.validate_word(word)
            if not is_valid:
                await update.message.reply_text(message)
                return REQUIRED_WORD_INPUT
            
            # الحصول على المهمة
            task = await TaskManager.get_task(task_id)
            if not task:
                await update.message.reply_text("❌ المهمة غير موجودة")
                return ConversationHandler.END
            
            # إضافة الكلمة
            blocked_words = task['settings'].get('blocked_words', [])
            required_words = task['settings'].get('required_words', [])
            
            if word not in required_words:
                required_words.append(word)
                
                success = await TaskManager.update_text_filters(task_id, blocked_words, required_words)
                
                if success:
                    text = f"✅ تم إضافة الكلمة المطلوبة: **{word}**"
                    keyboard = [
                        [
                            InlineKeyboardButton("➕ إضافة كلمة أخرى", callback_data=f"add_required_word_{task_id}"),
                            InlineKeyboardButton("🔙 العودة", callback_data=f"text_filters_{task_id}")
                        ]
                    ]
                else:
                    text = "❌ فشل في إضافة الكلمة"
                    keyboard = [[InlineKeyboardButton("🔙 العودة", callback_data=f"text_filters_{task_id}")]]
            else:
                text = f"⚠️ الكلمة **{word}** موجودة مسبقاً في القائمة المطلوبة"
                keyboard = [[InlineKeyboardButton("🔙 العودة", callback_data=f"text_filters_{task_id}")]]
            
            await update.message.reply_text(
                text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown'
            )
            
            return ConversationHandler.END
            
        except Exception as e:
            await ErrorHandler.log_error(update, context, e, "required_word_received")
            await update.message.reply_text("❌ حدث خطأ أثناء إضافة الكلمة")
            return ConversationHandler.END
    
    @staticmethod
    async def add_replacement_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """بدء إضافة استبدال"""
        try:
            task_id = int(update.callback_query.data.split('_')[-1])
            context.user_data['current_task_id'] = task_id
            
            text = """
🔄 **إضافة استبدال جديد**

أرسل **النص القديم** الذي تريد استبداله:
            """
            
            keyboard = [[InlineKeyboardButton("❌ إلغاء", callback_data=f"replacements_{task_id}")]]
            
            await update.callback_query.edit_message_text(
                text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown'
            )
            
            from handlers.task_settings_handlers import REPLACEMENT_OLD_TEXT
            return REPLACEMENT_OLD_TEXT
            
        except Exception as e:
            await ErrorHandler.log_error(update, context, e, "add_replacement_start")
            await update.callback_query.answer("❌ حدث خطأ")
            return ConversationHandler.END
    
    @staticmethod
    async def replacement_old_text_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """استقبال النص القديم للاستبدال"""
        try:
            old_text = update.message.text.strip()
            context.user_data['replacement_old_text'] = old_text
            
            # التحقق من صحة النص
            is_valid, message = DataValidator.validate_word(old_text)
            if not is_valid:
                await update.message.reply_text(message)
                return REPLACEMENT_OLD_TEXT
            
            text = f"""
🔄 **إضافة استبدال**

النص القديم: `{old_text}`

أرسل **النص الجديد** الذي سيحل محله:
            """
            
            await update.message.reply_text(text, parse_mode='Markdown')
            
            from handlers.task_settings_handlers import REPLACEMENT_NEW_TEXT
            return REPLACEMENT_NEW_TEXT
            
        except Exception as e:
            await ErrorHandler.log_error(update, context, e, "replacement_old_text_received")
            await update.message.reply_text("❌ حدث خطأ")
            return ConversationHandler.END
    
    @staticmethod
    async def replacement_new_text_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """استقبال النص الجديد للاستبدال"""
        try:
            new_text = update.message.text.strip()
            old_text = context.user_data.get('replacement_old_text')
            task_id = context.user_data.get('current_task_id')
            
            # التحقق من صحة النص
            is_valid, message = DataValidator.validate_replacement_text(old_text, new_text)
            if not is_valid:
                await update.message.reply_text(message)
                return REPLACEMENT_NEW_TEXT
            
            # الحصول على المهمة
            task = await TaskManager.get_task(task_id)
            if not task:
                await update.message.reply_text("❌ المهمة غير موجودة")
                return ConversationHandler.END
            
            # إضافة الاستبدال
            replacements = task['settings'].get('replacements', {})
            replacements[old_text] = new_text
            
            success = await TaskManager.update_replacements(task_id, replacements)
            
            if success:
                text = f"""
✅ **تم إضافة الاستبدال بنجاح!**

النص القديم: `{old_text}`
النص الجديد: `{new_text}`
                """
                keyboard = [
                    [
                        InlineKeyboardButton("➕ إضافة استبدال آخر", callback_data=f"add_replacement_{task_id}"),
                        InlineKeyboardButton("🔙 العودة", callback_data=f"replacements_{task_id}")
                    ]
                ]
            else:
                text = "❌ فشل في إضافة الاستبدال"
                keyboard = [[InlineKeyboardButton("🔙 العودة", callback_data=f"replacements_{task_id}")]]
            
            await update.message.reply_text(
                text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown'
            )
            
            return ConversationHandler.END
            
        except Exception as e:
            await ErrorHandler.log_error(update, context, e, "replacement_new_text_received")
            await update.message.reply_text("❌ حدث خطأ أثناء إضافة الاستبدال")
            return ConversationHandler.END
    
    @staticmethod
    async def set_delay_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """بدء تعيين وقت التأخير"""
        try:
            task_id = int(update.callback_query.data.split('_')[-1])
            context.user_data['current_task_id'] = task_id
            
            text = """
⏰ **تعيين وقت التأخير**

أرسل وقت التأخير **بالثواني**:

مثال:
• 5 = 5 ثوان
• 30 = 30 ثانية  
• 60 = دقيقة واحدة

⚠️ الحد الأقصى: 3600 ثانية (ساعة واحدة)
            """
            
            keyboard = [[InlineKeyboardButton("❌ إلغاء", callback_data=f"delay_settings_{task_id}")]]
            
            await update.callback_query.edit_message_text(
                text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown'
            )
            
            from handlers.task_settings_handlers import DELAY_TIME_INPUT
            return DELAY_TIME_INPUT
            
        except Exception as e:
            await ErrorHandler.log_error(update, context, e, "set_delay_start")
            await update.callback_query.answer("❌ حدث خطأ")
            return ConversationHandler.END
    
    @staticmethod
    async def delay_time_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """استقبال وقت التأخير"""
        try:
            delay_str = update.message.text.strip()
            task_id = context.user_data.get('current_task_id')
            
            # التحقق من صحة الوقت
            is_valid, delay, message = DataValidator.validate_delay_time(delay_str)
            if not is_valid:
                await update.message.reply_text(message)
                return DELAY_TIME_INPUT
            
            # تحديث إعدادات التأخير
            delay_config = {
                'enabled': True,
                'seconds': delay
            }
            
            success = await TaskManager.update_delay_settings(task_id, delay_config)
            
            if success:
                text = f"✅ تم تعيين وقت التأخير: **{delay} ثانية**"
                keyboard = [
                    [
                        InlineKeyboardButton("⏰ تغيير الوقت", callback_data=f"set_delay_{task_id}"),
                        InlineKeyboardButton("🔙 العودة", callback_data=f"delay_settings_{task_id}")
                    ]
                ]
            else:
                text = "❌ فشل في تعيين وقت التأخير"
                keyboard = [[InlineKeyboardButton("🔙 العودة", callback_data=f"delay_settings_{task_id}")]]
            
            await update.message.reply_text(
                text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown'
            )
            
            return ConversationHandler.END
            
        except Exception as e:
            await ErrorHandler.log_error(update, context, e, "delay_time_received")
            await update.message.reply_text("❌ حدث خطأ أثناء تعيين التأخير")
            return ConversationHandler.END
    
    @staticmethod
    async def toggle_delay(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تبديل حالة التأخير"""
        try:
            task_id = int(update.callback_query.data.split('_')[-1])
            task = await TaskManager.get_task(task_id)
            
            if not task:
                await update.callback_query.answer("❌ المهمة غير موجودة")
                return
            
            delay_settings = task['settings'].get('delay', {})
            current_state = delay_settings.get('enabled', False)
            
            delay_settings['enabled'] = not current_state
            
            success = await TaskManager.update_delay_settings(task_id, delay_settings)
            
            if success:
                state_text = "تم تفعيل" if not current_state else "تم تعطيل"
                await update.callback_query.answer(f"✅ {state_text} التأخير")
                
                # إعادة عرض القائمة
                context.user_data['callback_data'] = f"delay_settings_{task_id}"
                from handlers.task_settings_handlers import TaskSettingsHandlers
                await TaskSettingsHandlers.delay_settings_menu(update, context)
            else:
                await update.callback_query.answer("❌ فشل في تحديث التأخير")
                
        except Exception as e:
            await ErrorHandler.log_error(update, context, e, "toggle_delay")
            await update.callback_query.answer("❌ حدث خطأ")
    
    @staticmethod
    async def quick_delay_set(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تعيين تأخير سريع"""
        try:
            data_parts = update.callback_query.data.split('_')
            delay_seconds = int(data_parts[2])
            task_id = int(data_parts[3])
            
            delay_config = {
                'enabled': True,
                'seconds': delay_seconds
            }
            
            success = await TaskManager.update_delay_settings(task_id, delay_config)
            
            if success:
                await update.callback_query.answer(f"✅ تم تعيين التأخير: {delay_seconds} ثانية")
                
                # إعادة عرض القائمة
                context.user_data['callback_data'] = f"delay_settings_{task_id}"
                from handlers.task_settings_handlers import TaskSettingsHandlers
                await TaskSettingsHandlers.delay_settings_menu(update, context)
            else:
                await update.callback_query.answer("❌ فشل في تعيين التأخير")
                
        except Exception as e:
            await ErrorHandler.log_error(update, context, e, "quick_delay_set")
            await update.callback_query.answer("❌ حدث خطأ")
    
    @staticmethod
    async def add_whitelist_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """بدء إضافة مستخدم للقائمة البيضاء"""
        try:
            task_id = int(update.callback_query.data.split('_')[-1])
            context.user_data['current_task_id'] = task_id
            context.user_data['list_type'] = 'whitelist'
            
            text = """
➕ **إضافة للقائمة البيضاء**

أرسل **معرف المستخدم** (User ID):

💡 يمكنك الحصول على معرف المستخدم من @userinfobot
            """
            
            keyboard = [[InlineKeyboardButton("❌ إلغاء", callback_data=f"user_lists_{task_id}")]]
            
            await update.callback_query.edit_message_text(
                text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown'
            )
            
            from handlers.task_settings_handlers import WHITELIST_USER_INPUT
            return WHITELIST_USER_INPUT
            
        except Exception as e:
            await ErrorHandler.log_error(update, context, e, "add_whitelist_start")
            await update.callback_query.answer("❌ حدث خطأ")
            return ConversationHandler.END
    
    @staticmethod
    async def add_blacklist_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """بدء إضافة مستخدم للقائمة السوداء"""
        try:
            task_id = int(update.callback_query.data.split('_')[-1])
            context.user_data['current_task_id'] = task_id
            context.user_data['list_type'] = 'blacklist'
            
            text = """
➕ **إضافة للقائمة السوداء**

أرسل **معرف المستخدم** (User ID):

💡 يمكنك الحصول على معرف المستخدم من @userinfobot
            """
            
            keyboard = [[InlineKeyboardButton("❌ إلغاء", callback_data=f"user_lists_{task_id}")]]
            
            await update.callback_query.edit_message_text(
                text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown'
            )
            
            from handlers.task_settings_handlers import BLACKLIST_USER_INPUT
            return BLACKLIST_USER_INPUT
            
        except Exception as e:
            await ErrorHandler.log_error(update, context, e, "add_blacklist_start")
            await update.callback_query.answer("❌ حدث خطأ")
            return ConversationHandler.END
    
    @staticmethod
    async def user_list_input_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """استقبال معرف المستخدم للقائمة"""
        try:
            user_id_str = update.message.text.strip()
            task_id = context.user_data.get('current_task_id')
            list_type = context.user_data.get('list_type')
            
            # التحقق من صحة معرف المستخدم
            is_valid, user_id, message = DataValidator.validate_user_id(user_id_str)
            if not is_valid:
                await update.message.reply_text(message)
                return WHITELIST_USER_INPUT if list_type == 'whitelist' else BLACKLIST_USER_INPUT
            
            # إضافة المستخدم للقائمة
            success = await TaskManager.add_to_list(task_id, user_id, list_type)
            
            if success:
                list_name = "البيضاء" if list_type == 'whitelist' else "السوداء"
                text = f"✅ تم إضافة المستخدم `{user_id}` للقائمة {list_name}"
                keyboard = [
                    [
                        InlineKeyboardButton(f"➕ إضافة آخر", callback_data=f"add_{list_type}_{task_id}"),
                        InlineKeyboardButton("🔙 العودة", callback_data=f"user_lists_{task_id}")
                    ]
                ]
            else:
                text = "❌ فشل في إضافة المستخدم"
                keyboard = [[InlineKeyboardButton("🔙 العودة", callback_data=f"user_lists_{task_id}")]]
            
            await update.message.reply_text(
                text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown'
            )
            
            return ConversationHandler.END
            
        except Exception as e:
            await ErrorHandler.log_error(update, context, e, "user_list_input_received")
            await update.message.reply_text("❌ حدث خطأ أثناء إضافة المستخدم")
            return ConversationHandler.END

# دمج الكلاسات
TaskSettingsHandlers.select_all_media = TaskSettingsHandlersExtended.select_all_media
TaskSettingsHandlers.deselect_all_media = TaskSettingsHandlersExtended.deselect_all_media
TaskSettingsHandlers.add_required_word_start = TaskSettingsHandlersExtended.add_required_word_start
TaskSettingsHandlers.required_word_received = TaskSettingsHandlersExtended.required_word_received
TaskSettingsHandlers.add_replacement_start = TaskSettingsHandlersExtended.add_replacement_start
TaskSettingsHandlers.replacement_old_text_received = TaskSettingsHandlersExtended.replacement_old_text_received
TaskSettingsHandlers.replacement_new_text_received = TaskSettingsHandlersExtended.replacement_new_text_received
TaskSettingsHandlers.set_delay_start = TaskSettingsHandlersExtended.set_delay_start
TaskSettingsHandlers.delay_time_received = TaskSettingsHandlersExtended.delay_time_received
TaskSettingsHandlers.toggle_delay = TaskSettingsHandlersExtended.toggle_delay
TaskSettingsHandlers.quick_delay_set = TaskSettingsHandlersExtended.quick_delay_set
TaskSettingsHandlers.add_whitelist_start = TaskSettingsHandlersExtended.add_whitelist_start
TaskSettingsHandlers.add_blacklist_start = TaskSettingsHandlersExtended.add_blacklist_start
TaskSettingsHandlers.user_list_input_received = TaskSettingsHandlersExtended.user_list_input_received
TaskSettingsHandlers.toggle_advanced_filter = TaskSettingsHandlers.toggle_advanced_filter
