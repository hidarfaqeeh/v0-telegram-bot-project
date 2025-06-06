from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from database.task_manager import TaskManager
from database.statistics_manager import StatisticsManager
from utils.keyboard_builder import KeyboardBuilder
from utils.message_processor import MessageProcessor
import json
from utils.validators import InputValidator
from utils.decorators import admin_required, error_handler

# Conversation states
TASK_NAME, SOURCE_CHAT, TARGET_CHAT, TASK_TYPE = range(4)

class TaskHandlers:
    @staticmethod
    async def tasks_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show tasks menu"""
        keyboard = KeyboardBuilder.tasks_menu()
        
        text = """
📋 **إدارة المهام**

اختر العملية التي تريد تنفيذها:
        """
        
        await update.callback_query.edit_message_text(
            text, reply_markup=keyboard, parse_mode='Markdown'
        )
    
    @staticmethod
    async def create_task_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start creating new task"""
        text = """
➕ **إنشاء مهمة جديدة**

أرسل اسم المهمة:
        """
        
        keyboard = [[InlineKeyboardButton("❌ إلغاء", callback_data="tasks_menu")]]
        
        await update.callback_query.edit_message_text(
            text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown'
        )
        
        return TASK_NAME
    
    @staticmethod
    @error_handler
    async def task_name_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """استقبال اسم المهمة"""
        try:
            task_name_str = update.message.text.strip()
            
            # التحقق من صحة اسم المهمة
            is_valid, task_name, message = InputValidator.validate_task_name(task_name_str)
            
            if not is_valid:
                await update.message.reply_text(
                    f"{message}\n\n🔄 يرجى إدخال اسم مهمة صحيح:",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("❌ إلغاء", callback_data="tasks_menu")
                    ]])
                )
                return TASK_NAME
            
            # التحقق من عدم وجود مهمة بنفس الاسم
            existing_task = await TaskHandlers.task_manager.get_task_by_name(task_name)
            if existing_task:
                await update.message.reply_text(
                    f"❌ يوجد مهمة بنفس الاسم: {task_name}\n\n🔄 يرجى اختيار اسم آخر:",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("❌ إلغاء", callback_data="tasks_menu")
                    ]])
                )
                return TASK_NAME
            
            # حفظ اسم المهمة
            context.user_data['task_name'] = task_name
            
            # تسجيل النشاط
            await TaskHandlers.activity_manager.log_activity(
                user_id=update.effective_user.id,
                action="task_name_entered",
                details=f"تم إدخال اسم المهمة: {task_name}"
            )
            
            text = f"""
✅ اسم المهمة: **{task_name}**

**الخطوة 2: معرف المحادثة المصدر**

يرجى إدخال معرف المحادثة التي تريد إعادة توجيه الرسائل منها:

💡 **كيفية الحصول على معرف المحادثة:**
• للمجموعات: استخدم @userinfobot
• للقنوات: أضف البوت كمدير واستخدم /id
• للمحادثات الخاصة: معرف المستخدم

⚠️ **مثال:** -1001234567890 أو @channel_username
            """
            
            keyboard = [[InlineKeyboardButton("❌ إلغاء", callback_data="tasks_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
            
            return SOURCE_CHAT
            
        except Exception as e:
            logger.error(f"خطأ في استقبال اسم المهمة: {e}")
            await update.message.reply_text("❌ حدث خطأ في معالجة اسم المهمة")
            return ConversationHandler.END
    
    @staticmethod
    @error_handler
    async def source_chat_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """استقبال معرف المحادثة المصدر"""
        try:
            source_input = update.message.text.strip()
            
            # التحقق من نوع الإدخال (معرف أو اسم مستخدم)
            if source_input.startswith('@'):
                # اسم مستخدم
                is_valid, username, message = InputValidator.validate_username(source_input)
                if not is_valid:
                    await update.message.reply_text(
                        f"{message}\n\n🔄 يرجى إدخال معرف صحيح:",
                        reply_markup=InlineKeyboardMarkup([[
                            InlineKeyboardButton("❌ إلغاء", callback_data="tasks_menu")
                        ]])
                    )
                    return SOURCE_CHAT
                source_chat_id = username
            else:
                # معرف رقمي
                is_valid, chat_id, message = InputValidator.validate_chat_id(source_input)
                if not is_valid:
                    await update.message.reply_text(
                        f"{message}\n\n🔄 يرجى إدخال معرف صحيح:",
                        reply_markup=InlineKeyboardMarkup([[
                            InlineKeyboardButton("❌ إلغاء", callback_data="tasks_menu")
                        ]])
                    )
                    return SOURCE_CHAT
                source_chat_id = chat_id
            
            # حفظ معرف المحادثة المصدر
            context.user_data['source_chat_id'] = source_chat_id
            
            # تسجيل النشاط
            await TaskHandlers.activity_manager.log_activity(
                user_id=update.effective_user.id,
                action="source_chat_entered",
                details=f"تم إدخال المحادثة المصدر: {source_chat_id}"
            )
            
            text = f"""
✅ المحادثة المصدر: **{source_chat_id}**

**الخطوة 3: معرف المحادثة الهدف**

يرجى إدخال معرف المحادثة التي تريد إعادة توجيه الرسائل إليها:

💡 **ملاحظات:**
• يجب أن يكون البوت عضواً في المحادثة الهدف
• يجب أن يكون للبوت صلاحية إرسال الرسائل
• يمكن أن تكون نفس المحادثة المصدر

⚠️ **مثال:** -1001234567890 أو @target_channel
            """
            
            keyboard = [[InlineKeyboardButton("❌ إلغاء", callback_data="tasks_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
            
            return TARGET_CHAT
            
        except Exception as e:
            logger.error(f"خطأ في استقبال المحادثة المصدر: {e}")
            await update.message.reply_text("❌ حدث خطأ في معالجة المحادثة المصدر")
            return ConversationHandler.END
    
    @staticmethod
    @error_handler
    async def target_chat_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """استقبال معرف المحادثة الهدف وإنشاء المهمة"""
        try:
            target_input = update.message.text.strip()
            
            # التحقق من نوع الإدخال (معرف أو اسم مستخدم)
            if target_input.startswith('@'):
                # اسم مستخدم
                is_valid, username, message = InputValidator.validate_username(target_input)
                if not is_valid:
                    await update.message.reply_text(
                        f"{message}\n\n🔄 يرجى إدخال معرف صحيح:",
                        reply_markup=InlineKeyboardMarkup([[
                            InlineKeyboardButton("❌ إلغاء", callback_data="tasks_menu")
                        ]])
                    )
                    return TARGET_CHAT
                target_chat_id = username
            else:
                # معرف رقمي
                is_valid, chat_id, message = InputValidator.validate_chat_id(target_input)
                if not is_valid:
                    await update.message.reply_text(
                        f"{message}\n\n🔄 يرجى إدخال معرف صحيح:",
                        reply_markup=InlineKeyboardMarkup([[
                            InlineKeyboardButton("❌ إلغاء", callback_data="tasks_menu")
                        ]])
                    )
                    return TARGET_CHAT
                target_chat_id = chat_id
            
            # إنشاء المهمة في قاعدة البيانات
            task_data = {
                'name': context.user_data['task_name'],
                'source_chat_id': context.user_data['source_chat_id'],
                'target_chat_id': target_chat_id,
                'created_by': update.effective_user.id,
                'is_active': True,
                'settings': {
                    'media_filters': ['photo', 'video', 'document', 'audio', 'voice', 'sticker'],
                    'text_filters': {'enabled': True, 'keywords': []},
                    'time_filters': {'enabled': False, 'start_time': None, 'end_time': None},
                    'delay_seconds': 0,
                    'delete_original': False
                }
            }
            
            task_id = await TaskHandlers.task_manager.create_task(task_data)
            
            # تسجيل النشاط
            await TaskHandlers.activity_manager.log_activity(
                user_id=update.effective_user.id,
                action="task_created",
                details=f"تم إنشاء المهمة: {task_data['name']} (ID: {task_id})"
            )
            
            # تنظيف البيانات المؤقتة
            context.user_data.clear()
            
            text = f"""
🎉 **تم إنشاء المهمة بنجاح!**

**تفاصيل المهمة:**
• **الاسم:** {task_data['name']}
• **المصدر:** {task_data['source_chat_id']}
• **الهدف:** {target_chat_id}
• **الحالة:** 🟢 نشطة
• **معرف المهمة:** {task_id}

**الإعدادات الافتراضية:**
✅ جميع أنواع الوسائط مفعلة
✅ إعادة توجيه النصوص مفعلة
⏰ بدون تأخير زمني
🗑️ عدم حذف الرسائل الأصلية

يمكنك تخصيص هذه الإعدادات من قائمة إدارة المهام.
            """
            
            keyboard = [
                [InlineKeyboardButton("⚙️ تخصيص الإعدادات", callback_data=f"task_settings_{task_id}")],
                [InlineKeyboardButton("📋 عرض تفاصيل المهمة", callback_data=f"task_details_{task_id}")],
                [InlineKeyboardButton("📝 إنشاء مهمة أخرى", callback_data="create_task")],
                [InlineKeyboardButton("🔙 العودة لقائمة المهام", callback_data="tasks_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
            
            return ConversationHandler.END
            
        except Exception as e:
            logger.error(f"خطأ في إنشاء المهمة: {e}")
            await update.message.reply_text("❌ حدث خطأ في إنشاء المهمة")
            return ConversationHandler.END
    
    @staticmethod
    async def task_type_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Task type selected"""
        task_type = update.callback_query.data.split('_')[-1]  # forward or copy
        
        # Create task
        user_id = update.effective_user.id
        task_id = await TaskManager.create_task(
            user_id=user_id,
            task_name=context.user_data['task_name'],
            source_chat_id=context.user_data['source_chat_id'],
            target_chat_id=context.user_data['target_chat_id'],
            task_type=task_type
        )
        
        if task_id:
            text = f"""
✅ **تم إنشاء المهمة بنجاح!**

📝 **اسم المهمة:** {context.user_data['task_name']}
🆔 **رقم المهمة:** {task_id}
📥 **محادثة المصدر:** {context.user_data['source_chat_id']}
📤 **محادثة الهدف:** {context.user_data['target_chat_id']}
🔄 **نوع التوجيه:** {'توجيه' if task_type == 'forward' else 'نسخ'}

يمكنك الآن تخصيص إعدادات المهمة.
            """
            
            keyboard = [
                [InlineKeyboardButton("⚙️ إعدادات المهمة", callback_data=f"task_settings_{task_id}")],
                [InlineKeyboardButton("📋 عرض المهام", callback_data="view_tasks")]
            ]
        else:
            text = "❌ حدث خطأ أثناء إنشاء المهمة. يرجى المحاولة مرة أخرى."
            keyboard = [[InlineKeyboardButton("🔙 العودة", callback_data="tasks_menu")]]
        
        await update.callback_query.edit_message_text(
            text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown'
        )
        
        # Clear user data
        context.user_data.clear()
        return ConversationHandler.END
    
    @staticmethod
    async def view_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """View user tasks"""
        user_id = update.effective_user.id
        tasks = await TaskManager.get_user_tasks(user_id)
        
        if not tasks:
            text = "📭 لا توجد مهام مسجلة"
            keyboard = [[InlineKeyboardButton("➕ إنشاء مهمة", callback_data="create_task")]]
        else:
            text = "📋 **مهامك:**\n\n"
            keyboard = []
            
            for task in tasks:
                status = "🟢 نشطة" if task['is_active'] else "🔴 متوقفة"
                task_type = "📤 توجيه" if task['task_type'] == 'forward' else "📋 نسخ"
                
                text += f"**{task['task_name']}** {status}\n"
                text += f"{task_type} | من: `{task['source_chat_id']}` إلى: `{task['target_chat_id']}`\n\n"
                
                keyboard.append([
                    InlineKeyboardButton(
                        f"⚙️ {task['task_name']}", 
                        callback_data=f"task_settings_{task['id']}"
                    )
                ])
            
            keyboard.append([InlineKeyboardButton("➕ إنشاء مهمة جديدة", callback_data="create_task")])
        
        keyboard.append([InlineKeyboardButton("🔙 العودة", callback_data="tasks_menu")])
        
        await update.callback_query.edit_message_text(
            text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown'
        )
    
    @staticmethod
    async def task_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show task settings"""
        task_id = int(update.callback_query.data.split('_')[-1])
        task = await TaskManager.get_task(task_id)
        
        if not task:
            await update.callback_query.answer("❌ المهمة غير موجودة")
            return
        
        # Check if user owns this task
        if task['user_id'] != update.effective_user.id:
            await update.callback_query.answer("❌ غير مصرح لك بالوصول لهذه المهمة")
            return
        
        status = "🟢 نشطة" if task['is_active'] else "🔴 متوقفة"
        task_type = "📤 توجيه" if task['task_type'] == 'forward' else "📋 نسخ"
        
        text = f"""
⚙️ **إعدادات المهمة**

📝 **الاسم:** {task['task_name']}
📊 **الحالة:** {status}
🔄 **النوع:** {task_type}
📥 **المصدر:** `{task['source_chat_id']}`
📤 **الهدف:** `{task['target_chat_id']}`

اختر الإعداد الذي تريد تعديله:
        """
        
        keyboard = KeyboardBuilder.task_settings_menu(task_id)
        
        await update.callback_query.edit_message_text(
            text, reply_markup=keyboard, parse_mode='Markdown'
        )
    
    @staticmethod
    async def toggle_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Toggle task active status"""
        task_id = int(update.callback_query.data.split('_')[-1])
        
        success = await TaskManager.toggle_task(task_id)
        
        if success:
            await update.callback_query.answer("✅ تم تغيير حالة المهمة")
            # Refresh task settings
            await TaskHandlers.task_settings(update, context)
        else:
            await update.callback_query.answer("❌ حدث خطأ أثناء تغيير حالة المهمة")
    
    @staticmethod
    async def delete_task_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Confirm task deletion"""
        task_id = int(update.callback_query.data.split('_')[-1])
        
        keyboard = KeyboardBuilder.confirmation_keyboard("delete_task", task_id)
        
        text = "⚠️ **تأكيد الحذف**\n\nهل أنت متأكد من حذف هذه المهمة؟\nلا يمكن التراجع عن هذا الإجراء."
        
        await update.callback_query.edit_message_text(
            text, reply_markup=keyboard, parse_mode='Markdown'
        )
    
    @staticmethod
    async def delete_task_confirmed(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Delete task after confirmation"""
        task_id = int(update.callback_query.data.split('_')[-1])
        
        success = await TaskManager.delete_task(task_id)
        
        if success:
            await update.callback_query.answer("✅ تم حذف المهمة")
            await TaskHandlers.view_tasks(update, context)
        else:
            await update.callback_query.answer("❌ حدث خطأ أثناء حذف المهمة")

    @staticmethod
    async def active_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """عرض المهام النشطة فقط"""
        user_id = update.effective_user.id
        tasks = await TaskManager.get_user_tasks(user_id)
        active_tasks = [task for task in tasks if task['is_active']]
        
        if not active_tasks:
            text = "📭 لا توجد مهام نشطة"
            keyboard = [
                [InlineKeyboardButton("➕ إنشاء مهمة جديدة", callback_data="create_task")],
                [InlineKeyboardButton("🔙 العودة", callback_data="tasks_menu")]
            ]
        else:
            text = f"⚡ **المهام النشطة ({len(active_tasks)}):**\n\n"
            keyboard = []
            
            for task in active_tasks:
                task_type = "📤 توجيه" if task['task_type'] == 'forward' else "📋 نسخ"
                text += f"🟢 **{task['task_name']}**\n"
                text += f"{task_type} | من: `{task['source_chat_id']}` إلى: `{task['target_chat_id']}`\n\n"
                
                keyboard.append([
                    InlineKeyboardButton(
                        f"⚙️ {task['task_name']}", 
                        callback_data=f"task_settings_{task['id']}"
                    ),
                    InlineKeyboardButton(
                        "⏸️ إيقاف", 
                        callback_data=f"toggle_task_{task['id']}"
                    )
                ])
        
        keyboard.append([InlineKeyboardButton("🔙 العودة", callback_data="tasks_menu")])
        
        await update.callback_query.edit_message_text(
            text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown'
        )

    @staticmethod
    async def inactive_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """عرض المهام المتوقفة فقط"""
        user_id = update.effective_user.id
        tasks = await TaskManager.get_user_tasks(user_id)
        inactive_tasks = [task for task in tasks if not task['is_active']]
        
        if not inactive_tasks:
            text = "📭 لا توجد مهام متوقفة"
            keyboard = [
                [InlineKeyboardButton("➕ إنشاء مهمة جديدة", callback_data="create_task")],
                [InlineKeyboardButton("🔙 العودة", callback_data="tasks_menu")]
            ]
        else:
            text = f"⏸️ **المهام المتوقفة ({len(inactive_tasks)}):**\n\n"
            keyboard = []
            
            for task in inactive_tasks:
                task_type = "📤 توجيه" if task['task_type'] == 'forward' else "📋 نسخ"
                text += f"🔴 **{task['task_name']}**\n"
                text += f"{task_type} | من: `{task['source_chat_id']}` إلى: `{task['target_chat_id']}`\n\n"
                
                keyboard.append([
                    InlineKeyboardButton(
                        f"⚙️ {task['task_name']}", 
                        callback_data=f"task_settings_{task['id']}"
                    ),
                    InlineKeyboardButton(
                        "▶️ تشغيل", 
                        callback_data=f"toggle_task_{task['id']}"
                    )
                ])
        
        keyboard.append([InlineKeyboardButton("🔙 العودة", callback_data="tasks_menu")])
        
        await update.callback_query.edit_message_text(
            text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown'
        )

    @staticmethod
    async def edit_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تعديل إعدادات المهمة الأساسية"""
        task_id = int(update.callback_query.data.split('_')[-1])
        task = await TaskManager.get_task(task_id)
        
        if not task:
            await update.callback_query.answer("❌ المهمة غير موجودة")
            return
        
        # التحقق من ملكية المهمة
        if task['user_id'] != update.effective_user.id:
            await update.callback_query.answer("❌ غير مصرح لك بتعديل هذه المهمة")
            return
        
        text = f"""
📝 **تعديل المهمة: {task['task_name']}**

اختر الإعداد الذي تريد تعديله:
        """
        
        keyboard = [
            [
                InlineKeyboardButton("📝 تغيير الاسم", callback_data=f"edit_name_{task_id}"),
                InlineKeyboardButton("📥 تغيير المصدر", callback_data=f"edit_source_{task_id}")
            ],
            [
                InlineKeyboardButton("📤 تغيير الهدف", callback_data=f"edit_target_{task_id}"),
                InlineKeyboardButton("🔄 تغيير النوع", callback_data=f"edit_type_{task_id}")
            ],
            [
                InlineKeyboardButton("📊 أولوية المهمة", callback_data=f"edit_priority_{task_id}"),
                InlineKeyboardButton("📝 وصف المهمة", callback_data=f"edit_description_{task_id}")
            ],
            [InlineKeyboardButton("🔙 العودة", callback_data=f"task_settings_{task_id}")]
        ]
        
        await update.callback_query.edit_message_text(
            text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown'
        )

    @staticmethod
    async def task_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """إحصائيات مهمة محددة"""
        task_id = int(update.callback_query.data.split('_')[-1])
        task = await TaskManager.get_task(task_id)
        
        if not task:
            await update.callback_query.answer("❌ المهمة غير موجودة")
            return
        
        # الحصول على الإحصائيات
        stats_7_days = await StatisticsManager.get_task_stats(task_id, days=7)
        stats_30_days = await StatisticsManager.get_task_stats(task_id, days=30)
        
        total_forwarded_7 = sum(s['messages_forwarded'] for s in stats_7_days)
        total_filtered_7 = sum(s['messages_filtered'] for s in stats_7_days)
        total_forwarded_30 = sum(s['messages_forwarded'] for s in stats_30_days)
        total_filtered_30 = sum(s['messages_filtered'] for s in stats_30_days)
        
        # حساب المعدلات
        success_rate_7 = 0
        success_rate_30 = 0
        
        if total_forwarded_7 + total_filtered_7 > 0:
            success_rate_7 = (total_forwarded_7 / (total_forwarded_7 + total_filtered_7)) * 100
        
        if total_forwarded_30 + total_filtered_30 > 0:
            success_rate_30 = (total_forwarded_30 / (total_forwarded_30 + total_filtered_30)) * 100
        
        status = "🟢 نشطة" if task['is_active'] else "🔴 متوقفة"
        task_type = "📤 توجيه" if task['task_type'] == 'forward' else "📋 نسخ"
        
        text = f"""
📊 **إحصائيات المهمة**

📝 **الاسم:** {task['task_name']}
📊 **الحالة:** {status}
🔄 **النوع:** {task_type}

📈 **آخر 7 أيام:**
• الرسائل المُوجهة: {total_forwarded_7:,}
• الرسائل المُرشحة: {total_filtered_7:,}
• معدل النجاح: {success_rate_7:.1f}%

📈 **آخر 30 يوم:**
• الرسائل المُوجهة: {total_forwarded_30:,}
• الرسائل المُرشحة: {total_filtered_30:,}
• معدل النجاح: {success_rate_30:.1f}%
        """
        
        keyboard = [
            [
                InlineKeyboardButton("📊 رسم بياني", callback_data=f"task_chart_{task_id}"),
                InlineKeyboardButton("📋 تقرير مفصل", callback_data=f"detailed_report_{task_id}")
            ],
            [
                InlineKeyboardButton("📤 تصدير البيانات", callback_data=f"export_task_data_{task_id}"),
                InlineKeyboardButton("🔄 تحديث", callback_data=f"task_stats_{task_id}")
            ],
            [InlineKeyboardButton("🔙 العودة", callback_data=f"task_settings_{task_id}")]
        ]
        
        await update.callback_query.edit_message_text(
            text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown'
        )
