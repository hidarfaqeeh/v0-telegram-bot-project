from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database.user_manager import UserManager
from database.statistics_manager import StatisticsManager
from utils.keyboard_builder import KeyboardBuilder
from config import Config
from database.task_manager import TaskManager

class MainHandlers:
    @staticmethod
    async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        
        # Create or update user in database
        await UserManager.create_or_update_user(
            user_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )
        
        # Set admin if this is the first user or configured admin
        if user.id == Config.ADMIN_USER_ID:
            await UserManager.set_admin(user.id, True)
        
        welcome_text = f"""
🎉 **مرحباً {user.first_name}!**

أهلاً بك في **بوت توجيه الرسائل المتقدم**

🚀 **المميزات:**
• توجيه ونسخ الرسائل تلقائياً
• فلاتر متقدمة للرسائل والوسائط
• دعم Userbot للمحادثات الخاصة
• إحصائيات مفصلة
• واجهة تحكم سهلة الاستخدام

📋 **ابدأ الآن:**
اضغط على "إدارة المهام" لإنشاء مهمة توجيه جديدة
        """
        
        keyboard = KeyboardBuilder.main_menu()
        
        await update.message.reply_text(
            welcome_text, reply_markup=keyboard, parse_mode='Markdown'
        )
    
    @staticmethod
    async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show main menu"""
        user = update.effective_user
        
        # Update user activity
        await UserManager.create_or_update_user(
            user_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )
        
        # Get user statistics
        stats = await StatisticsManager.get_user_stats(user.id)
        
        text = f"""
🏠 **القائمة الرئيسية**

👋 مرحباً **{user.first_name}**

📊 **إحصائياتك:**
• المهام الإجمالية: {stats.get('total_tasks', 0)}
• المهام النشطة: {stats.get('active_tasks', 0)}
• الرسائل المُوجهة: {stats.get('total_forwarded', 0)}
• الرسائل المُرشحة: {stats.get('total_filtered', 0)}

اختر العملية التي تريد تنفيذها:
        """
        
        keyboard = KeyboardBuilder.main_menu()
        
        if update.callback_query:
            await update.callback_query.edit_message_text(
                text, reply_markup=keyboard, parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                text, reply_markup=keyboard, parse_mode='Markdown'
            )
    
    @staticmethod
    async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show help information"""
        help_text = """
📚 **دليل الاستخدام**

🔧 **الأوامر الأساسية:**
• `/start` - بدء البوت
• `/help` - عرض المساعدة
• `/menu` - القائمة الرئيسية
• `/stats` - الإحصائيات

📋 **إدارة المهام:**
1️⃣ اذهب إلى "إدارة المهام"
2️⃣ اضغط "إنشاء مهمة جديدة"
3️⃣ أدخل اسم المهمة
4️⃣ أدخل ID محادثة المصدر
5️⃣ أدخل ID محادثة الهدف
6️⃣ اختر نوع التوجيه (توجيه/نسخ)

⚙️ **الإعدادات المتقدمة:**
• **فلاتر الوسائط:** تحديد أنواع الملفات
• **فلاتر النص:** كلمات مطلوبة/محظورة
• **الاستبدال:** تغيير النصوص
• **التأخير:** تأخير إرسال الرسائل
• **القوائم:** قائمة بيضاء/سوداء للمستخدمين

🤖 **Userbot:**
يسمح بمراقبة المحادثات الخاصة والمجموعات المقيدة

❓ **الحصول على ID المحادثة:**
استخدم @userinfobot أو @getidsbot

⚠️ **ملاحظات مهمة:**
• تأكد من إضافة البوت للمجموعات المطلوبة
• امنح البوت صلاحيات الإدارة إذا لزم الأمر
• استخدم حساب منفصل للـ Userbot
        """
        
        keyboard = [[InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main_menu")]]
        
        if update.callback_query:
            await update.callback_query.edit_message_text(
                help_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                help_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown'
            )
    
    @staticmethod
    async def statistics_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show statistics menu"""
        user_id = update.effective_user.id
        stats = await StatisticsManager.get_user_stats(user_id)
        
        text = f"""
📊 **الإحصائيات التفصيلية**

📋 **المهام:**
• إجمالي المهام: {stats.get('total_tasks', 0)}
• المهام النشطة: {stats.get('active_tasks', 0)}
• المهام المتوقفة: {stats.get('total_tasks', 0) - stats.get('active_tasks', 0)}

📤 **الرسائل:**
• الرسائل المُوجهة: {stats.get('total_forwarded', 0):,}
• الرسائل المُرشحة: {stats.get('total_filtered', 0):,}
• إجمالي الرسائل المُعالجة: {stats.get('total_forwarded', 0) + stats.get('total_filtered', 0):,}

📈 **معدل النجاح:**
        """
        
        total_processed = stats.get('total_forwarded', 0) + stats.get('total_filtered', 0)
        if total_processed > 0:
            success_rate = (stats.get('total_forwarded', 0) / total_processed) * 100
            text += f"• معدل التوجيه: {success_rate:.1f}%"
        else:
            text += "• لا توجد بيانات كافية"
        
        keyboard = [
            [
                InlineKeyboardButton("📊 إحصائيات المهام", callback_data="task_statistics"),
                InlineKeyboardButton("📈 الرسوم البيانية", callback_data="charts")
            ],
            [
                InlineKeyboardButton("🔄 تحديث", callback_data="statistics"),
                InlineKeyboardButton("🔙 العودة", callback_data="main_menu")
            ]
        ]
        
        await update.callback_query.edit_message_text(
            text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown'
        )
    
    @staticmethod
    async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming messages for forwarding"""
        # This will be handled by the MessageForwarder
        message = update.message
        
        # Import here to avoid circular imports
        from handlers.message_forwarder import MessageForwarder
        
        # Get the forwarder instance from context
        forwarder = context.bot_data.get('message_forwarder')
        if forwarder:
            await forwarder.process_message(message)

    @staticmethod
    async def task_statistics(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """عرض إحصائيات المهام التفصيلية"""
        user_id = update.effective_user.id
        tasks = await TaskManager.get_user_tasks(user_id)
        
        if not tasks:
            text = "📭 لا توجد مهام لعرض إحصائياتها"
            keyboard = [[InlineKeyboardButton("🔙 العودة", callback_data="statistics")]]
        else:
            text = "📊 **إحصائيات المهام:**\n\n"
            keyboard = []
            
            for task in tasks:
                stats = await StatisticsManager.get_task_stats(task['id'], days=7)
                total_forwarded = sum(s['messages_forwarded'] for s in stats)
                total_filtered = sum(s['messages_filtered'] for s in stats)
                
                status = "🟢" if task['is_active'] else "🔴"
                text += f"{status} **{task['task_name']}**\n"
                text += f"   📤 مُوجه: {total_forwarded}\n"
                text += f"   🚫 مُرشح: {total_filtered}\n\n"
                
                keyboard.append([
                    InlineKeyboardButton(
                        f"📊 {task['task_name']}", 
                        callback_data=f"detailed_stats_{task['id']}"
                    )
                ])
            
            keyboard.append([InlineKeyboardButton("🔙 العودة", callback_data="statistics")])
        
        await update.callback_query.edit_message_text(
            text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown'
        )

    @staticmethod
    async def detailed_task_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """عرض إحصائيات مفصلة لمهمة محددة"""
        task_id = int(update.callback_query.data.split('_')[-1])
        task = await TaskManager.get_task(task_id)
        
        if not task:
            await update.callback_query.answer("❌ المهمة غير موجودة")
            return
        
        # إحصائيات آخر 7 أيام
        stats = await StatisticsManager.get_task_stats(task_id, days=7)
        
        text = f"📊 **إحصائيات مفصلة: {task['task_name']}**\n\n"
        
        total_forwarded = sum(s['messages_forwarded'] for s in stats)
        total_filtered = sum(s['messages_filtered'] for s in stats)
        total_processed = total_forwarded + total_filtered
        
        text += f"📈 **الإجمالي (7 أيام):**\n"
        text += f"• الرسائل المُعالجة: {total_processed:,}\n"
        text += f"• الرسائل المُوجهة: {total_forwarded:,}\n"
        text += f"• الرسائل المُرشحة: {total_filtered:,}\n"
        
        if total_processed > 0:
            success_rate = (total_forwarded / total_processed) * 100
            text += f"• معدل النجاح: {success_rate:.1f}%\n\n"
        
        text += f"📅 **تفاصيل يومية:**\n"
        for stat in stats[-5:]:  # آخر 5 أيام
            text += f"• {stat['date']}: {stat['messages_forwarded']} مُوجه, {stat['messages_filtered']} مُرشح\n"
        
        keyboard = [
            [
                InlineKeyboardButton("📊 رسم بياني", callback_data=f"chart_{task_id}"),
                InlineKeyboardButton("📋 تقرير كامل", callback_data=f"full_report_{task_id}")
            ],
            [InlineKeyboardButton("🔙 العودة", callback_data="task_statistics")]
        ]
        
        await update.callback_query.edit_message_text(
            text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown'
        )
