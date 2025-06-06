from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from database.task_manager import TaskManager
from database.statistics_manager import StatisticsManager
from utils.keyboard_builder import KeyboardBuilder
from utils.message_processor import MessageProcessor
import json

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
    async def task_name_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Receive task name"""
        task_name = update.message.text
        context.user_data['task_name'] = task_name
        
        text = f"""
📝 **اسم المهمة:** {task_name}

الآن أرسل ID محادثة المصدر:
(يمكنك الحصول على ID المحادثة باستخدام @userinfobot)
        """
        
        await update.message.reply_text(text, parse_mode='Markdown')
        return SOURCE_CHAT
    
    @staticmethod
    async def source_chat_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Receive source chat ID"""
        try:
            source_chat_id = int(update.message.text)
            context.user_data['source_chat_id'] = source_chat_id
            
            text = f"""
📝 **اسم المهمة:** {context.user_data['task_name']}
📥 **محادثة المصدر:** {source_chat_id}

الآن أرسل ID محادثة الهدف:
            """
            
            await update.message.reply_text(text, parse_mode='Markdown')
            return TARGET_CHAT
        except ValueError:
            await update.message.reply_text("❌ يرجى إرسال رقم صحيح لـ ID المحادثة")
            return SOURCE_CHAT
    
    @staticmethod
    async def target_chat_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Receive target chat ID"""
        try:
            target_chat_id = int(update.message.text)
            context.user_data['target_chat_id'] = target_chat_id
            
            keyboard = [
                [
                    InlineKeyboardButton("📤 توجيه", callback_data="task_type_forward"),
                    InlineKeyboardButton("📋 نسخ", callback_data="task_type_copy")
                ]
            ]
            
            text = f"""
📝 **اسم المهمة:** {context.user_data['task_name']}
📥 **محادثة المصدر:** {context.user_data['source_chat_id']}
📤 **محادثة الهدف:** {target_chat_id}

اختر نوع التوجيه:
            """
            
            await update.message.reply_text(
                text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown'
            )
            return TASK_TYPE
        except ValueError:
            await update.message.reply_text("❌ يرجى إرسال رقم صحيح لـ ID المحادثة")
            return TARGET_CHAT
    
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
