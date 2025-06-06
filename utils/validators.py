import re
import validators
from typing import Optional, Tuple, List

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
    def validate_api_credentials(api_id_str: str, api_hash: str) -> Tuple[bool, str]:
        """التحقق من صحة بيانات API"""
        try:
            api_id = int(api_id_str)
            
            if api_id <= 0:
                return False, "❌ API ID يجب أن يكون رقماً موجباً"
            
        except ValueError:
            return False, "❌ API ID يجب أن يكون رقماً"
        
        if not api_hash or len(api_hash) != 32:
            return False, "❌ API Hash يجب أن يكون 32 حرف"
        
        if not re.match(r'^[a-f0-9]{32}$', api_hash):
            return False, "❌ API Hash يحتوي على أحرف غير صحيحة"
        
        return True, "✅ بيانات API صحيحة"
    
    @staticmethod
    def validate_phone_number(phone: str) -> Tuple[bool, str]:
        """التحقق من صحة رقم الهاتف"""
        # إزالة المسافات والرموز
        clean_phone = re.sub(r'[^\d+]', '', phone)
        
        if not clean_phone.startswith('+'):
            return False, "❌ رقم الهاتف يجب أن يبدأ بـ +"
        
        if len(clean_phone) < 10 or len(clean_phone) > 15:
            return False, "❌ رقم الهاتف غير صحيح"
        
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
