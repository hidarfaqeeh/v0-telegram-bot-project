# إضافة الثوابت المطلوبة
BLOCKED_WORD_INPUT = 1
REQUIRED_WORD_INPUT = 2
REPLACEMENT_OLD_TEXT = 3
REPLACEMENT_NEW_TEXT = 4
DELAY_TIME_INPUT = 5
WHITELIST_USER_INPUT = 6
BLACKLIST_USER_INPUT = 7
HEADER_TEXT_INPUT = 8
FOOTER_TEXT_INPUT = 9

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from database.task_manager import TaskManager
from utils.error_handler import ErrorHandler
from config import Config


class TaskSettingsHandlers:
    """
    Handlers for task settings management.
    """

    @staticmethod
    async def media_filters_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """قائمة فلاتر الوسائط"""
        try:
            task_id = int(update.callback_query.data.split('_')[-1])
            task = await TaskManager.get_task(task_id)
            
            if not task:
                await update.callback_query.answer("❌ المهمة غير موجودة")
                return
            
            # الحصول على إعدادات فلاتر الوسائط
            media_filters = task['settings'].get('media_filters', {})
            enabled = media_filters.get('enabled', True)
            allowed_types = media_filters.get('allowed_types', [])
            
            # إنشاء النص
            status = "🟢 مفعل" if enabled else "🔴 معطل"
            text = f"""
🎯 **فلاتر الوسائط**

📝 **المهمة:** {task['task_name']}
📊 **الحالة:** {status}

اختر أنواع الوسائط المسموح بها:
            """
            
            # إنشاء أزرار أنواع الوسائط
            keyboard = []
            media_types = [
                ('photo', '🖼️ صور'),
                ('video', '🎬 فيديو'),
                ('audio', '🎵 صوت'),
                ('document', '📄 ملفات'),
                ('voice', '🎤 تسجيل صوتي'),
                ('video_note', '⭕ فيديو دائري'),
                ('sticker', '😊 ملصقات'),
                ('animation', '🎭 صور متحركة')
            ]
            
            for media_type, label in media_types:
                status_icon = "✅" if media_type in allowed_types else "❌"
                keyboard.append([
                    InlineKeyboardButton(
                        f"{status_icon} {label}", 
                        callback_data=f"toggle_media_{media_type}_{task_id}"
                    )
                ])
            
            # أزرار إضافية
            filter_status = "تعطيل" if enabled else "تفعيل"
            keyboard.append([
                InlineKeyboardButton(
                    f"{'🔴' if enabled else '🟢'} {filter_status} الفلتر", 
                    callback_data=f"toggle_media_filter_{task_id}"
                )
            ])
            
            keyboard.append([
                InlineKeyboardButton("✅ تحديد الكل", callback_data=f"select_all_media_{task_id}"),
                InlineKeyboardButton("❌ إلغاء الكل", callback_data=f"deselect_all_media_{task_id}")
            ])
            
            keyboard.append([InlineKeyboardButton("🔙 العودة", callback_data=f"task_settings_{task_id}")])
            
            await update.callback_query.edit_message_text(
                text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown'
            )
            
        except Exception as e:
            await ErrorHandler.log_error(update, context, e, "media_filters_menu")
            await update.callback_query.answer("❌ حدث خطأ")

    @staticmethod
    async def toggle_media_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تبديل نوع وسائط"""
        try:
            data_parts = update.callback_query.data.split('_')
            media_type = data_parts[2]
            task_id = int(data_parts[3])
            
            task = await TaskManager.get_task(task_id)
            if not task:
                await update.callback_query.answer("❌ المهمة غير موجودة")
                return
            
            # الحصول على إعدادات فلاتر الوسائط
            media_filters = task['settings'].get('media_filters', {})
            allowed_types = media_filters.get('allowed_types', [])
            
            # تبديل حالة نوع الوسائط
            if media_type in allowed_types:
                allowed_types.remove(media_type)
            else:
                allowed_types.append(media_type)
            
            # تحديث الإعدادات
            success = await TaskManager.update_media_filters(task_id, allowed_types)
            
            if success:
                status = "إضافة" if media_type in allowed_types else "إزالة"
                await update.callback_query.answer(f"✅ تم {status} {media_type}")
                
                # إعادة عرض القائمة
                await TaskSettingsHandlers.media_filters_menu(update, context)
            else:
                await update.callback_query.answer("❌ فشل في تحديث الفلتر")
                
        except Exception as e:
            await ErrorHandler.log_error(update, context, e, "toggle_media_type")
            await update.callback_query.answer("❌ حدث خطأ")

    @staticmethod
    async def select_all_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تحديد جميع أنواع الوسائط"""
        try:
            task_id = int(update.callback_query.data.split('_')[-1])
            
            success = await TaskManager.update_media_filters(task_id, Config.SUPPORTED_MEDIA_TYPES.copy())
            
            if success:
                await update.callback_query.answer("✅ تم تحديد جميع أنواع الوسائط")
                # إعادة عرض القائمة
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
                await TaskSettingsHandlers.media_filters_menu(update, context)
            else:
                await update.callback_query.answer("❌ فشل في التحديث")
                
        except Exception as e:
            await ErrorHandler.log_error(update, context, e, "deselect_all_media")
            await update.callback_query.answer("❌ حدث خطأ")

    @staticmethod
    async def text_filters_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """قائمة فلاتر النص"""
        try:
            task_id = int(update.callback_query.data.split('_')[-1])
            task = await TaskManager.get_task(task_id)
            
            if not task:
                await update.callback_query.answer("❌ المهمة غير موجودة")
                return
            
            # الحصول على إعدادات فلاتر النص
            blocked_words = task['settings'].get('blocked_words', [])
            required_words = task['settings'].get('required_words', [])
            
            # إنشاء النص
            text = f"""
🔍 **فلاتر النص**

📝 **المهمة:** {task['task_name']}

🚫 **الكلمات المحظورة:** {len(blocked_words)}
✅ **الكلمات المطلوبة:** {len(required_words)}

اختر العملية التي تريد تنفيذها:
            """
            
            # إنشاء الأزرار
            keyboard = [
                [
                    InlineKeyboardButton("🚫 إضافة كلمة محظورة", callback_data=f"add_blocked_word_{task_id}"),
                    InlineKeyboardButton("✅ إضافة كلمة مطلوبة", callback_data=f"add_required_word_{task_id}")
                ],
                [
                    InlineKeyboardButton("📝 إدارة المحظورة", callback_data=f"manage_blocked_{task_id}"),
                    InlineKeyboardButton("📝 إدارة المطلوبة", callback_data=f"manage_required_{task_id}")
                ],
                [InlineKeyboardButton("🔙 العودة", callback_data=f"task_settings_{task_id}")]
            ]
            
            # إضافة قائمة الكلمات المحظورة والمطلوبة
            if blocked_words:
                text += "\n\n🚫 **الكلمات المحظورة:**\n"
                for i, word in enumerate(blocked_words[:5], 1):
                    text += f"{i}. `{word}`\n"
                if len(blocked_words) > 5:
                    text += f"... و {len(blocked_words) - 5} كلمات أخرى\n"
            
            if required_words:
                text += "\n✅ **الكلمات المطلوبة:**\n"
                for i, word in enumerate(required_words[:5], 1):
                    text += f"{i}. `{word}`\n"
                if len(required_words) > 5:
                    text += f"... و {len(required_words) - 5} كلمات أخرى\n"
            
            await update.callback_query.edit_message_text(
                text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown'
            )
            
        except Exception as e:
            await ErrorHandler.log_error(update, context, e, "text_filters_menu")
            await update.callback_query.answer("❌ حدث خطأ")

    @staticmethod
    async def add_blocked_word_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """بدء إضافة كلمة محظورة"""
        try:
            task_id = int(update.callback_query.data.split('_')[-1])
            context.user_data['current_task_id'] = task_id
            context.user_data['word_type'] = 'blocked'
            
            text = """
➕ **إضافة كلمة محظورة**

أرسل الكلمة أو العبارة المحظورة:

💡 الرسائل التي تحتوي على هذه الكلمة سيتم تجاهلها
            """
            
            keyboard = [[InlineKeyboardButton("❌ إلغاء", callback_data=f"text_filters_{task_id}")]]
            
            await update.callback_query.edit_message_text(
                text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown'
            )
            
            return BLOCKED_WORD_INPUT
            
        except Exception as e:
            await ErrorHandler.log_error(update, context, e, "add_blocked_word_start")
            await update.callback_query.answer("❌ حدث خطأ")
            return ConversationHandler.END

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
            
            return REQUIRED_WORD_INPUT
            
        except Exception as e:
            await ErrorHandler.log_error(update, context, e, "add_required_word_start")
            await update.callback_query.answer("❌ حدث خطأ")
            return ConversationHandler.END

    @staticmethod
    async def blocked_word_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """استقبال كلمة محظورة"""
        try:
            word = update.message.text.strip()
            task_id = context.user_data.get('current_task_id')
            
            # التحقق من صحة الكلمة
            from utils.validators import DataValidator
            is_valid, message = DataValidator.validate_word(word)
            if not is_valid:
                await update.message.reply_text(message)
                return BLOCKED_WORD_INPUT
            
            # الحصول على المهمة
            task = await TaskManager.get_task(task_id)
            if not task:
                await update.message.reply_text("❌ المهمة غير موجودة")
                return ConversationHandler.END
            
            # إضافة الكلمة
            blocked_words = task['settings'].get('blocked_words', [])
            required_words = task['settings'].get('required_words', [])
            
            if word not in blocked_words:
                blocked_words.append(word)
                
                success = await TaskManager.update_text_filters(task_id, blocked_words, required_words)
                
                if success:
                    text = f"✅ تم إضافة الكلمة المحظورة: **{word}**"
                    keyboard = [
                        [
                            InlineKeyboardButton("➕ إضافة كلمة أخرى", callback_data=f"add_blocked_word_{task_id}"),
                            InlineKeyboardButton("🔙 العودة", callback_data=f"text_filters_{task_id}")
                        ]
                    ]
                else:
                    text = "❌ فشل في إضافة الكلمة"
                    keyboard = [[InlineKeyboardButton("🔙 العودة", callback_data=f"text_filters_{task_id}")]]
            else:
                text = f"⚠️ الكلمة **{word}** موجودة مسبقاً في القائمة المحظورة"
                keyboard = [[InlineKeyboardButton("🔙 العودة", callback_data=f"text_filters_{task_id}")]]
            
            await update.message.reply_text(
                text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown'
            )
            
            return ConversationHandler.END
            
        except Exception as e:
            await ErrorHandler.log_error(update, context, e, "blocked_word_received")
            await update.message.reply_text("❌ حدث خطأ أثناء إضافة الكلمة")
            return ConversationHandler.END

    @staticmethod
    async def required_word_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """استقبال الكلمة المطلوبة"""
        try:
            word = update.message.text.strip()
            task_id = context.user_data.get('current_task_id')
            
            # التحقق من صحة الكلمة
            from utils.validators import DataValidator
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
    async def advanced_filters_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """قائمة الفلاتر المتقدمة"""
        try:
            task_id = int(update.callback_query.data.split('_')[-1])
            task = await TaskManager.get_task(task_id)
            
            if not task:
                await update.callback_query.answer("❌ المهمة غير موجودة")
                return
            
            # الحصول على إعدادات الفلاتر المتقدمة
            advanced_filters = task['settings'].get('advanced_filters', {})
            
            # إنشاء النص
            text = f"""
⚡ **الفلاتر المتقدمة**

📝 **المهمة:** {task['task_name']}

اختر الفلاتر التي تريد تفعيلها:
            """
            
            # إنشاء الأزرار
            filters_config = [
                ('block_links', '🔗 حظر الروابط'),
                ('block_mentions', '@️ حظر المعرفات'),
                ('block_forwarded', '↪️ حظر المعاد توجيهها'),
                ('block_inline_keyboards', '⌨️ حظر الأزرار')
            ]
            
            keyboard = []
            for filter_key, label in filters_config:
                status = advanced_filters.get(filter_key, False)
                status_icon = "✅" if status else "❌"
                keyboard.append([
                    InlineKeyboardButton(
                        f"{status_icon} {label}", 
                        callback_data=f"toggle_{filter_key.split('_')[1]}_filter_{task_id}"
                    )
                ])
            
            keyboard.append([InlineKeyboardButton("🔙 العودة", callback_data=f"task_settings_{task_id}")])
            
            await update.callback_query.edit_message_text(
                text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown'
            )
            
        except Exception as e:
            await ErrorHandler.log_error(update, context, e, "advanced_filters_menu")
            await update.callback_query.answer("❌ حدث خطأ")

    @staticmethod
    async def toggle_advanced_filter(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تبديل فلتر متقدم"""
        try:
            data_parts = update.callback_query.data.split('_')
            filter_type = data_parts[1]  # link, mention, forward, keyboard, media
            task_id = int(data_parts[-1])

            task = await TaskManager.get_task(task_id)
            if not task:
                await update.callback_query.answer("❌ المهمة غير موجودة")
                return

            if filter_type == 'media':
                # تبديل حالة فلتر الوسائط
                media_filters = task['settings'].get('media_filters', {})
                current_state = media_filters.get('enabled', True)
                media_filters['enabled'] = not current_state

                # الحفاظ على الأنواع المحددة
                if 'allowed_types' not in media_filters:
                    from config import Config
                    media_filters['allowed_types'] = Config.SUPPORTED_MEDIA_TYPES.copy()

                success = await TaskManager.update_media_filters(task_id, media_filters['allowed_types'])
                if success:
                    # تحديث حالة التفعيل
                    task = await TaskManager.get_task(task_id)
                    settings = task['settings']
                    settings['media_filters']['enabled'] = not current_state
                    await TaskManager.update_task_settings(task_id, settings)
            else:
                # فلاتر متقدمة أخرى
                advanced_filters = task['settings'].get('advanced_filters', {})

                # تحديد نوع الفلتر
                filter_key = {
                    'link': 'block_links',
                    'mention': 'block_mentions',
                    'forward': 'block_forwarded',
                    'keyboard': 'block_inline_keyboards'
                }.get(filter_type)

                if filter_key:
                    # تبديل الحالة
                    current_state = advanced_filters.get(filter_key, False)
                    advanced_filters[filter_key] = not current_state

                    success = await TaskManager.update_advanced_filters(task_id, advanced_filters)
                else:
                    await update.callback_query.answer("❌ نوع فلتر غير صحيح")
                    return

            if success:
                state_text = "تم تفعيل" if not current_state else "تم تعطيل"
                await update.callback_query.answer(f"✅ {state_text} الفلتر")

                # إعادة عرض القائمة المناسبة
                if filter_type == 'media':
                    context.user_data['callback_data'] = f"media_filters_{task_id}"
                    await TaskSettingsHandlers.media_filters_menu(update, context)
                else:
                    context.user_data['callback_data'] = f"advanced_filters_{task_id}"
                    await TaskSettingsHandlers.advanced_filters_menu(update, context)
            else:
                await update.callback_query.answer("❌ فشل في تحديث الفلتر")

        except Exception as e:
            await ErrorHandler.log_error(update, context, e, "toggle_advanced_filter")
            await update.callback_query.answer("❌ حدث خطأ أثناء تحديث الفلتر")

    @staticmethod
    async def replacements_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """قائمة الاستبدالات"""
        try:
            task_id = int(update.callback_query.data.split('_')[-1])
            task = await TaskManager.get_task(task_id)
            
            if not task:
                await update.callback_query.answer("❌ المهمة غير موجودة")
                return
            
            # الحصول على إعدادات الاستبدالات
            replacements = task['settings'].get('replacements', {})
            
            # إنشاء النص
            text = f"""
🔄 **الاستبدالات**

📝 **المهمة:** {task['task_name']}
📊 **عدد الاستبدالات:** {len(replacements)}

اختر العملية التي تريد تنفيذها:
            """
            
            # إنشاء الأزرار
            keyboard = [
                [InlineKeyboardButton("➕ إضافة استبدال", callback_data=f"add_replacement_{task_id}")],
                [InlineKeyboardButton("📝 إدارة الاستبدالات", callback_data=f"manage_replacements_{task_id}")],
                [InlineKeyboardButton("🔙 العودة", callback_data=f"task_settings_{task_id}")]
            ]
            
            # إضافة قائمة الاستبدالات
            if replacements:
                text += "\n\n**الاستبدالات الحالية:**\n"
                count = 0
                for old_text, new_text in replacements.items():
                    if count < 5:
                        text += f"• `{old_text}` ➡️ `{new_text}`\n"
                        count += 1
                    else:
                        break
                
                if len(replacements) > 5:
                    text += f"\n... و {len(replacements) - 5} استبدالات أخرى"
            
            await update.callback_query.edit_message_text(
                text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown'
            )
            
        except Exception as e:
            await ErrorHandler.log_error(update, context, e, "replacements_menu")
            await update.callback_query.answer("❌ حدث خطأ")

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
            from utils.validators import DataValidator
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
            from utils.validators import DataValidator
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
    async def delay_settings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """قائمة إعدادات التأخير"""
        try:
            task_id = int(update.callback_query.data.split('_')[-1])
            task = await TaskManager.get_task(task_id)
            
            if not task:
                await update.callback_query.answer("❌ المهمة غير موجودة")
                return
            
            # الحصول على إعدادات التأخير
            delay_settings = task['settings'].get('delay', {})
            enabled = delay_settings.get('enabled', False)
            seconds = delay_settings.get('seconds', 0)
            
            # إنشاء النص
            status = "🟢 مفعل" if enabled else "🔴 معطل"
            text = f"""
⏰ **إعدادات التأخير**

📝 **المهمة:** {task['task_name']}
📊 **الحالة:** {status}
⏱️ **التأخير:** {seconds} ثانية

اختر العملية التي تريد تنفيذها:
            """
            
            # إنشاء الأزرار
            keyboard = [
                [InlineKeyboardButton("⏱️ تعيين وقت التأخير", callback_data=f"set_delay_{task_id}")],
                [
                    InlineKeyboardButton(
                        f"{'🔴 تعطيل' if enabled else '🟢 تفعيل'} التأخير", 
                        callback_data=f"toggle_delay_{task_id}"
                    )
                ],
                [
                    InlineKeyboardButton("5 ثوان", callback_data=f"quick_delay_5_{task_id}"),
                    InlineKeyboardButton("30 ثانية", callback_data=f"quick_delay_30_{task_id}"),
                    InlineKeyboardButton("دقيقة", callback_data=f"quick_delay_60_{task_id}")
                ],
                [InlineKeyboardButton("🔙 العودة", callback_data=f"task_settings_{task_id}")]
            ]
            
            await update.callback_query.edit_message_text(
                text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown'
            )
            
        except Exception as e:
            await ErrorHandler.log_error(update, context, e, "delay_settings_menu")
            await update.callback_query.answer("❌ حدث خطأ")

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
            from utils.validators import DataValidator
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
                await TaskSettingsHandlers.delay_settings_menu(update, context)
            else:
                await update.callback_query.answer("❌ فشل في تعيين التأخير")
                
        except Exception as e:
            await ErrorHandler.log_error(update, context, e, "quick_delay_set")
            await update.callback_query.answer("❌ حدث خطأ")

    @staticmethod
    async def user_lists_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """قائمة قوائم المستخدمين"""
        try:
            task_id = int(update.callback_query.data.split('_')[-1])
            task = await TaskManager.get_task(task_id)
            
            if not task:
                await update.callback_query.answer("❌ المهمة غير موجودة")
                return
            
            # الحصول على إعدادات القوائم
            whitelist = task['settings'].get('whitelist', [])
            blacklist = task['settings'].get('blacklist', [])
            
            # إنشاء النص
            text = f"""
👥 **قوائم المستخدمين**

📝 **المهمة:** {task['task_name']}
⚪ **القائمة البيضاء:** {len(whitelist)} مستخدم
⚫ **القائمة السوداء:** {len(blacklist)} مستخدم

اختر العملية التي تريد تنفيذها:
            """
            
            # إنشاء الأزرار
            keyboard = [
                [
                    InlineKeyboardButton("➕ إضافة للقائمة البيضاء", callback_data=f"add_whitelist_{task_id}"),
                    InlineKeyboardButton("➕ إضافة للقائمة السوداء", callback_data=f"add_blacklist_{task_id}")
                ],
                [
                    InlineKeyboardButton("📝 إدارة القائمة البيضاء", callback_data=f"manage_whitelist_{task_id}"),
                    InlineKeyboardButton("📝 إدارة القائمة السوداء", callback_data=f"manage_blacklist_{task_id}")
                ],
                [InlineKeyboardButton("🔙 العودة", callback_data=f"task_settings_{task_id}")]
            ]
            
            # إضافة قائمة المستخدمين
            if whitelist:
                text += "\n\n⚪ **القائمة البيضاء:**\n"
                for i, user_id in enumerate(whitelist[:5], 1):
                    text += f"{i}. `{user_id}`\n"
                if len(whitelist) > 5:
                    text += f"... و {len(whitelist) - 5} مستخدمين آخرين\n"
            
            if blacklist:
                text += "\n⚫ **القائمة السوداء:**\n"
                for i, user_id in enumerate(blacklist[:5], 1):
                    text += f"{i}. `{user_id}`\n"
                if len(blacklist) > 5:
                    text += f"... و {len(blacklist) - 5} مستخدمين آخرين\n"
            
            await update.callback_query.edit_message_text(
                text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown'
            )
            
        except Exception as e:
            await ErrorHandler.log_error(update, context, e, "user_lists_menu")
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
            
            return BLACKLIST_USER_INPUT
            
        except Exception as e:
            await ErrorHandler.log_error(update, context, e, "add_blacklist_start")
            await update.callback_query.answer("❌ حدث خطأ")
            return ConversationHandler.END

    @staticmethod
    async def whitelist_user_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """استقبال معرف المستخدم للقائمة البيضاء"""
        try:
            user_id_str = update.message.text.strip()
            task_id = context.user_data.get('current_task_id')
            
            # التحقق من صحة معرف المستخدم
            from utils.validators import DataValidator
            is_valid, user_id, message = DataValidator.validate_user_id(user_id_str)
            if not is_valid:
                await update.message.reply_text(message)
                return WHITELIST_USER_INPUT
            
            # إضافة المستخدم للقائمة البيضاء
            success = await TaskManager.add_to_list(task_id, user_id, 'whitelist')
            
            if success:
                text = f"✅ تم إضافة المستخدم `{user_id}` للقائمة البيضاء"
                keyboard = [
                    [
                        InlineKeyboardButton("➕ إضافة مستخدم آخر", callback_data=f"add_whitelist_{task_id}"),
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
            await ErrorHandler.log_error(update, context, e, "whitelist_user_received")
            await update.message.reply_text("❌ حدث خطأ أثناء إضافة المستخدم")
            return ConversationHandler.END

    @staticmethod
    async def blacklist_user_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """استقبال معرف المستخدم للقائمة السوداء"""
        try:
            user_id_str = update.message.text.strip()
            task_id = context.user_data.get('current_task_id')
            
            # التحقق من صحة معرف المستخدم
            from utils.validators import DataValidator
            is_valid, user_id, message = DataValidator.validate_user_id(user_id_str)
            if not is_valid:
                await update.message.reply_text(message)
                return BLACKLIST_USER_INPUT
            
            # إضافة المستخدم للقائمة السوداء
            success = await TaskManager.add_to_list(task_id, user_id, 'blacklist')
            
            if success:
                text = f"✅ تم إضافة المستخدم `{user_id}` للقائمة السوداء"
                keyboard = [
                    [
                        InlineKeyboardButton("➕ إضافة مستخدم آخر", callback_data=f"add_blacklist_{task_id}"),
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
            await ErrorHandler.log_error(update, context, e, "blacklist_user_received")
            await update.message.reply_text("❌ حدث خطأ أثناء إضافة المستخدم")
            return ConversationHandler.END

    @staticmethod
    async def manage_blocked_words(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """إدارة الكلمات المحظورة"""
        try:
            task_id = int(update.callback_query.data.split('_')[-1])
            task = await TaskManager.get_task(task_id)
            
            if not task:
                await update.callback_query.answer("❌ المهمة غير موجودة")
                return
            
            # الحصول على الكلمات المحظورة
            blocked_words = task['settings'].get('blocked_words', [])
            
            # إنشاء النص
            text = f"""
📝 **إدارة الكلمات المحظورة**

📝 **المهمة:** {task['task_name']}
📊 **عدد الكلمات:** {len(blocked_words)}

اختر الكلمة التي تريد حذفها:
            """
            
            # إنشاء الأزرار
            keyboard = []
            for i, word in enumerate(blocked_words[:10]):
                keyboard.append([
                    InlineKeyboardButton(
                        f"❌ {word}", 
                        callback_data=f"remove_blocked_{i}_{task_id}"
                    )
                ])
            
            keyboard.append([InlineKeyboardButton("🔙 العودة", callback_data=f"text_filters_{task_id}")])
            
            await update.callback_query.edit_message_text(
                text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown'
            )
            
        except Exception as e:
            await ErrorHandler.log_error(update, context, e, "manage_blocked_words")
            await update.callback_query.answer("❌ حدث خطأ")

    @staticmethod
    async def manage_required_words(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """إدارة الكلمات المطلوبة"""
        try:
            task_id = int(update.callback_query.data.split('_')[-1])
            task = await TaskManager.get_task(task_id)
            
            if not task:
                await update.callback_query.answer("❌ المهمة غير موجودة")
                return
            
            # الحصول على الكلمات المطلوبة
            required_words = task['settings'].get('required_words', [])
            
            # إنشاء النص
            text = f"""
📝 **إدارة الكلمات المطلوبة**

📝 **المهمة:** {task['task_name']}
📊 **عدد الكلمات:** {len(required_words)}

اختر الكلمة التي تريد حذفها:
            """
            
            # إنشاء الأزرار
            keyboard = []
            for i, word in enumerate(required_words[:10]):
                keyboard.append([
                    InlineKeyboardButton(
                        f"❌ {word}", 
                        callback_data=f"remove_required_{i}_{task_id}"
                    )
                ])
            
            keyboard.append([InlineKeyboardButton("🔙 العودة", callback_data=f"text_filters_{task_id}")])
            
            await update.callback_query.edit_message_text(
                text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown'
            )
            
        except Exception as e:
            await ErrorHandler.log_error(update, context, e, "manage_required_words")
            await update.callback_query.answer("❌ حدث خطأ")

    @staticmethod
    async def manage_whitelist(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """إدارة القائمة البيضاء"""
        try:
            task_id = int(update.callback_query.data.split('_')[-1])
            task = await TaskManager.get_task(task_id)
            
            if not task:
                await update.callback_query.answer("❌ المهمة غير موجودة")
                return
            
            # الحصول على القائمة البيضاء
            whitelist = task['settings'].get('whitelist', [])
            
            # إنشاء النص
            text = f"""
📝 **إدارة القائمة البيضاء**

📝 **المهمة:** {task['task_name']}
📊 **عدد المستخدمين:** {len(whitelist)}

اختر المستخدم الذي تريد حذفه:
            """
            
            # إنشاء الأزرار
            keyboard = []
            for i, user_id in enumerate(whitelist[:10]):
                keyboard.append([
                    InlineKeyboardButton(
                        f"❌ {user_id}", 
                        callback_data=f"remove_whitelist_{i}_{task_id}"
                    )
                ])
            
            keyboard.append([InlineKeyboardButton("🔙 العودة", callback_data=f"user_lists_{task_id}")])
            
            await update.callback_query.edit_message_text(
                text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown'
            )
            
        except Exception as e:
            await ErrorHandler.log_error(update, context, e, "manage_whitelist")
            await update.callback_query.answer("❌ حدث خطأ")

    @staticmethod
    async def manage_blacklist(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """إدارة القائمة السوداء"""
        try:
            task_id = int(update.callback_query.data.split('_')[-1])
            task = await TaskManager.get_task(task_id)
            
            if not task:
                await update.callback_query.answer("❌ المهمة غير موجودة")
                return
            
            # الحصول على القائمة السوداء
            blacklist = task['settings'].get('blacklist', [])
            
            # إنشاء النص
            text = f"""
📝 **إدارة القائمة السوداء**

📝 **المهمة:** {task['task_name']}
📊 **عدد المستخدمين:** {len(blacklist)}

اختر المستخدم الذي تريد حذفه:
            """
            
            # إنشاء الأزرار
            keyboard = []
            for i, user_id in enumerate(blacklist[:10]):
                keyboard.append([
                    InlineKeyboardButton(
                        f"❌ {user_id}", 
                        callback_data=f"remove_blacklist_{i}_{task_id}"
                    )
                ])
            
            keyboard.append([InlineKeyboardButton("🔙 العودة", callback_data=f"user_lists_{task_id}")])
            
            await update.callback_query.edit_message_text(
                text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown'
            )
            
        except Exception as e:
            await ErrorHandler.log_error(update, context, e, "manage_blacklist")
            await update.callback_query.answer("❌ حدث خطأ")

    @staticmethod
    async def manage_replacements(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """إدارة الاستبدالات"""
        try:
            task_id = int(update.callback_query.data.split('_')[-1])
            task = await TaskManager.get_task(task_id)
            
            if not task:
                await update.callback_query.answer("❌ المهمة غير موجودة")
                return
            
            # الحصول على الاستبدالات
            replacements = task['settings'].get('replacements', {})
            
            # إنشاء النص
            text = f"""
📝 **إدارة الاستبدالات**

📝 **المهمة:** {task['task_name']}
📊 **عدد الاستبدالات:** {len(replacements)}

اختر الاستبدال الذي تريد حذفه:
            """
            
            # إنشاء الأزرار
            keyboard = []
            for i, (old_text, new_text) in enumerate(list(replacements.items())[:10]):
                keyboard.append([
                    InlineKeyboardButton(
                        f"❌ {old_text} ➡️ {new_text}", 
                        callback_data=f"remove_replacement_{i}_{task_id}"
                    )
                ])
            
            keyboard.append([InlineKeyboardButton("🔙 العودة", callback_data=f"replacements_{task_id}")])
            
            await update.callback_query.edit_message_text(
                text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown'
            )
            
        except Exception as e:
            await ErrorHandler.log_error(update, context, e, "manage_replacements")
            await update.callback_query.answer("❌ حدث خطأ")

    @staticmethod
    async def remove_blocked_word(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """حذف كلمة محظورة"""
        try:
            data_parts = update.callback_query.data.split('_')
            word_index = int(data_parts[2])
            task_id = int(data_parts[3])
            
            task = await TaskManager.get_task(task_id)
            if not task:
                await update.callback_query.answer("❌ المهمة غير موجودة")
                return
            
            # الحصول على الكلمات المحظورة
            blocked_words = task['settings'].get('blocked_words', [])
            required_words = task['settings'].get('required_words', [])
            
            # حذف الكلمة
            if 0 <= word_index < len(blocked_words):
                removed_word = blocked_words.pop(word_index)
                
                success = await TaskManager.update_text_filters(task_id, blocked_words, required_words)
                
                if success:
                    await update.callback_query.answer(f"✅ تم حذف الكلمة: {removed_word}")
                else:
                    await update.callback_query.answer("❌ فشل في حذف الكلمة")
            else:
                await update.callback_query.answer("❌ فهرس الكلمة غير صالح")
            
            # إعادة عرض قائمة الكلمات المحظورة
            await TaskSettingsHandlers.manage_blocked_words(update, context)
            
        except Exception as e:
            await ErrorHandler.log_error(update, context, e, "remove_blocked_word")
            await update.callback_query.answer("❌ حدث خطأ")

    @staticmethod
    async def remove_required_word(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """حذف كلمة مطلوبة"""
        try:
            data_parts = update.callback_query.data.split('_')
            word_index = int(data_parts[2])
            task_id = int(data_parts[3])
            
            task = await TaskManager.get_task(task_id)
            if not task:
                await update.callback_query.answer("❌ المهمة غير موجودة")
                return
            
            # الحصول على الكلمات المطلوبة
            blocked_words = task['settings'].get('blocked_words', [])
            required_words = task['settings'].get('required_words', [])
            
            # حذف الكلمة
            if 0 <= word_index < len(required_words):
                removed_word = required_words.pop(word_index)
                
                success = await TaskManager.update_text_filters(task_id, blocked_words, required_words)
                
                if success:
                    await update.callback_query.answer(f"✅ تم حذف الكلمة: {removed_word}")
                else:
                    await update.callback_query.answer("❌ فشل في حذف الكلمة")
            else:
                await update.callback_query.answer("❌ فهرس الكلمة غير صالح")
            
            # إعادة عرض قائمة الكلمات المطلوبة
            await TaskSettingsHandlers.manage_required_words(update, context)
            
        except Exception as e:
            await ErrorHandler.log_error(update, context, e, "remove_required_word")
            await update.callback_query.answer("❌ حدث خطأ")

    @staticmethod
    async def remove_whitelist_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """حذف مستخدم من القائمة البيضاء"""
        try:
            data_parts = update.callback_query.data.split('_')
            user_index = int(data_parts[2])
            task_id = int(data_parts[3])
            
            task = await TaskManager.get_task(task_id)
            if not task:
                await update.callback_query.answer("❌ المهمة غير موجودة")
                return
            
            # الحصول على القائمة البيضاء
            whitelist = task['settings'].get('whitelist', [])
            
            # حذف المستخدم
            if 0 <= user_index < len(whitelist):
                removed_user = whitelist.pop(user_index)
                
                success = await TaskManager.update_user_lists(task_id, whitelist, 'whitelist')
                
                if success:
                    await update.callback_query.answer(f"✅ تم حذف المستخدم: {removed_user}")
                else:
                    await update.callback_query.answer("❌ فشل في حذف المستخدم")
            else:
                await update.callback_query.answer("❌ فهرس المستخدم غير صالح")
            
            # إعادة عرض قائمة المستخدمين في القائمة البيضاء
            await TaskSettingsHandlers.manage_whitelist(update, context)
            
        except Exception as e:
            await ErrorHandler.log_error(update, context, e, "remove_whitelist_user")
            await update.callback_query.answer("❌ حدث خطأ")

    @staticmethod
    async def remove_blacklist_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """حذف مستخدم من القائمة السوداء"""
        try:
            data_parts = update.callback_query.data.split('_')
            user_index = int(data_parts[2])
            task_id = int(data_parts[3])
            
            task = await TaskManager.get_task(task_id)
            if not task:
                await update.callback_query.answer("❌ المهمة غير موجودة")
                return
            
            # الحصول على القائمة السوداء
            blacklist = task['settings'].get('blacklist', [])
            
            # حذف المستخدم
            if 0 <= user_index < len(blacklist):
                removed_user = blacklist.pop(user_index)
                
                success = await TaskManager.update_user_lists(task_id, blacklist, 'blacklist')
                
                if success:
                    await update.callback_query.answer(f"✅ تم حذف المستخدم: {removed_user}")
                else:
                    await update.callback_query.answer("❌ فشل في حذف المستخدم")
            else:
                await update.callback_query.answer("❌ فهرس المستخدم غير صالح")
            
            # إعادة عرض قائمة المستخدمين في القائمة السوداء
            await TaskSettingsHandlers.manage_blacklist(update, context)
            
        except Exception as e:
            await ErrorHandler.log_error(update, context, e, "remove_blacklist_user")
            await update.callback_query.answer("❌ حدث خطأ")

    @staticmethod
    async def remove_replacement(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """حذف استبدال"""
        try:
            data_parts = update.callback_query.data.split('_')
            replacement_index = int(data_parts[2])
            task_id = int(data_parts[3])
            
            task = await TaskManager.get_task(task_id)
            if not task:
                await update.callback_query.answer("❌ المهمة غير موجودة")
                return
            
            # الحصول على الاستبدالات
            replacements = task['settings'].get('replacements', {})
            
            # حذف الاستبدال
            replacement_list = list(replacements.items())
            if 0 <= replacement_index < len(replacement_list):
                old_text, new_text = replacement_list.pop(replacement_index)
                del replacements[old_text]
                
                success = await TaskManager.update_replacements(task_id, replacements)
                
                if success:
                    await update.callback_query.answer(f"✅ تم حذف الاستبدال: {old_text} ➡️ {new_text}")
                else:
                    await update.callback_query.answer("❌ فشل في حذف الاستبدال")
            else:
                await update.callback_query.answer("❌ فهرس الاستبدال غير صالح")
            
            # إعادة عرض قائمة الاستبدالات
            await TaskSettingsHandlers.manage_replacements(update, context)
            
        except Exception as e:
            await ErrorHandler.log_error(update, context, e, "remove_replacement")
            await update.callback_query.answer("❌ حدث خطأ")
