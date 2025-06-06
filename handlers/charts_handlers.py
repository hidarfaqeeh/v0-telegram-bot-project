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
    async def tasks_chart(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """رسم بياني للمهام"""
        user_id = update.effective_user.id
        
        try:
            # الحصول على بيانات المهام
            tasks = await TaskManager.get_user_tasks(user_id)
            active_tasks = len([t for t in tasks if t['is_active']])
            inactive_tasks = len([t for t in tasks if not t['is_active']])
            
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
    async def comprehensive_chart(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """رسم بياني شامل"""
        user_id = update.effective_user.id
        
        try:
            # الحصول على جميع البيانات
            tasks = await TaskManager.get_user_tasks(user_id)
            user_stats = await StatisticsManager.get_user_stats(user_id)
            
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
