"""
Input Validators - معالجات التحقق من صحة الإدخال
نظام شامل للتحقق من صحة جميع أنواع الإدخالات
"""

import re
import asyncio
from typing import Tuple, Optional, Dict, Any, List
from datetime import datetime, timedelta
import logging

from telethon import TelegramClient
from telethon.errors import (
    ApiIdInvalidError, 
    PhoneNumberInvalidError,
    PhoneCodeInvalidError,
    SessionPasswordNeededError
)

logger = logging.getLogger(__name__)

class InputValidator:
    """كلاس التحقق من صحة الإدخالات"""
    
    # أنماط التحقق
    PATTERNS = {
        'phone': re.compile(r'^\+?[1-9]\d{1,14}$'),
        'username': re.compile(r'^@?[a-zA-Z0-9_]{5,32}$'),
        'chat_id': re.compile(r'^-?\d+$'),
        'api_hash': re.compile(r'^[a-f0-9]{32}$'),
        'task_name': re.compile(r'^[a-zA-Z0-9\u0600-\u06FF\s_-]{1,50}$'),
        'keyword': re.compile(r'^.{1,100}$'),
        'time_format': re.compile(r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$')
    }
    
    # نطاقات صحيحة
    RANGES = {
        'api_id': (1, 999999999),
        'user_id': (1, 999999999999),
        'chat_id': (-999999999999, 999999999999),
        'delay_seconds': (1, 3600),
        'max_messages': (1, 10000)
    }
    
    @staticmethod
    def validate_api_id(api_id_str: str) -> Tuple[bool, Optional[int], str]:
        """
        التحقق من صحة API ID
        
        Args:
            api_id_str: API ID كنص
            
        Returns:
            Tuple[bool, Optional[int], str]: (صحيح/خطأ, API ID, رسالة)
        """
        try:
            # التحقق من أنه رقم
            api_id = int(api_id_str.strip())
            
            # التحقق من النطاق
            min_id, max_id = InputValidator.RANGES['api_id']
            if not (min_id <= api_id <= max_id):
                return False, None, f"❌ API ID يجب أن يكون بين {min_id} و {max_id}"
            
            # التحقق من أنه ليس رقماً شائعاً خاطئاً
            invalid_ids = [123456, 111111, 000000, 999999]
            if api_id in invalid_ids:
                return False, None, "❌ API ID غير صحيح. يرجى استخدام API ID الحقيقي من my.telegram.org"
            
            return True, api_id, "✅ API ID صحيح"
            
        except ValueError:
            return False, None, "❌ API ID يجب أن يكون رقماً صحيحاً"
        except Exception as e:
            logger.error(f"خطأ في التحقق من API ID: {e}")
            return False, None, "❌ خطأ في التحقق من API ID"
    
    @staticmethod
    def validate_api_hash(api_hash: str) -> Tuple[bool, str]:
        """
        التحقق من صحة API Hash
        
        Args:
            api_hash: API Hash
            
        Returns:
            Tuple[bool, str]: (صحيح/خطأ, رسالة)
        """
        try:
            api_hash = api_hash.strip().lower()
            
            # التحقق من الطول
            if len(api_hash) != 32:
                return False, "❌ API Hash يجب أن يكون 32 حرفاً بالضبط"
            
            # التحقق من النمط (أحرف وأرقام فقط)
            if not InputValidator.PATTERNS['api_hash'].match(api_hash):
                return False, "❌ API Hash يجب أن يحتوي على أحرف وأرقام فقط (a-f, 0-9)"
            
            # التحقق من أنه ليس hash شائعاً خاطئاً
            invalid_hashes = [
                '0' * 32,
                '1' * 32,
                'a' * 32,
                'f' * 32
            ]
            if api_hash in invalid_hashes:
                return False, "❌ API Hash غير صحيح. يرجى استخدام API Hash الحقيقي من my.telegram.org"
            
            return True, "✅ API Hash صحيح"
            
        except Exception as e:
            logger.error(f"خطأ في التحقق من API Hash: {e}")
            return False, "❌ خطأ في التحقق من API Hash"
    
    @staticmethod
    def validate_phone_number(phone: str) -> Tuple[bool, Optional[str], str]:
        """
        التحقق من صحة رقم الهاتف
        
        Args:
            phone: رقم الهاتف
            
        Returns:
            Tuple[bool, Optional[str], str]: (صحيح/خطأ, رقم منسق, رسالة)
        """
        try:
            # تنظيف الرقم
            phone = re.sub(r'[^\d+]', '', phone.strip())
            
            # إضافة + إذا لم تكن موجودة
            if not phone.startswith('+'):
                phone = '+' + phone
            
            # التحقق من النمط
            if not InputValidator.PATTERNS['phone'].match(phone):
                return False, None, "❌ رقم الهاتف غير صحيح. يجب أن يكون بالصيغة: +1234567890"
            
            # التحقق من الطول
            if len(phone) < 8 or len(phone) > 16:
                return False, None, "❌ رقم الهاتف يجب أن يكون بين 8 و 16 رقماً"
            
            return True, phone, "✅ رقم الهاتف صحيح"
            
        except Exception as e:
            logger.error(f"خطأ في التحقق من رقم الهاتف: {e}")
            return False, None, "❌ خطأ في التحقق من رقم الهاتف"
    
    @staticmethod
    def validate_verification_code(code: str) -> Tuple[bool, Optional[str], str]:
        """
        التحقق من صحة كود التحقق
        
        Args:
            code: كود التحقق
            
        Returns:
            Tuple[bool, Optional[str], str]: (صحيح/خطأ, كود منظف, رسالة)
        """
        try:
            # تنظيف الكود
            code = re.sub(r'[^\d]', '', code.strip())
            
            # التحقق من الطول
            if len(code) != 5:
                return False, None, "❌ كود التحقق يجب أن يكون 5 أرقام"
            
            # التحقق من أنه أرقام فقط
            if not code.isdigit():
                return False, None, "❌ كود التحقق يجب أن يحتوي على أرقام فقط"
            
            return True, code, "✅ كود التحقق صحيح"
            
        except Exception as e:
            logger.error(f"خطأ في التحقق من كود التحقق: {e}")
            return False, None, "❌ خطأ في التحقق من كود التحقق"
    
    @staticmethod
    def validate_chat_id(chat_id_str: str) -> Tuple[bool, Optional[int], str]:
        """
        التحقق من صحة معرف المحادثة
        
        Args:
            chat_id_str: معرف المحادثة كنص
            
        Returns:
            Tuple[bool, Optional[int], str]: (صحيح/خطأ, معرف المحادثة, رسالة)
        """
        try:
            # تنظيف المعرف
            chat_id_str = chat_id_str.strip()
            
            # التحقق من النمط
            if not InputValidator.PATTERNS['chat_id'].match(chat_id_str):
                return False, None, "❌ معرف المحادثة يجب أن يكون رقماً صحيحاً"
            
            chat_id = int(chat_id_str)
            
            # التحقق من النطاق
            min_id, max_id = InputValidator.RANGES['chat_id']
            if not (min_id <= chat_id <= max_id):
                return False, None, f"❌ معرف المحادثة خارج النطاق المسموح"
            
            # التحقق من أنه ليس صفراً
            if chat_id == 0:
                return False, None, "❌ معرف المحادثة لا يمكن أن يكون صفراً"
            
            return True, chat_id, "✅ معرف المحادثة صحيح"
            
        except ValueError:
            return False, None, "❌ معرف المحادثة يجب أن يكون رقماً صحيحاً"
        except Exception as e:
            logger.error(f"خطأ في التحقق من معرف المحادثة: {e}")
            return False, None, "❌ خطأ في التحقق من معرف المحادثة"
    
    @staticmethod
    def validate_username(username: str) -> Tuple[bool, Optional[str], str]:
        """
        التحقق من صحة اسم المستخدم
        
        Args:
            username: اسم المستخدم
            
        Returns:
            Tuple[bool, Optional[str], str]: (صحيح/خطأ, اسم منظف, رسالة)
        """
        try:
            # تنظيف اسم المستخدم
            username = username.strip()
            
            # إضافة @ إذا لم تكن موجودة
            if not username.startswith('@'):
                username = '@' + username
            
            # التحقق من النمط
            if not InputValidator.PATTERNS['username'].match(username):
                return False, None, "❌ اسم المستخدم غير صحيح. يجب أن يكون بين 5-32 حرف ويحتوي على أحرف وأرقام و _ فقط"
            
            return True, username, "✅ اسم المستخدم صحيح"
            
        except Exception as e:
            logger.error(f"خطأ في التحقق من اسم المستخدم: {e}")
            return False, None, "❌ خطأ في التحقق من اسم المستخدم"
    
    @staticmethod
    def validate_task_name(task_name: str) -> Tuple[bool, Optional[str], str]:
        """
        التحقق من صحة اسم المهمة
        
        Args:
            task_name: اسم المهمة
            
        Returns:
            Tuple[bool, Optional[str], str]: (صحيح/خطأ, اسم منظف, رسالة)
        """
        try:
            # تنظيف الاسم
            task_name = task_name.strip()
            
            # التحقق من الطول
            if len(task_name) < 1:
                return False, None, "❌ اسم المهمة لا يمكن أن يكون فارغاً"
            
            if len(task_name) > 50:
                return False, None, "❌ اسم المهمة يجب أن يكون أقل من 50 حرفاً"
            
            # التحقق من النمط
            if not InputValidator.PATTERNS['task_name'].match(task_name):
                return False, None, "❌ اسم المهمة يحتوي على أحرف غير مسموحة"
            
            return True, task_name, "✅ اسم المهمة صحيح"
            
        except Exception as e:
            logger.error(f"خطأ في التحقق من اسم المهمة: {e}")
            return False, None, "❌ خطأ في التحقق من اسم المهمة"
    
    @staticmethod
    def validate_user_id(user_id_str: str) -> Tuple[bool, Optional[int], str]:
        """
        التحقق من صحة معرف المستخدم
        
        Args:
            user_id_str: معرف المستخدم كنص
            
        Returns:
            Tuple[bool, Optional[int], str]: (صحيح/خطأ, معرف المستخدم, رسالة)
        """
        try:
            user_id = int(user_id_str.strip())
            
            # التحقق من النطاق
            min_id, max_id = InputValidator.RANGES['user_id']
            if not (min_id <= user_id <= max_id):
                return False, None, f"❌ معرف المستخدم خارج النطاق المسموح"
            
            return True, user_id, "✅ معرف المستخدم صحيح"
            
        except ValueError:
            return False, None, "❌ معرف المستخدم يجب أن يكون رقماً صحيحاً"
        except Exception as e:
            logger.error(f"خطأ في التحقق من معرف المستخدم: {e}")
            return False, None, "❌ خطأ في التحقق من معرف المستخدم"
    
    @staticmethod
    def validate_keyword(keyword: str) -> Tuple[bool, Optional[str], str]:
        """
        التحقق من صحة الكلمة المفتاحية
        
        Args:
            keyword: الكلمة المفتاحية
            
        Returns:
            Tuple[bool, Optional[str], str]: (صحيح/خطأ, كلمة منظفة, رسالة)
        """
        try:
            keyword = keyword.strip()
            
            if len(keyword) < 1:
                return False, None, "❌ الكلمة المفتاحية لا يمكن أن تكون فارغة"
            
            if len(keyword) > 100:
                return False, None, "❌ الكلمة المفتاحية يجب أن تكون أقل من 100 حرف"
            
            return True, keyword, "✅ الكلمة المفتاحية صحيحة"
            
        except Exception as e:
            logger.error(f"خطأ في التحقق من الكلمة المفتاحية: {e}")
            return False, None, "❌ خطأ في التحقق من الكلمة المفتاحية"
    
    @staticmethod
    def validate_time_format(time_str: str) -> Tuple[bool, Optional[str], str]:
        """
        التحقق من صحة تنسيق الوقت
        
        Args:
            time_str: الوقت بصيغة HH:MM
            
        Returns:
            Tuple[bool, Optional[str], str]: (صحيح/خطأ, وقت منسق, رسالة)
        """
        try:
            time_str = time_str.strip()
            
            if not InputValidator.PATTERNS['time_format'].match(time_str):
                return False, None, "❌ تنسيق الوقت غير صحيح. يجب أن يكون بالصيغة HH:MM (مثال: 14:30)"
            
            # التحقق من صحة الوقت
            try:
                datetime.strptime(time_str, '%H:%M')
            except ValueError:
                return False, None, "❌ الوقت غير صحيح"
            
            return True, time_str, "✅ تنسيق الوقت صحيح"
            
        except Exception as e:
            logger.error(f"خطأ في التحقق من تنسيق الوقت: {e}")
            return False, None, "❌ خطأ في التحقق من تنسيق الوقت"
    
    @staticmethod
    def validate_delay_seconds(delay_str: str) -> Tuple[bool, Optional[int], str]:
        """
        التحقق من صحة تأخير بالثواني
        
        Args:
            delay_str: التأخير بالثواني كنص
            
        Returns:
            Tuple[bool, Optional[int], str]: (صحيح/خطأ, تأخير, رسالة)
        """
        try:
            delay = int(delay_str.strip())
            
            min_delay, max_delay = InputValidator.RANGES['delay_seconds']
            if not (min_delay <= delay <= max_delay):
                return False, None, f"❌ التأخير يجب أن يكون بين {min_delay} و {max_delay} ثانية"
            
            return True, delay, "✅ التأخير صحيح"
            
        except ValueError:
            return False, None, "❌ التأخير يجب أن يكون رقماً صحيحاً"
        except Exception as e:
            logger.error(f"خطأ في التحقق من التأخير: {e}")
            return False, None, "❌ خطأ في التحقق من التأخير"
    
    @staticmethod
    async def validate_api_credentials_with_telegram(api_id: int, api_hash: str) -> Tuple[bool, str]:
        """
        التحقق من صحة بيانات API مع تلغرام
        
        Args:
            api_id: API ID
            api_hash: API Hash
            
        Returns:
            Tuple[bool, str]: (صحيح/خطأ, رسالة)
        """
        try:
            # إنشاء عميل مؤقت للاختبار
            client = TelegramClient('test_session', api_id, api_hash)
            
            # محاولة الاتصال
            await client.connect()
            
            # التحقق من صحة البيانات
            if await client.is_user_authorized():
                await client.disconnect()
                return True, "✅ بيانات API صحيحة ومتصلة"
            else:
                await client.disconnect()
                return True, "✅ بيانات API صحيحة (غير متصل)"
                
        except ApiIdInvalidError:
            return False, "❌ API ID غير صحيح"
        except Exception as e:
            logger.error(f"خطأ في التحقق من بيانات API: {e}")
            return False, f"❌ خطأ في التحقق من بيانات API: {str(e)}"
    
    @staticmethod
    def validate_setting_value(setting_key: str, value: str) -> Tuple[bool, Any, str]:
        """
        التحقق من صحة قيمة الإعداد
        
        Args:
            setting_key: مفتاح الإعداد
            value: القيمة
            
        Returns:
            Tuple[bool, Any, str]: (صحيح/خطأ, قيمة محولة, رسالة)
        """
        try:
            # إعدادات رقمية
            if setting_key in ['max_messages_per_hour', 'delay_between_messages', 'max_file_size_mb']:
                try:
                    num_value = int(value.strip())
                    if num_value < 0:
                        return False, None, "❌ القيمة يجب أن تكون رقماً موجباً"
                    return True, num_value, "✅ القيمة صحيحة"
                except ValueError:
                    return False, None, "❌ القيمة يجب أن تكون رقماً صحيحاً"
            
            # إعدادات نصية
            elif setting_key in ['bot_name', 'welcome_message']:
                value = value.strip()
                if len(value) < 1:
                    return False, None, "❌ القيمة لا يمكن أن تكون فارغة"
                if len(value) > 500:
                    return False, None, "❌ القيمة طويلة جداً (أقصى حد 500 حرف)"
                return True, value, "✅ القيمة صحيحة"
            
            # إعدادات منطقية
            elif setting_key in ['auto_delete_messages', 'send_notifications', 'log_activities']:
                value_lower = value.strip().lower()
                if value_lower in ['true', '1', 'yes', 'نعم', 'صحيح']:
                    return True, True, "✅ تم تفعيل الإعداد"
                elif value_lower in ['false', '0', 'no', 'لا', 'خطأ']:
                    return True, False, "✅ تم إلغاء تفعيل الإعداد"
                else:
                    return False, None, "❌ القيمة يجب أن تكون true أو false"
            
            else:
                return False, None, "❌ إعداد غير معروف"
                
        except Exception as e:
            logger.error(f"خطأ في التحقق من قيمة الإعداد: {e}")
            return False, None, "❌ خطأ في التحقق من قيمة الإعداد"
    
    @staticmethod
    def sanitize_input(text: str, max_length: int = 1000) -> str:
        """
        تنظيف النص من الأحرف الضارة
        
        Args:
            text: النص المراد تنظيفه
            max_length: الحد الأقصى للطول
            
        Returns:
            str: النص المنظف
        """
        try:
            # إزالة الأحرف الضارة
            text = re.sub(r'[<>"\']', '', text)
            
            # تحديد الطول
            if len(text) > max_length:
                text = text[:max_length]
            
            return text.strip()
            
        except Exception as e:
            logger.error(f"خطأ في تنظيف النص: {e}")
            return ""
