from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from database.user_manager import UserManager
from database.task_manager import TaskManager
from utils.error_handler import ErrorHandler
from config import Config
from utils.validators import InputValidator

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
    @error_handler
    async def setting_value_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """استقبال قيمة الإعداد"""
        try:
            setting_key = context.user_data.get('setting_key')
            value_str = update.message.text.strip()
            
            if not setting_key:
                await update.message.reply_text("❌ خطأ في تحديد الإعداد")
                return ConversationHandler.END
            
            # التحقق من صحة قيمة الإعداد
            is_valid, value, message = InputValidator.validate_setting_value(setting_key, value_str)
            
            if not is_valid:
                await update.message.reply_text(
                    f"{message}\n\n🔄 يرجى إدخال قيمة صحيحة:",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("❌ إلغاء", callback_data="settings_menu")
                    ]])
                )
                return SETTING_VALUE_INPUT
            
            # حفظ الإعداد في قاعدة البيانات
            success = await SettingsHandlers.settings_manager.update_setting(setting_key, value)
            
            if success:
                # تسجيل النشاط
                await SettingsHandlers.activity_manager.log_activity(
                    user_id=update.effective_user.id,
                    action="setting_updated",
                    details=f"تم تحديث الإعداد {setting_key} إلى: {value}"
                )
                
                text = f"""
✅ **تم تحديث الإعداد بنجاح!**

**الإعداد:** {setting_key}
**القيمة الجديدة:** {value}
**تم التحديث بواسطة:** {update.effective_user.first_name}
**التاريخ:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{message}
                """
                
                keyboard = [
                    [InlineKeyboardButton("⚙️ عرض جميع الإعدادات", callback_data="settings_menu")],
                    [InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="main_menu")]
                ]
                
            else:
                text = "❌ فشل في حفظ الإعداد. يرجى المحاولة مرة أخرى."
                keyboard = [
                    [InlineKeyboardButton("🔄 المحاولة مرة أخرى", callback_data=f"setting_input_{setting_key}")],
                    [InlineKeyboardButton("🔙 العودة للإعدادات", callback_data="settings_menu")]
                ]
            
            # تنظيف البيانات المؤقتة
            context.user_data.clear()
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
            
            return ConversationHandler.END
            
        except Exception as e:
            logger.error(f"خطأ في حفظ الإعداد: {e}")
            await update.message.reply_text("❌ حدث خطأ في حفظ الإعداد")
            return ConversationHandler.END
