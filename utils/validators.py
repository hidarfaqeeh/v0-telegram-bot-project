import re
import validators
from typing import Optional, Tuple, List
import psutil

class DataValidator:
    @staticmethod
    def validate_chat_id(chat_id_str: str) -> Tuple[bool, Optional[int], str]:
        """التحقق من صحة معرف المحادثة"""
        try:
            chat_id = int(chat_id_str)
            
            # التحقق من النطاق المسموح
            if abs(chat_id) < 1000000000:
                return False, None, "❌ معرف المحادثة غير صحيح"
            
            return True, chat_id, "✅ معرف صحيح"
            
        except ValueError:
            return False, None, "❌ يجب أن يكون المعرف رقماً"
    
    @staticmethod
    def validate_task_name(name: str) -> Tuple[bool, str]:
        """التحقق من صحة اسم المهمة"""
        if not name or not name.strip():
            return False, "❌ اسم المهمة لا يمكن أن يكون فارغاً"
        
        if len(name.strip()) < 3:
            return False, "❌ اسم المهمة يجب أن يكون 3 أحرف على الأقل"
        
        if len(name.strip()) > 50:
            return False, "❌ اسم المهمة طويل جداً (الحد الأقصى 50 حرف)"
        
        # التحقق من الأحرف المسموحة
        if not re.match(r'^[a-zA-Z0-9\u0600-\u06FF\s_-]+$', name.strip()):
            return False, "❌ اسم المهمة يحتوي على أحرف غير مسموحة"
        
        return True, "✅ اسم صحيح"
    
    @staticmethod
    def validate_delay_time(delay_str: str) -> Tuple[bool, Optional[int], str]:
        """التحقق من صحة وقت التأخير"""
        try:
            delay = int(delay_str)
            
            if delay < 0:
                return False, None, "❌ وقت التأخير لا يمكن أن يكون سالباً"
            
            if delay > 3600:  # ساعة واحدة كحد أقصى
                return False, None, "❌ وقت التأخير طويل جداً (الحد الأقصى ساعة واحدة)"
            
            return True, delay, "✅ وقت صحيح"
            
        except ValueError:
            return False, None, "❌ يجب أن يكون الوقت رقماً بالثواني"
    
    @staticmethod
    def validate_replacement_text(old_text: str, new_text: str) -> Tuple[bool, str]:
        """التحقق من صحة نص الاستبدال"""
        if not old_text or not old_text.strip():
            return False, "❌ النص القديم لا يمكن أن يكون فارغاً"
        
        if len(old_text.strip()) > 200:
            return False, "❌ النص القديم طويل جداً"
        
        if len(new_text) > 200:
            return False, "❌ النص الجديد طويل جداً"
        
        return True, "✅ نص صحيح"
    
    @staticmethod
    def validate_user_id(user_id_str: str) -> Tuple[bool, Optional[int], str]:
        """التحقق من صحة معرف المستخدم"""
        try:
            user_id = int(user_id_str)
            
            if user_id <= 0:
                return False, None, "❌ معرف المستخدم يجب أن يكون رقماً موجباً"
            
            if user_id < 1000000:
                return False, None, "❌ معرف المستخدم غير صحيح"
            
            return True, user_id, "✅ معرف صحيح"
            
        except ValueError:
            return False, None, "❌ يجب أن يكون المعرف رقماً"
    
    @staticmethod
    def validate_api_id(api_id_str: str) -> Tuple[bool, Optional[int], str]:
        """التحقق من صحة API ID"""
        try:
            api_id = int(api_id_str)
            
            if api_id <= 0:
                return False, None, "❌ API ID يجب أن يكون رقماً موجباً"
            
            if api_id < 100000:
                return False, None, "❌ API ID قصير جداً (يجب أن يكون 6 أرقام على الأقل)"
            
            if api_id > 999999999:
                return False, None, "❌ API ID طويل جداً"
            
            return True, api_id, "✅ API ID صحيح"
            
        except ValueError:
            return False, None, "❌ API ID يجب أن يكون رقماً"
    
    @staticmethod
    def validate_api_hash(api_hash: str) -> Tuple[bool, str]:
        """التحقق من صحة API Hash"""
        if not api_hash or not api_hash.strip():
            return False, "❌ API Hash لا يمكن أن يكون فارغاً"
        
        api_hash = api_hash.strip()
        
        if len(api_hash) != 32:
            return False, "❌ API Hash يجب أن يكون 32 حرف بالضبط"
        
        if not re.match(r'^[a-f0-9]{32}$', api_hash.lower()):
            return False, "❌ API Hash يجب أن يحتوي على أحرف وأرقام فقط (a-f, 0-9)"
        
        return True, "✅ API Hash صحيح"
    
    @staticmethod
    def validate_phone_number(phone: str) -> Tuple[bool, str]:
        """التحقق من صحة رقم الهاتف"""
        if not phone or not phone.strip():
            return False, "❌ رقم الهاتف لا يمكن أن يكون فارغاً"
        
        # إزالة المسافات والرموز غير الضرورية
        clean_phone = re.sub(r'[^\d+]', '', phone.strip())
        
        if not clean_phone.startswith('+'):
            return False, "❌ رقم الهاتف يجب أن يبدأ بـ + متبوعاً برمز البلد"
        
        # إزالة علامة + للتحقق من الطول
        phone_digits = clean_phone[1:]
        
        if not phone_digits.isdigit():
            return False, "❌ رقم الهاتف يجب أن يحتوي على أرقام فقط بعد رمز البلد"
        
        if len(phone_digits) < 10 or len(phone_digits) > 15:
            return False, "❌ رقم الهاتف غير صحيح (يجب أن يكون بين 10-15 رقم)"
        
        return True, "✅ رقم هاتف صحيح"
    
    @staticmethod
    def validate_word(word: str) -> Tuple[bool, str]:
        """التحقق من صحة الكلمة"""
        if not word or not word.strip():
            return False, "❌ الكلمة لا يمكن أن تكون فارغة"
        
        if len(word.strip()) > 100:
            return False, "❌ الكلمة طويلة جداً"
        
        return True, "✅ كلمة صحيحة"
    
    @staticmethod
    def validate_url(url: str) -> Tuple[bool, str]:
        """التحقق من صحة الرابط"""
        if not url or not url.strip():
            return False, "❌ الرابط لا يمكن أن يكون فارغاً"
        
        if not validators.url(url):
            return False, "❌ الرابط غير صحيح"
        
        return True, "✅ رابط صحيح"

    @staticmethod
    def validate_task_name_advanced(name: str, user_id: int = None) -> Tuple[bool, str]:
        """التحقق المتقدم من صحة اسم المهمة"""
        if not name or not name.strip():
            return False, "❌ اسم المهمة لا يمكن أن يكون فارغاً"
        
        name = name.strip()
        
        if len(name) < 3:
            return False, "❌ اسم المهمة يجب أن يكون 3 أحرف على الأقل"
        
        if len(name) > 50:
            return False, "❌ اسم المهمة طويل جداً (الحد الأقصى 50 حرف)"
        
        # التحقق من الأحرف المسموحة
        if not re.match(r'^[a-zA-Z0-9\u0600-\u06FF\s_-]+$', name):
            return False, "❌ اسم المهمة يحتوي على أحرف غير مسموحة"
        
        # التحقق من الكلمات المحظورة
        forbidden_words = ['admin', 'bot', 'system', 'test', 'null', 'undefined']
        if any(word in name.lower() for word in forbidden_words):
            return False, "❌ اسم المهمة يحتوي على كلمات محظورة"
        
        return True, "✅ اسم صحيح"

    @staticmethod
    def validate_chat_id_advanced(chat_id_str: str) -> Tuple[bool, Optional[int], str, str]:
        """التحقق المتقدم من صحة معرف المحادثة"""
        try:
            chat_id = int(chat_id_str)
            
            # التحقق من النطاق المسموح
            if abs(chat_id) < 1000000000:
                return False, None, "❌ معرف المحادثة غير صحيح", "invalid_range"
            
            # تحديد نوع المحادثة
            chat_type = "unknown"
            if chat_id > 0:
                chat_type = "private"
            elif str(chat_id).startswith("-100"):
                chat_type = "supergroup_or_channel"
            elif chat_id < 0:
                chat_type = "group"
            
            return True, chat_id, "✅ معرف صحيح", chat_type
        
        except ValueError:
            return False, None, "❌ يجب أن يكون المعرف رقماً", "invalid_format"

    @staticmethod
    def validate_settings_integrity(settings: dict) -> Tuple[bool, str]:
        """التحقق من تكامل إعدادات المهمة"""
        blocked_words = settings.get('blocked_words', [])
        required_words = settings.get('required_words', [])
        
        # التحقق من تضارب الكلمات
        conflicts = set(blocked_words) & set(required_words)
        if conflicts:
            return False, f"❌ تضارب في الكلمات: {', '.join(conflicts)} موجودة في القائمتين"
        
        # التحقق من حدود الكلمات
        if len(blocked_words) > 100:
            return False, "❌ عدد الكلمات المحظورة كثير جداً (الحد الأقصى 100)"
        
        if len(required_words) > 50:
            return False, "❌ عدد الكلمات المطلوبة كثير جداً (الحد الأقصى 50)"
        
        # التحقق من إعدادات التأخير
        delay_settings = settings.get('delay', {})
        if delay_settings.get('enabled') and delay_settings.get('seconds', 0) > 3600:
            return False, "❌ وقت التأخير طويل جداً (الحد الأقصى ساعة واحدة)"
        
        return True, "✅ الإعدادات صحيحة"

    @staticmethod
    def validate_user_limits(user_id: int, action: str) -> Tuple[bool, str]:
        """التحقق من حدود المستخدم"""
        # هذه الدالة ستحتاج للتكامل مع قاعدة البيانات
        # سيتم تنفيذها في TaskManager
        return True, "✅ ضمن الحدود المسموحة"

    @staticmethod
    def validate_word_advanced(word: str, word_list: List[str] = None) -> Tuple[bool, str]:
        """التحقق المتقدم من صحة الكلمة"""
        if not word or not word.strip():
            return False, "❌ الكلمة لا يمكن أن تكون فارغة"
        
        word = word.strip()
        
        if len(word) > 100:
            return False, "❌ الكلمة طويلة جداً (الحد الأقصى 100 حرف)"
        
        if len(word) < 2:
            return False, "❌ الكلمة قصيرة جداً (الحد الأدنى حرفان)"
        
        # التحقق من التكرار
        if word_list and word in word_list:
            return False, f"❌ الكلمة '{word}' موجودة مسبقاً"
        
        # التحقق من الأحرف الخاصة المفرطة
        special_chars = len(re.findall(r'[^\w\s\u0600-\u06FF]', word))
        if special_chars > len(word) // 2:
            return False, "❌ الكلمة تحتوي على أحرف خاصة كثيرة"
        
        return True, "✅ كلمة صحيحة"

    @staticmethod
    def validate_system_limits() -> Tuple[bool, str]:
        """التحقق من حدود النظام العامة"""
        
        # التحقق من استخدام الذاكرة
        memory_percent = psutil.virtual_memory().percent
        if memory_percent > 90:
            return False, "❌ استخدام الذاكرة مرتفع جداً"
        
        # التحقق من مساحة القرص
        disk_percent = psutil.disk_usage('/').percent
        if disk_percent > 95:
            return False, "❌ مساحة القرص ممتلئة"
        
        return True, "✅ النظام يعمل بشكل طبيعي"
