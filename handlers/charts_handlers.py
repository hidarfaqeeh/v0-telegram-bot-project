from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database.statistics_manager import StatisticsManager
from database.task_manager import TaskManager
from database.user_manager import UserManager
from utils.error_handler import ErrorHandler
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import io
import base64

class ChartsHandlers:
    @staticmethod
    async def charts_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """قائمة الرسوم البيانية"""
        user_id = update.effective_user.id
        
        text = """
📈 **الرسوم البيانية**

اختر نوع الرسم البياني الذي تريد عرضه:
        """
        
        keyboard = [
            [
                InlineKeyboardButton("📊 رسم بياني للمهام", callback_data="tasks_chart"),
                InlineKeyboardButton("📈 رسم بياني للرسائل", callback_data="messages_chart")
            ],
            [
                InlineKeyboardButton("⏰ رسم بياني زمني", callback_data="timeline_chart"),
                InlineKeyboardButton("🎯 رسم بياني للفلاتر", callback_data="filters_chart")
            ],
            [
                InlineKeyboardButton("👥 رسم بياني للمستخدمين", callback_data="users_chart"),
                InlineKeyboardButton("📊 رسم بياني شامل", callback_data="comprehensive_chart")
            ],
            [InlineKeyboardButton("🔙 العودة", callback_data="statistics")]
        ]
        
        await update.callback_query.edit_message_text(
            text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown'
        )

    @staticmethod
    async def tasks_chart(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """رسم بياني للمهام"""
        user_id = update.effective_user.id
        
        try:
            # الحصول على بيانات المهام
            tasks = await TaskManager.get_user_tasks(user_id)
            active_tasks = len([t for t in tasks if t['is_active']])
            inactive_tasks = len([t for t in tasks if not t['is_active']])
            
            if not tasks:
                await update.callback_query.answer("❌ لا توجد مهام لإنشاء رسم بياني")
                return
            
            # إنشاء الرسم البياني
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))
            
            # رسم دائري لحالة المهام
            labels = ['نشطة', 'متوقفة']
            sizes = [active_tasks, inactive_tasks]
            colors = ['#4CAF50', '#F44336']
            
            ax1.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
            ax1.set_title('حالة المهام')
            
            # رسم بياني لأنواع المهام
            forward_tasks = len([t for t in tasks if t['task_type'] == 'forward'])
            copy_tasks = len([t for t in tasks if t['task_type'] == 'copy'])
            
            task_types = ['توجيه', 'نسخ']
            task_counts = [forward_tasks, copy_tasks]
            
            ax2.bar(task_types, task_counts, color=['#2196F3', '#FF9800'])
            ax2.set_title('أنواع المهام')
            ax2.set_ylabel('عدد المهام')
            
            plt.tight_layout()
            
            # حفظ الرسم كصورة
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
            img_buffer.seek(0)
            plt.close()
            
            # إرسال الصورة
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=img_buffer,
                caption="📊 **رسم بياني للمهام**",
                parse_mode='Markdown'
            )
            
            await update.callback_query.answer("✅ تم إنشاء الرسم البياني")
            
        except Exception as e:
            await ErrorHandler.log_error(update, context, e, "tasks_chart")
            await update.callback_query.answer("❌ فشل في إنشاء الرسم البياني")
    
    @staticmethod
    async def messages_chart(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """رسم بياني للرسائل"""
        user_id = update.effective_user.id
        
        try:
            # الحصول على بيانات الرسائل لآخر 30 يوم
            tasks = await TaskManager.get_user_tasks(user_id)
            
            if not tasks:
                await update.callback_query.answer("❌ لا توجد مهام لإنشاء رسم بياني")
                return
            
            # جمع البيانات لكل مهمة
            dates = []
            forwarded_counts = []
            filtered_counts = []
            
            for i in range(30):
                date = datetime.now().date() - timedelta(days=i)
                dates.append(date)
                
                daily_forwarded = 0
                daily_filtered = 0
                
                for task in tasks:
                    stats = await StatisticsManager.get_task_stats(task['id'], days=1)
                    for stat in stats:
                        if stat['date'] == date:
                            daily_forwarded += stat['messages_forwarded']
                            daily_filtered += stat['messages_filtered']
                
                forwarded_counts.append(daily_forwarded)
                filtered_counts.append(daily_filtered)
            
            # عكس القوائم لعرض التواريخ من الأقدم للأحدث
            dates.reverse()
            forwarded_counts.reverse()
            filtered_counts.reverse()
            
            # إنشاء الرسم البياني
            fig, ax = plt.subplots(figsize=(12, 6))
            
            ax.plot(dates, forwarded_counts, label='رسائل موجهة', color='#4CAF50', linewidth=2)
            ax.plot(dates, filtered_counts, label='رسائل مرشحة', color='#F44336', linewidth=2)
            
            ax.set_title('إحصائيات الرسائل - آخر 30 يوم')
            ax.set_xlabel('التاريخ')
            ax.set_ylabel('عدد الرسائل')
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            # تنسيق التواريخ
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
            ax.xaxis.set_major_locator(mdates.DayLocator(interval=5))
            plt.xticks(rotation=45)
            
            plt.tight_layout()
            
            # حفظ الرسم كصورة
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
            img_buffer.seek(0)
            plt.close()
            
            # إرسال الصورة
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=img_buffer,
                caption="📈 **رسم بياني للرسائل - آخر 30 يوم**",
                parse_mode='Markdown'
            )
            
            await update.callback_query.answer("✅ تم إنشاء الرسم البياني")
            
        except Exception as e:
            await ErrorHandler.log_error(update, context, e, "messages_chart")
            await update.callback_query.answer("❌ فشل في إنشاء الرسم البياني")
    
    @staticmethod
    async def timeline_chart(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """رسم بياني زمني للنشاط"""
        user_id = update.effective_user.id
        
        try:
            # الحصول على بيانات النشاط لآخر 7 أيام بالساعات
            tasks = await TaskManager.get_user_tasks(user_id)
            
            if not tasks:
                await update.callback_query.answer("❌ لا توجد مهام لإنشاء رسم بياني")
                return
            
            # إنشاء قائمة الساعات لآخر 7 أيام
            hours = []
            activity_counts = []
            
            for day in range(7):
                for hour in range(24):
                    dt = datetime.now() - timedelta(days=day, hours=23-hour)
                    hours.append(dt)
                    
                    # حساب النشاط في هذه الساعة (مبسط)
                    hour_activity = 0
                    for task in tasks:
                        if task['is_active']:
                            # محاكاة بيانات النشاط
                            hour_activity += max(0, 10 - abs(12 - hour))  # ذروة النشاط في منتصف النهار
                    
                    activity_counts.append(hour_activity)
            
            # عكس القوائم
            hours.reverse()
            activity_counts.reverse()
            
            # إنشاء الرسم البياني
            fig, ax = plt.subplots(figsize=(14, 6))
            
            ax.plot(hours, activity_counts, color='#2196F3', linewidth=1.5, alpha=0.8)
            ax.fill_between(hours, activity_counts, alpha=0.3, color='#2196F3')
            
            ax.set_title('النشاط الزمني - آخر 7 أيام')
            ax.set_xlabel('الوقت')
            ax.set_ylabel('مستوى النشاط')
            ax.grid(True, alpha=0.3)
            
            # تنسيق التواريخ
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:%M'))
            ax.xaxis.set_major_locator(mdates.HourLocator(interval=12))
            plt.xticks(rotation=45)
            
            plt.tight_layout()
            
            # حفظ الرسم كصورة
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
            img_buffer.seek(0)
            plt.close()
            
            # إرسال الصورة
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=img_buffer,
                caption="⏰ **الرسم البياني الزمني للنشاط**",
                parse_mode='Markdown'
            )
            
            await update.callback_query.answer("✅ تم إنشاء الرسم البياني")
            
        except Exception as e:
            await ErrorHandler.log_error(update, context, e, "timeline_chart")
            await update.callback_query.answer("❌ فشل في إنشاء الرسم البياني")
    
    @staticmethod
    async def filters_chart(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """رسم بياني للفلاتر"""
        user_id = update.effective_user.id
        
        try:
            tasks = await TaskManager.get_user_tasks(user_id)
            
            if not tasks:
                await update.callback_query.answer("❌ لا توجد مهام لإنشاء رسم بياني")
                return
            
            # تحليل الفلاتر المستخدمة
            media_filters_count = 0
            text_filters_count = 0
            advanced_filters_count = 0
            user_lists_count = 0
            
            for task in tasks:
                settings = task.get('settings', {})
                
                if settings.get('media_filters', {}).get('enabled'):
                    media_filters_count += 1
                
                if settings.get('blocked_words') or settings.get('required_words'):
                    text_filters_count += 1
                
                if settings.get('advanced_filters'):
                    advanced_filters_count += 1
                
                if settings.get('whitelist') or settings.get('blacklist'):
                    user_lists_count += 1
            
            # إنشاء الرسم البياني
            fig, ax = plt.subplots(figsize=(10, 6))
            
            filter_types = ['فلاتر الوسائط', 'فلاتر النص', 'فلاتر متقدمة', 'قوائم المستخدمين']
            filter_counts = [media_filters_count, text_filters_count, advanced_filters_count, user_lists_count]
            colors = ['#4CAF50', '#2196F3', '#FF9800', '#9C27B0']
            
            bars = ax.bar(filter_types, filter_counts, color=colors)
            ax.set_title('استخدام الفلاتر في المهام')
            ax.set_ylabel('عدد المهام')
            
            # إضافة قيم على الأعمدة
            for bar, count in zip(bars, filter_counts):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                       f'{count}', ha='center', va='bottom')
            
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            # حفظ الرسم كصورة
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
            img_buffer.seek(0)
            plt.close()
            
            # إرسال الصورة
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=img_buffer,
                caption="🎯 **رسم بياني لاستخدام الفلاتر**",
                parse_mode='Markdown'
            )
            
            await update.callback_query.answer("✅ تم إنشاء الرسم البياني")
            
        except Exception as e:
            await ErrorHandler.log_error(update, context, e, "filters_chart")
            await update.callback_query.answer("❌ فشل في إنشاء الرسم البياني")
    
    @staticmethod
    async def users_chart(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """رسم بياني للمستخدمين"""
        user_id = update.effective_user.id
        
        # التحقق من صلاحيات المدير
        if not await UserManager.is_admin(user_id):
            await update.callback_query.answer("❌ هذه الميزة متاحة للمديرين فقط")
            return
        
        try:
            users = await UserManager.get_all_users()
            
            if not users:
                await update.callback_query.answer("❌ لا توجد بيانات مستخدمين")
                return
            
            # تحليل بيانات المستخدمين
            total_users = len(users)
            active_users = len([u for u in users if u['is_active']])
            admin_users = len([u for u in users if u['is_admin']])
            banned_users = total_users - active_users
            
            # إنشاء الرسم البياني
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))
            
            # رسم دائري لحالة المستخدمين
            labels1 = ['نشطين', 'محظورين']
            sizes1 = [active_users, banned_users]
            colors1 = ['#4CAF50', '#F44336']
            
            ax1.pie(sizes1, labels=labels1, colors=colors1, autopct='%1.1f%%', startangle=90)
            ax1.set_title('حالة المستخدمين')
            
            # رسم بياني لأنواع المستخدمين
            user_types = ['مستخدمين عاديين', 'مديرين']
            user_counts = [total_users - admin_users, admin_users]
            
            ax2.bar(user_types, user_counts, color=['#2196F3', '#FF9800'])
            ax2.set_title('أنواع المستخدمين')
            ax2.set_ylabel('العدد')
            
            plt.tight_layout()
            
            # حفظ الرسم كصورة
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
            img_buffer.seek(0)
            plt.close()
            
            # إرسال الصورة
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=img_buffer,
                caption="👥 **رسم بياني للمستخدمين**",
                parse_mode='Markdown'
            )
            
            await update.callback_query.answer("✅ تم إنشاء الرسم البياني")
            
        except Exception as e:
            await ErrorHandler.log_error(update, context, e, "users_chart")
            await update.callback_query.answer("❌ فشل في إنشاء الرسم البياني")
    
    @staticmethod
    async def comprehensive_chart(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """رسم بياني شامل"""
        user_id = update.effective_user.id
        
        try:
            # الحصول على جميع البيانات
            tasks = await TaskManager.get_user_tasks(user_id)
            user_stats = await StatisticsManager.get_user_stats(user_id)
            
            if not tasks:
                await update.callback_query.answer("❌ لا توجد مهام لإنشاء رسم بياني")
                return
            
            # إنشاء رسم بياني متعدد الأجزاء
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
            
            # الرسم الأول: حالة المهام
            active_tasks = len([t for t in tasks if t['is_active']])
            inactive_tasks = len([t for t in tasks if not t['is_active']])
            
            ax1.pie([active_tasks, inactive_tasks], labels=['نشطة', 'متوقفة'], 
                   colors=['#4CAF50', '#F44336'], autopct='%1.1f%%')
            ax1.set_title('حالة المهام')
            
            # الرسم الثاني: أنواع المهام
            forward_tasks = len([t for t in tasks if t['task_type'] == 'forward'])
            copy_tasks = len([t for t in tasks if t['task_type'] == 'copy'])
            
            ax2.bar(['توجيه', 'نسخ'], [forward_tasks, copy_tasks], 
                   color=['#2196F3', '#FF9800'])
            ax2.set_title('أنواع المهام')
            ax2.set_ylabel('العدد')
            
            # الرسم الثالث: إحصائيات الرسائل
            forwarded = user_stats.get('total_forwarded', 0)
            filtered = user_stats.get('total_filtered', 0)
            
            ax3.bar(['موجهة', 'مرشحة'], [forwarded, filtered], 
                   color=['#4CAF50', '#F44336'])
            ax3.set_title('إحصائيات الرسائل')
            ax3.set_ylabel('العدد')
            
            # الرسم الرابع: معدل النجاح
            if forwarded + filtered > 0:
                success_rate = (forwarded / (forwarded + filtered)) * 100
                ax4.pie([success_rate, 100-success_rate], 
                       labels=[f'نجح {success_rate:.1f}%', f'فشل {100-success_rate:.1f}%'],
                       colors=['#4CAF50', '#F44336'], autopct='%1.1f%%')
            else:
                ax4.text(0.5, 0.5, 'لا توجد بيانات', ha='center', va='center')
            ax4.set_title('معدل النجاح')
            
            plt.tight_layout()
            
            # حفظ الرسم كصورة
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
            img_buffer.seek(0)
            plt.close()
            
            # إرسال الصورة
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=img_buffer,
                caption="📊 **الرسم البياني الشامل**",
                parse_mode='Markdown'
            )
            
            await update.callback_query.answer("✅ تم إنشاء الرسم البياني الشامل")
            
        except Exception as e:
            await ErrorHandler.log_error(update, context, e, "comprehensive_chart")
            await update.callback_query.answer("❌ فشل في إنشاء الرسم البياني")
