from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from database.user_manager import UserManager
from database.task_manager import TaskManager
from database.statistics_manager import StatisticsManager
from utils.error_handler import ErrorHandler
from config import Config

# حالات المحادثة لإدارة المستخدمين
SEARCH_USER_INPUT, BAN_REASON_INPUT, ADMIN_USER_INPUT = range(3)

class UsersHandlers:
    @staticmethod
    async def view_all_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """عرض جميع المستخدمين مع التصفح"""
        user_id = update.effective_user.id
        
        # التحقق من صلاحيات المدير
        if not await UserManager.is_admin(user_id) and user_id != Config.ADMIN_USER_ID:
            await update.callback_query.answer("❌ غير مصرح لك بالوصول لهذه الميزة")
            return
        
        page = int(context.user_data.get('users_page', 1))
        users_per_page = 5
        
        users = await UserManager.get_all_users()
        total_pages = (len(users) + users_per_page - 1) // users_per_page
        
        start_idx = (page - 1) * users_per_page
        end_idx = start_idx + users_per_page
        page_users = users[start_idx:end_idx]
        
        text = f"👥 **جميع المستخدمين** (صفحة {page}/{total_pages})\n\n"
        
        keyboard = []
        for user in page_users:
            name = user['first_name'] or user['username'] or f"User {user['user_id']}"
            status = "👑" if user['is_admin'] else "👤"
            active = "🟢" if user['is_active'] else "🔴"
            
            text += f"{active} {status} **{name}**\n"
            text += f"   ID: `{user['user_id']}`\n"
            text += f"   آخر نشاط: {user['last_activity'].strftime('%Y-%m-%d')}\n\n"
            
            keyboard.append([
                InlineKeyboardButton(
                    f"⚙️ إدارة {name}", 
                    callback_data=f"manage_user_{user['user_id']}"
                )
            ])
        
        # أزرار التصفح
        nav_buttons = []
        if page > 1:
            nav_buttons.append(
                InlineKeyboardButton("⬅️ السابق", callback_data="users_page_prev")
            )
        if page < total_pages:
            nav_buttons.append(
                InlineKeyboardButton("التالي ➡️", callback_data="users_page_next")
            )
        
        if nav_buttons:
            keyboard.append(nav_buttons)
        
        keyboard.append([InlineKeyboardButton("🔙 العودة", callback_data="users_menu")])
        
        await update.callback_query.edit_message_text(
            text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown'
        )
    
    @staticmethod
    async def manage_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """إدارة مستخدم محدد"""
        target_user_id = int(update.callback_query.data.split('_')[-1])
        admin_user_id = update.effective_user.id
        
        # التحقق من صلاحيات المدير
        if not await UserManager.is_admin(admin_user_id) and admin_user_id != Config.ADMIN_USER_ID:
            await update.callback_query.answer("❌ غير مصرح لك بالوصول لهذه الميزة")
            return
        
        # الحصول على بيانات المستخدم
        user = await UserManager.get_user(target_user_id)
        if not user:
            await update.callback_query.answer("❌ المستخدم غير موجود")
            return
        
        # الحصول على إحصائيات المستخدم
        user_stats = await StatisticsManager.get_user_stats(target_user_id)
        user_tasks = await TaskManager.get_user_tasks(target_user_id)
        
        name = user['first_name'] or user['username'] or f"User {user['user_id']}"
        status = "👑 مدير" if user['is_admin'] else "👤 مستخدم"
        active_status = "🟢 نشط" if user['is_active'] else "🔴 غير نشط"
        
        text = f"""
👤 **إدارة المستخدم**

**الاسم:** {name}
**المعرف:** @{user['username'] or 'غير متاح'}
**ID:** `{user['user_id']}`
**الحالة:** {status}
**النشاط:** {active_status}
**تاريخ التسجيل:** {user['created_at'].strftime('%Y-%m-%d')}
**آخر نشاط:** {user['last_activity'].strftime('%Y-%m-%d %H:%M')}

📊 **الإحصائيات:**
• المهام الإجمالية: {user_stats.get('total_tasks', 0)}
• المهام النشطة: {user_stats.get('active_tasks', 0)}
• الرسائل المُوجهة: {user_stats.get('total_forwarded', 0):,}
• الرسائل المُرشحة: {user_stats.get('total_filtered', 0):,}
        """
        
        keyboard = []
        
        # أزرار الإدارة
        if user['is_admin']:
            keyboard.append([
                InlineKeyboardButton("👤 إزالة صلاحيات المدير", callback_data=f"remove_admin_{target_user_id}")
            ])
        else:
            keyboard.append([
                InlineKeyboardButton("👑 منح صلاحيات المدير", callback_data=f"make_admin_{target_user_id}")
            ])
        
        if user['is_active']:
            keyboard.append([
                InlineKeyboardButton("🚫 حظر المستخدم", callback_data=f"ban_user_{target_user_id}")
            ])
        else:
            keyboard.append([
                InlineKeyboardButton("✅ إلغاء حظر المستخدم", callback_data=f"unban_user_{target_user_id}")
            ])
        
        keyboard.extend([
            [
                InlineKeyboardButton("📋 عرض المهام", callback_data=f"user_tasks_{target_user_id}"),
                InlineKeyboardButton("📊 الإحصائيات المفصلة", callback_data=f"user_detailed_stats_{target_user_id}")
            ],
            [
                InlineKeyboardButton("💬 إرسال رسالة", callback_data=f"message_user_{target_user_id}"),
                InlineKeyboardButton("📤 تصدير البيانات", callback_data=f"export_user_data_{target_user_id}")
            ],
            [InlineKeyboardButton("🔙 العودة", callback_data="view_all_users")]
        ])
        
        await update.callback_query.edit_message_text(
            text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown'
        )
    
    @staticmethod
    async def search_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """البحث عن مستخدم"""
        text = """
🔍 **البحث عن مستخدم**

أرسل أحد البيانات التالية للبحث:
• معرف المستخدم (User ID)
• اسم المستخدم (@username)
• الاسم الأول
        """
        
        keyboard = [[InlineKeyboardButton("❌ إلغاء", callback_data="users_menu")]]
        
        await update.callback_query.edit_message_text(
            text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown'
        )
        
        return SEARCH_USER_INPUT
    
    @staticmethod
    async def search_user_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة البحث عن المستخدم"""
        search_term = update.message.text.strip()
        
        try:
            # البحث بمعرف المستخدم
            if search_term.isdigit():
                user = await UserManager.get_user(int(search_term))
                if user:
                    users = [user]
                else:
                    users = []
            else:
                # البحث بالاسم أو المعرف
                users = await UserManager.search_users(search_term)
            
            if not users:
                text = f"❌ لم يتم العثور على مستخدمين بالبحث: `{search_term}`"
                keyboard = [[InlineKeyboardButton("🔙 العودة", callback_data="users_menu")]]
            else:
                text = f"🔍 **نتائج البحث عن:** `{search_term}`\n\n"
                keyboard = []
                
                for user in users[:10]:  # أول 10 نتائج
                    name = user['first_name'] or user['username'] or f"User {user['user_id']}"
                    status = "👑" if user['is_admin'] else "👤"
                    active = "🟢" if user['is_active'] else "🔴"
                    
                    text += f"{active} {status} **{name}**\n"
                    text += f"   ID: `{user['user_id']}`\n\n"
                    
                    keyboard.append([
                        InlineKeyboardButton(
                            f"⚙️ إدارة {name}", 
                            callback_data=f"manage_user_{user['user_id']}"
                        )
                    ])
                
                keyboard.append([InlineKeyboardButton("🔙 العودة", callback_data="users_menu")])
            
            await update.message.reply_text(
                text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown'
            )
            
            return ConversationHandler.END
            
        except Exception as e:
            await ErrorHandler.log_error(update, context, e, "search_user_input")
            await update.message.reply_text("❌ حدث خطأ أثناء البحث")
            return ConversationHandler.END
    
    @staticmethod
    async def manage_admins(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """إدارة المديرين"""
        user_id = update.effective_user.id
        
        # التحقق من صلاحيات المدير الرئيسي
        if user_id != Config.ADMIN_USER_ID:
            await update.callback_query.answer("❌ هذه الميزة متاحة للمدير الرئيسي فقط")
            return
        
        # الحصول على قائمة المديرين
        users = await UserManager.get_all_users()
        admins = [user for user in users if user['is_admin']]
        
        text = f"👑 **إدارة المديرين** ({len(admins)} مدير)\n\n"
        
        keyboard = []
        for admin in admins:
            name = admin['first_name'] or admin['username'] or f"User {admin['user_id']}"
            active = "🟢" if admin['is_active'] else "🔴"
            
            text += f"{active} **{name}**\n"
            text += f"   ID: `{admin['user_id']}`\n\n"
            
            if admin['user_id'] != Config.ADMIN_USER_ID:  # لا يمكن إزالة المدير الرئيسي
                keyboard.append([
                    InlineKeyboardButton(
                        f"❌ إزالة {name}", 
                        callback_data=f"remove_admin_{admin['user_id']}"
                    )
                ])
        
        keyboard.extend([
            [InlineKeyboardButton("➕ إضافة مدير جديد", callback_data="add_admin")],
            [InlineKeyboardButton("🔙 العودة", callback_data="users_menu")]
        ])
        
        await update.callback_query.edit_message_text(
            text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown'
        )
    
    @staticmethod
    async def make_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """منح صلاحيات المدير"""
        target_user_id = int(update.callback_query.data.split('_')[-1])
        admin_user_id = update.effective_user.id
        
        # التحقق من صلاحيات المدير الرئيسي
        if admin_user_id != Config.ADMIN_USER_ID:
            await update.callback_query.answer("❌ هذه الميزة متاحة للمدير الرئيسي فقط")
            return
        
        success = await UserManager.set_admin(target_user_id, True)
        
        if success:
            await update.callback_query.answer("✅ تم منح صلاحيات المدير")
            # إعادة عرض صفحة إدارة المستخدم
            context.user_data['callback_data'] = f"manage_user_{target_user_id}"
            await UsersHandlers.manage_user(update, context)
        else:
            await update.callback_query.answer("❌ فشل في منح صلاحيات المدير")
    
    @staticmethod
    async def remove_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """إزالة صلاحيات المدير"""
        target_user_id = int(update.callback_query.data.split('_')[-1])
        admin_user_id = update.effective_user.id
        
        # التحقق من صلاحيات المدير الرئيسي
        if admin_user_id != Config.ADMIN_USER_ID:
            await update.callback_query.answer("❌ هذه الميزة متاحة للمدير الرئيسي فقط")
            return
        
        # لا يمكن إزالة المدير الرئيسي
        if target_user_id == Config.ADMIN_USER_ID:
            await update.callback_query.answer("❌ لا يمكن إزالة صلاحيات المدير الرئيسي")
            return
        
        success = await UserManager.set_admin(target_user_id, False)
        
        if success:
            await update.callback_query.answer("✅ تم إزالة صلاحيات المدير")
            # إعادة عرض صفحة إدارة المستخدم
            context.user_data['callback_data'] = f"manage_user_{target_user_id}"
            await UsersHandlers.manage_user(update, context)
        else:
            await update.callback_query.answer("❌ فشل في إزالة صلاحيات المدير")
    
    @staticmethod
    async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """حظر مستخدم"""
        target_user_id = int(update.callback_query.data.split('_')[-1])
        admin_user_id = update.effective_user.id
        
        # التحقق من الصلاحيات
        if not await UserManager.is_admin(admin_user_id) and admin_user_id != Config.ADMIN_USER_ID:
            await update.callback_query.answer("❌ غير مصرح لك بهذه العملية")
            return
        
        # لا يمكن حظر المدير الرئيسي
        if target_user_id == Config.ADMIN_USER_ID:
            await update.callback_query.answer("❌ لا يمكن حظر المدير الرئيسي")
            return
        
        success = await UserManager.ban_user(target_user_id)
        
        if success:
            await update.callback_query.answer("✅ تم حظر المستخدم")
            # إعادة عرض صفحة إدارة المستخدم
            context.user_data['callback_data'] = f"manage_user_{target_user_id}"
            await UsersHandlers.manage_user(update, context)
        else:
            await update.callback_query.answer("❌ فشل في حظر المستخدم")
    
    @staticmethod
    async def unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """إلغاء حظر مستخدم"""
        target_user_id = int(update.callback_query.data.split('_')[-1])
        admin_user_id = update.effective_user.id
        
        # التحقق من الصلاحيات
        if not await UserManager.is_admin(admin_user_id) and admin_user_id != Config.ADMIN_USER_ID:
            await update.callback_query.answer("❌ غير مصرح لك بهذه العملية")
            return
        
        success = await UserManager.unban_user(target_user_id)
        
        if success:
            await update.callback_query.answer("✅ تم إلغاء حظر المستخدم")
            # إعادة عرض صفحة إدارة المستخدم
            context.user_data['callback_data'] = f"manage_user_{target_user_id}"
            await UsersHandlers.manage_user(update, context)
        else:
            await update.callback_query.answer("❌ فشل في إلغاء حظر المستخدم")
    
    @staticmethod
    async def users_statistics(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """إحصائيات المستخدمين المفصلة"""
        user_id = update.effective_user.id
        
        # التحقق من الصلاحيات
        if not await UserManager.is_admin(user_id) and user_id != Config.ADMIN_USER_ID:
            await update.callback_query.answer("❌ غير مصرح لك بالوصول لهذه الميزة")
            return
        
        # الحصول على الإحصائيات
        users = await UserManager.get_all_users()
        total_users = len(users)
        active_users = len([u for u in users if u['is_active']])
        admin_users = len([u for u in users if u['is_admin']])
        banned_users = total_users - active_users
        
        # إحصائيات التسجيل
        from datetime import datetime, timedelta
        today = datetime.now().date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        new_users_today = len([u for u in users if u['created_at'].date() == today])
        new_users_week = len([u for u in users if u['created_at'].date() >= week_ago])
        new_users_month = len([u for u in users if u['created_at'].date() >= month_ago])
        
        # إحصائيات النشاط
        active_today = len([u for u in users if u['last_activity'].date() == today])
        active_week = len([u for u in users if u['last_activity'].date() >= week_ago])
        
        text = f"""
📊 **إحصائيات المستخدمين المفصلة**

👥 **إجمالي المستخدمين:**
• المجموع: {total_users:,}
• النشطين: {active_users:,} ({(active_users/total_users*100):.1f}%)
• المحظورين: {banned_users:,} ({(banned_users/total_users*100):.1f}%)
• المديرين: {admin_users:,}

📈 **المستخدمين الجدد:**
• اليوم: {new_users_today:,}
• هذا الأسبوع: {new_users_week:,}
• هذا الشهر: {new_users_month:,}

⚡ **النشاط:**
• نشطين اليوم: {active_today:,}
• نشطين هذا الأسبوع: {active_week:,}
• معدل النشاط: {(active_week/total_users*100):.1f}%
        """
        
        keyboard = [
            [
                InlineKeyboardButton("📊 رسم بياني", callback_data="users_chart"),
                InlineKeyboardButton("📋 تقرير مفصل", callback_data="detailed_users_report")
            ],
            [
                InlineKeyboardButton("📤 تصدير البيانات", callback_data="export_users_data"),
                InlineKeyboardButton("🔄 تحديث", callback_data="users_statistics")
            ],
            [InlineKeyboardButton("🔙 العودة", callback_data="users_menu")]
        ]
        
        await update.callback_query.edit_message_text(
            text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown'
        )
