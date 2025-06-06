from typing import Tuple

class Validators:
    @staticmethod
    def validate_replacement_text(old_text: str, new_text: str) -> Tuple[bool, str]:
        """التحقق من صحة نص الاستبدال"""
        try:
            # التحقق من النص القديم
            if not old_text or not old_text.strip():
                return False, "❌ النص القديم لا يمكن أن يكون فارغاً"
            
            if len(old_text.strip()) > 200:
                return False, "❌ النص القديم طويل جداً (الحد الأقصى 200 حرف)"
            
            # التحقق من النص الجديد
            if len(new_text.strip()) > 500:
                return False, "❌ النص الجديد طويل جداً (الحد الأقصى 500 حرف)"
            
            # التحقق من عدم تطابق النصين
            if old_text.strip() == new_text.strip():
                return False, "❌ النص القديم والجديد متطابقان"
            
            return True, "✅ النص صحيح"
            
        except Exception as e:
            return False, f"❌ خطأ في التحقق: {str(e)}"

    @staticmethod
    def validate_delay_time(delay_str: str) -> Tuple[bool, int, str]:
        """التحقق من صحة وقت التأخير"""
        try:
            # التحقق من أن المدخل رقم
            try:
                delay = int(delay_str.strip())
            except ValueError:
                return False, 0, "❌ يجب أن يكون الوقت رقماً صحيحاً"
            
            # التحقق من النطاق المسموح
            if delay < 0:
                return False, 0, "❌ لا يمكن أن يكون الوقت سالباً"
            
            if delay > 3600:  # ساعة واحدة كحد أقصى
                return False, 0, "❌ الحد الأقصى للتأخير هو 3600 ثانية (ساعة واحدة)"
            
            return True, delay, "✅ الوقت صحيح"
            
        except Exception as e:
            return False, 0, f"❌ خطأ في التحقق: {str(e)}"

    @staticmethod
    def validate_user_id(user_id_str: str) -> Tuple[bool, int, str]:
        """التحقق من صحة معرف المستخدم"""
        try:
            # التحقق من أن المدخل رقم
            try:
                user_id = int(user_id_str.strip())
            except ValueError:
                return False, 0, "❌ معرف المستخدم يجب أن يكون رقماً"
            
            # التحقق من النطاق المسموح لمعرفات Telegram
            if user_id <= 0:
                return False, 0, "❌ معرف المستخدم يجب أن يكون رقماً موجباً"
            
            if user_id > 2147483647:  # حد معرفات Telegram
                return False, 0, "❌ معرف المستخدم كبير جداً"
            
            return True, user_id, "✅ معرف المستخدم صحيح"
            
        except Exception as e:
            return False, 0, f"❌ خطأ في التحقق: {str(e)}"

    @staticmethod
    def validate_settings_integrity(settings: dict) -> Tuple[bool, str]:
        """التحقق من سلامة إعدادات المهمة"""
        try:
            # التحقق من البنية الأساسية
            if not isinstance(settings, dict):
                return False, "❌ الإعدادات يجب أن تكون من نوع dict"
            
            # التحقق من فلاتر الوسائط
            if 'media_filters' in settings:
                media_filters = settings['media_filters']
                if not isinstance(media_filters, dict):
                    return False, "❌ إعدادات فلاتر الوسائط غير صحيحة"
                
                if 'allowed_types' in media_filters:
                    allowed_types = media_filters['allowed_types']
                    if not isinstance(allowed_types, list):
                        return False, "❌ قائمة أنواع الوسائط المسموحة غير صحيحة"
            
            # التحقق من الكلمات المحظورة والمطلوبة
            if 'blocked_words' in settings:
                if not isinstance(settings['blocked_words'], list):
                    return False, "❌ قائمة الكلمات المحظورة غير صحيحة"
            
            if 'required_words' in settings:
                if not isinstance(settings['required_words'], list):
                    return False, "❌ قائمة الكلمات المطلوبة غير صحيحة"
            
            # التحقق من الاستبدالات
            if 'replacements' in settings:
                if not isinstance(settings['replacements'], dict):
                    return False, "❌ قائمة الاستبدالات غير صحيحة"
            
            # التحقق من القوائم البيضاء والسوداء
            if 'whitelist' in settings:
                if not isinstance(settings['whitelist'], list):
                    return False, "❌ القائمة البيضاء غير صحيحة"
            
            if 'blacklist' in settings:
                if not isinstance(settings['blacklist'], list):
                    return False, "❌ القائمة السوداء غير صحيحة"
            
            # التحقق من إعدادات التأخير
            if 'delay' in settings:
                delay_settings = settings['delay']
                if not isinstance(delay_settings, dict):
                    return False, "❌ إعدادات التأخير غير صحيحة"
                
                if 'seconds' in delay_settings:
                    seconds = delay_settings['seconds']
                    if not isinstance(seconds, (int, float)) or seconds < 0:
                        return False, "❌ وقت التأخير غير صحيح"
            
            return True, "✅ الإعدادات صحيحة"
            
        except Exception as e:
            return False, f"❌ خطأ في التحقق: {str(e)}"
