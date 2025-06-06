from telegram import Update
from telegram.ext import ContextTypes

from task_manager import TaskManager
from error_handler import ErrorHandler


class TaskSettingsHandlers:
    """
    Handlers for task settings management.
    """

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
