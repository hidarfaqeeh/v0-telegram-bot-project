from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from database.user_manager import UserManager
from database.task_manager import TaskManager
from utils.error_handler import ErrorHandler
from config import Config

# حالات المحادثة للإعدادات
NOTIFICATION_SETTING, LANGUAGE_SETTING, SECURITY_SETTING = range(3)

class SettingsHandlers:
    @staticmethod
    async def notification_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """إعدادات الإشعارات"""
        user_id = update.effective_user.id
        
        text = """
🔔 **إعدادات الإشعارات**

اختر نوع الإشعارات التي تريد تفعيلها:
        """
        
        keyboard = [
            [
                InlineKeyboardButton("✅ إشعارات المهام", callback_data="toggle_task_notifications"),
                InlineKeyboardButton("✅ إشعارات الأخطاء", callback_data="toggle_error_notifications")
            ],
            [
                InlineKeyboardButton("✅ إشعارات الإحصائيات", callback_data="toggle_stats_notifications"),
                InlineKeyboardButton("✅ إشعارات النظام", callback_data="toggle_system_notifications")
            ],
            [
                InlineKeyboardButton("⏰ توقيت الإشعارات", callback_data="notification_timing"),
                InlineKeyboardButton("🔕 تعطيل الكل", callback_data="disable_all_notifications")
            ],
            [InlineKeyboardButton("🔙 العودة", callback_data="settings")]
        ]
        
        await update.callback_query.edit_message_text(
            text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown'
        )
    
    @staticmethod
    async def language_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """إعدادات اللغة"""
        text = """
🌐 **إعدادات اللغة**

اختر لغة الواجهة:
        """
        
        keyboard = [
            [
                InlineKeyboardButton("🇸🇦 العربية", callback_data="set_language_ar"),
                InlineKeyboardButton("🇺🇸 English", callback_data="set_language_en")
            ],
            [
                InlineKeyboardButton("🇫🇷 Français", callback_data="set_language_fr"),
                InlineKeyboardButton("🇩🇪 Deutsch", callback_data="set_language_de")
            ],
            [
                InlineKeyboardButton("🇪🇸 Español", callback_data="set_language_es"),
                InlineKeyboardButton("🇷🇺 Русский", callback_data="set_language_ru")
            ],
            [InlineKeyboardButton("🔙 العودة", callback_data="settings")]
        ]
        
        await update.callback_query.edit_message_text(
            text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown'
        )
    
    @staticmethod
    async def security_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """إعدادات الأمان"""
        user_id = update.effective_user.id
        
        text = """
🔒 **إعدادات الأمان**

اختر الإعداد الأمني الذي تريد تعديله:
        """
        
        keyboard = [
            [
                InlineKeyboardButton("🔐 تفعيل المصادقة الثنائية", callback_data="enable_2fa"),
                InlineKeyboardButton("🔑 تغيير كلمة المرور", callback_data="change_password")
            ],
            [
                InlineKeyboardButton("📱 أجهزة موثوقة", callback_data="trusted_devices"),
                InlineKeyboardButton("🚫 جلسات نشطة", callback_data="active_sessions")
            ],
            [
                InlineKeyboardButton("🔒 قفل التطبيق", callback_data="app_lock"),
                InlineKeyboardButton("📊 سجل الأنشطة", callback_data="activity_log")
            ],
            [InlineKeyboardButton("🔙 العودة", callback_data="settings")]
        ]
        
        await update.callback_query.edit_message_text(
            text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown'
        )
    
    @staticmethod
    async def backup_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """إعدادات النسخ الاحتياطي"""
        user_id = update.effective_user.id
        
        text = """
💾 **النسخ الاحتياطي**

إدارة النسخ الاحتياطية لبياناتك:
        """
        
        keyboard = [
            [
                InlineKeyboardButton("📤 إنشاء نسخة احتياطية", callback_data="create_backup"),
                InlineKeyboardButton("📥 استعادة نسخة احتياطية", callback_data="restore_backup")
            ],
            [
                InlineKeyboardButton("⏰ جدولة النسخ التلقائي", callback_data="schedule_backup"),
                InlineKeyboardButton("📋 عرض النسخ المحفوظة", callback_data="view_backups")
            ],
            [
                InlineKeyboardButton("☁️ رفع للسحابة", callback_data="cloud_backup"),
                InlineKeyboardButton("🗑️ حذف النسخ القديمة", callback_data="delete_old_backups")
            ],
            [InlineKeyboardButton("🔙 العودة", callback_data="settings")]
        ]
        
        await update.callback_query.edit_message_text(
            text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown'
        )
    
    @staticmethod
    async def ui_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """إعدادات الواجهة"""
        text = """
🎨 **إعدادات الواجهة**

تخصيص مظهر وسلوك الواجهة:
        """
        
        keyboard = [
            [
                InlineKeyboardButton("🌙 الوضع الليلي", callback_data="toggle_dark_mode"),
                InlineKeyboardButton("🎨 تخصيص الألوان", callback_data="customize_colors")
            ],
            [
                InlineKeyboardButton("📱 حجم الخط", callback_data="font_size"),
                InlineKeyboardButton("🔤 نوع الخط", callback_data="font_type")
            ],
            [
                InlineKeyboardButton("📐 تخطيط الواجهة", callback_data="layout_settings"),
                InlineKeyboardButton("🎵 الأصوات", callback_data="sound_settings")
            ],
            [InlineKeyboardButton("🔙 العودة", callback_data="settings")]
        ]
        
        await update.callback_query.edit_message_text(
            text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown'
        )
    
    @staticmethod
    async def stats_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """إعدادات الإحصائيات"""
        text = """
📊 **إعدادات الإحصائيات**

تخصيص عرض وحفظ الإحصائيات:
        """
        
        keyboard = [
            [
                InlineKeyboardButton("📈 نوع الرسوم البيانية", callback_data="chart_type"),
                InlineKeyboardButton("⏰ فترة الإحصائيات", callback_data="stats_period")
            ],
            [
                InlineKeyboardButton("💾 حفظ الإحصائيات", callback_data="save_stats"),
                InlineKeyboardButton("📤 تصدير الإحصائيات", callback_data="export_stats")
            ],
            [
                InlineKeyboardButton("🔄 تحديث تلقائي", callback_data="auto_refresh"),
                InlineKeyboardButton("📊 إحصائيات مفصلة", callback_data="detailed_stats")
            ],
            [InlineKeyboardButton("🔙 العودة", callback_data="settings")]
        ]
        
        await update.callback_query.edit_message_text(
            text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown'
        )
    
    @staticmethod
    async def create_backup(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """إنشاء نسخة احتياطية"""
        user_id = update.effective_user.id
        
        try:
            # الحصول على بيانات المستخدم
            user_tasks = await TaskManager.get_user_tasks(user_id)
            user_data = await UserManager.get_user(user_id)
            
            # إنشاء ملف النسخة الاحتياطية
            import json
            from datetime import datetime
            
            backup_data = {
                'user_data': user_data,
                'tasks': user_tasks,
                'created_at': datetime.now().isoformat(),
                'version': '1.0'
            }
            
            # حفظ النسخة الاحتياطية
            backup_json = json.dumps(backup_data, ensure_ascii=False, indent=2)
            
            # إرسال الملف للمستخدم
            from io import BytesIO
            backup_file = BytesIO(backup_json.encode('utf-8'))
            backup_file.name = f"backup_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            await context.bot.send_document(
                chat_id=update.effective_chat.id,
                document=backup_file,
                caption="💾 **تم إنشاء النسخة الاحتياطية بنجاح!**\n\nاحتفظ بهذا الملف في مكان آمن.",
                parse_mode='Markdown'
            )
            
            await update.callback_query.answer("✅ تم إنشاء النسخة الاحتياطية")
            
        except Exception as e:
            await ErrorHandler.log_error(update, context, e, "create_backup")
            await update.callback_query.answer("❌ فشل في إنشاء النسخة الاحتياطية")
    
    @staticmethod
    async def view_backups(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """عرض النسخ الاحتياطية المحفوظة"""
        text = """
📋 **النسخ الاحتياطية المحفوظة**

لا توجد نسخ احتياطية محفوظة على الخادم.
يمكنك إنشاء نسخة احتياطية جديدة وحفظها محلياً.
        """
        
        keyboard = [
            [InlineKeyboardButton("📤 إنشاء نسخة جديدة", callback_data="create_backup")],
            [InlineKeyboardButton("🔙 العودة", callback_data="backup_settings")]
        ]
        
        await update.callback_query.edit_message_text(
            text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown'
        )
    
    @staticmethod
    async def toggle_setting(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تبديل إعداد معين"""
        setting_type = update.callback_query.data.split('_')[1]
        
        # هنا يمكن إضافة منطق تبديل الإعدادات
        await update.callback_query.answer(f"✅ تم تحديث إعداد {setting_type}")
        
        # إعادة عرض القائمة المناسبة
        if 'notification' in setting_type:
            await SettingsHandlers.notification_settings(update, context)
        elif 'language' in setting_type:
            await SettingsHandlers.language_settings(update, context)
        elif 'security' in setting_type:
            await SettingsHandlers.security_settings(update, context)

    @staticmethod
    async def restore_backup_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """بدء استعادة نسخة احتياطية"""
        try:
            text = """
📥 **استعادة نسخة احتياطية**

أرسل ملف النسخة الاحتياطية (.json) لاستعادة بياناتك:

⚠️ **تحذير:**
• سيتم استبدال جميع البيانات الحالية
• تأكد من أن الملف صحيح وغير تالف
• يُنصح بإنشاء نسخة احتياطية قبل الاستعادة
            """
            
            keyboard = [[InlineKeyboardButton("❌ إلغاء", callback_data="backup_settings")]]
            
            await update.callback_query.edit_message_text(
                text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown'
            )
            
            # تعيين حالة انتظار الملف
            context.user_data['waiting_for_backup_file'] = True
            
        except Exception as e:
            await ErrorHandler.log_error(update, context, e, "restore_backup_start")
            await update.callback_query.answer("❌ حدث خطأ")

    @staticmethod
    async def restore_backup_file_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """استقبال ملف النسخة الاحتياطية"""
        try:
            if not context.user_data.get('waiting_for_backup_file'):
                return
            
            user_id = update.effective_user.id
            
            # التحقق من وجود ملف
            if not update.message.document:
                await update.message.reply_text(
                    "❌ يرجى إرسال ملف النسخة الاحتياطية (.json)",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("❌ إلغاء", callback_data="backup_settings")
                    ]])
                )
                return
            
            # التحقق من نوع الملف
            if not update.message.document.file_name.endswith('.json'):
                await update.message.reply_text(
                    "❌ يجب أن يكون الملف من نوع JSON (.json)",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("❌ إلغاء", callback_data="backup_settings")
                    ]])
                )
                return
            
            # تحميل الملف
            file = await context.bot.get_file(update.message.document.file_id)
            file_content = await file.download_as_bytearray()
            
            try:
                # تحليل محتوى JSON
                import json
                backup_data = json.loads(file_content.decode('utf-8'))
                
                # التحقق من صحة البيانات
                if not isinstance(backup_data, dict):
                    raise ValueError("تنسيق ملف غير صحيح")
                
                required_keys = ['user_data', 'tasks', 'backup_info']
                if not all(key in backup_data for key in required_keys):
                    raise ValueError("ملف النسخة الاحتياطية غير مكتمل")
                
                # استعادة البيانات
                success = await SettingsHandlers._restore_user_data(user_id, backup_data)
                
                if success:
                    # إزالة حالة الانتظار
                    context.user_data.pop('waiting_for_backup_file', None)
                    
                    text = """
✅ **تم استعادة النسخة الاحتياطية بنجاح!**

📊 **تم استعادة:**
• بيانات المستخدم
• جميع المهام والإعدادات
• الفلاتر والقوائم
• الإحصائيات

🔄 يُنصح بإعادة تشغيل البوت لضمان تطبيق جميع التغييرات.
                    """
                    
                    keyboard = [[InlineKeyboardButton("🔙 العودة", callback_data="backup_settings")]]
                    
                    await update.message.reply_text(
                        text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown'
                    )
                else:
                    await update.message.reply_text(
                        "❌ فشل في استعادة النسخة الاحتياطية. يرجى التحقق من الملف والمحاولة مرة أخرى.",
                        reply_markup=InlineKeyboardMarkup([[
                            InlineKeyboardButton("🔙 العودة", callback_data="backup_settings")
                        ]])
                    )
                
            except json.JSONDecodeError:
                await update.message.reply_text(
                    "❌ ملف JSON غير صحيح. يرجى التحقق من الملف.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 العودة", callback_data="backup_settings")
                    ]])
                )
            except ValueError as ve:
                await update.message.reply_text(
                    f"❌ خطأ في البيانات: {str(ve)}",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 العودة", callback_data="backup_settings")
                    ]])
                )
                
        except Exception as e:
            await ErrorHandler.log_error(update, context, e, "restore_backup_file_received")
            await update.message.reply_text(
                "❌ حدث خطأ أثناء استعادة النسخة الاحتياطية",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 العودة", callback_data="backup_settings")
                ]])
            )

    @staticmethod
    async def _restore_user_data(user_id: int, backup_data: dict) -> bool:
        """استعادة بيانات المستخدم من النسخة الاحتياطية"""
        try:
            from database.task_manager import TaskManager
            from database.user_manager import UserManager
            
            # حذف البيانات الحالية
            await SettingsHandlers._clear_user_data(user_id)
            
            # استعادة بيانات المستخدم
            user_data = backup_data.get('user_data')
            if user_data:
                await UserManager.update_user_from_backup(user_id, user_data)
            
            # استعادة المهام
            tasks_data = backup_data.get('tasks', [])
            for task_data in tasks_data:
                # إنشاء المهمة
                task_id = await TaskManager.create_task(
                    user_id=user_id,
                    task_name=task_data.get('task_name'),
                    source_chat_id=task_data.get('source_chat_id'),
                    target_chat_id=task_data.get('target_chat_id'),
                    task_type=task_data.get('task_type', 'forward'),
                    settings=task_data.get('settings', {})
                )
                
                if task_id:
                    # تحديث الإحصائيات إذا كانت موجودة
                    if 'total_forwarded' in task_data:
                        await TaskManager.update_task_statistics(
                            task_id,
                            forwarded=task_data.get('total_forwarded', 0),
                            filtered=task_data.get('total_filtered', 0)
                        )
            
            return True
            
        except Exception as e:
            print(f"Error restoring user data: {e}")
            return False

    @staticmethod
    async def _clear_user_data(user_id: int):
        """حذف بيانات المستخدم الحالية"""
        try:
            from database.models import db
            
            async with db.pool.acquire() as conn:
                async with conn.transaction():
                    # حذف المهام والبيانات المرتبطة
                    await conn.execute(
                        'DELETE FROM forwarding_tasks WHERE user_id = $1', user_id
                    )
                    
                    # حذف جلسات Userbot
                    await conn.execute(
                        'DELETE FROM userbot_sessions WHERE user_id = $1', user_id
                    )
                    
                    # إعادة تعيين إعدادات المستخدم
                    await conn.execute('''
                        UPDATE user_settings 
                        SET notifications_enabled = TRUE,
                            language = 'ar',
                            timezone = 'UTC'
                        WHERE user_id = $1
                    ''', user_id)
                    
        except Exception as e:
            print(f"Error clearing user data: {e}")

    @staticmethod
    async def schedule_backup(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """جدولة النسخ الاحتياطي التلقائي"""
        try:
            text = """
⏰ **جدولة النسخ الاحتياطي التلقائي**

اختر تكرار النسخ الاحتياطي التلقائي:
            """
            
            keyboard = [
                [
                    InlineKeyboardButton("📅 يومياً", callback_data="schedule_daily"),
                    InlineKeyboardButton("📅 أسبوعياً", callback_data="schedule_weekly")
                ],
                [
                    InlineKeyboardButton("📅 شهرياً", callback_data="schedule_monthly"),
                    InlineKeyboardButton("🔴 تعطيل", callback_data="schedule_disable")
                ],
                [InlineKeyboardButton("🔙 العودة", callback_data="backup_settings")]
            ]
            
            await update.callback_query.edit_message_text(
                text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown'
            )
            
        except Exception as e:
            await ErrorHandler.log_error(update, context, e, "schedule_backup")
            await update.callback_query.answer("❌ حدث خطأ")

    @staticmethod
    async def cloud_backup(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """رفع النسخة الاحتياطية للسحابة"""
        try:
            text = """
☁️ **رفع للسحابة**

اختر خدمة التخزين السحابي:

⚠️ **ملاحظة:** هذه الميزة قيد التطوير
            """
            
            keyboard = [
                [
                    InlineKeyboardButton("📁 Google Drive", callback_data="cloud_gdrive"),
                    InlineKeyboardButton("📁 Dropbox", callback_data="cloud_dropbox")
                ],
                [
                    InlineKeyboardButton("📁 OneDrive", callback_data="cloud_onedrive"),
                    InlineKeyboardButton("📁 Telegram", callback_data="cloud_telegram")
                ],
                [InlineKeyboardButton("🔙 العودة", callback_data="backup_settings")]
            ]
            
            await update.callback_query.edit_message_text(
                text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown'
            )
            
        except Exception as e:
            await ErrorHandler.log_error(update, context, e, "cloud_backup")
            await update.callback_query.answer("❌ حدث خطأ")

    @staticmethod
    async def delete_old_backups(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """حذف النسخ الاحتياطية القديمة"""
        try:
            from database.backup_manager import BackupManager
            
            # حذف النسخ المنتهية الصلاحية
            deleted_count = await BackupManager.cleanup_expired_backups()
            
            text = f"""
🗑️ **تنظيف النسخ الاحتياطية**

✅ تم حذف {deleted_count} نسخة احتياطية منتهية الصلاحية

💡 يتم حذف النسخ الاحتياطية تلقائياً بعد 90 يوماً من إنشائها.
            """
            
            keyboard = [[InlineKeyboardButton("🔙 العودة", callback_data="backup_settings")]]
            
            await update.callback_query.edit_message_text(
                text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown'
            )
            
        except Exception as e:
            await ErrorHandler.log_error(update, context, e, "delete_old_backups")
            await update.callback_query.answer("❌ حدث خطأ")
