#!/usr/bin/env python3
"""
سكريبت للتحقق من إعداد البوت والتبعيات
"""

import os
import sys
import asyncio
import importlib.util
from pathlib import Path

def check_python_version():
    """التحقق من إصدار Python"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ مطلوب")
        return False
    print(f"✅ Python {sys.version}")
    return True

def check_required_packages():
    """التحقق من الحزم المطلوبة"""
    required_packages = [
        'telegram',
        'asyncpg',
        'dotenv',
        'telethon',
        'PIL',
        'matplotlib',
        'psutil',
        'aiofiles',
        'aiohttp'
    ]
    
    missing_packages = []
    for package in required_packages:
        if importlib.util.find_spec(package) is None:
            missing_packages.append(package)
        else:
            print(f"✅ {package}")
    
    if missing_packages:
        print(f"❌ الحزم المفقودة: {', '.join(missing_packages)}")
        print("قم بتشغيل: pip install -r requirements.txt")
        return False
    
    return True

def check_env_file():
    """التحقق من ملف .env"""
    env_path = Path('.env')
    if not env_path.exists():
        print("❌ ملف .env غير موجود")
        print("قم بإنشاء ملف .env وإضافة المتغيرات المطلوبة")
        return False
    
    print("✅ ملف .env موجود")
    
    # التحقق من المتغيرات المطلوبة
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = ['BOT_TOKEN', 'DATABASE_URL', 'ADMIN_USER_ID']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
        else:
            print(f"✅ {var}")
    
    if missing_vars:
        print(f"❌ المتغيرات المفقودة في .env: {', '.join(missing_vars)}")
        return False
    
    return True

def check_file_structure():
    """التحقق من بنية الملفات"""
    required_files = [
        'bot.py',
        'config.py',
        'handlers/__init__.py',
        'handlers/main_handlers.py',
        'handlers/task_handlers.py',
        'handlers/userbot_handlers.py',
        'database/__init__.py',
        'database/models.py',
        'utils/__init__.py',
        'utils/error_handler.py'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
        else:
            print(f"✅ {file_path}")
    
    if missing_files:
        print(f"❌ الملفات المفقودة: {', '.join(missing_files)}")
        return False
    
    return True

async def check_database_connection():
    """التحقق من الاتصال بقاعدة البيانات"""
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        import asyncpg
        database_url = os.getenv('DATABASE_URL')
        
        if not database_url:
            print("❌ DATABASE_URL غير محدد")
            return False
        
        conn = await asyncpg.connect(database_url)
        await conn.fetchval('SELECT 1')
        await conn.close()
        
        print("✅ الاتصال بقاعدة البيانات")
        return True
        
    except Exception as e:
        print(f"❌ خطأ في الاتصال بقاعدة البيانات: {e}")
        return False

async def check_bot_token():
    """التحقق من صحة رمز البوت"""
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        from telegram import Bot
        bot_token = os.getenv('BOT_TOKEN')
        
        if not bot_token:
            print("❌ BOT_TOKEN غير محدد")
            return False
        
        bot = Bot(token=bot_token)
        bot_info = await bot.get_me()
        
        print(f"✅ البوت: @{bot_info.username}")
        return True
        
    except Exception as e:
        print(f"❌ خطأ في رمز البوت: {e}")
        return False

async def main():
    """الدالة الرئيسية للفحص"""
    print("🔍 فحص إعداد البوت...\n")
    
    checks = [
        ("إصدار Python", check_python_version()),
        ("الحزم المطلوبة", check_required_packages()),
        ("ملف .env", check_env_file()),
        ("بنية الملفات", check_file_structure()),
        ("الاتصال بقاعدة البيانات", await check_database_connection()),
        ("رمز البوت", await check_bot_token())
    ]
    
    passed = 0
    total = len(checks)
    
    for name, result in checks:
        if result:
            passed += 1
        print()
    
    print(f"\n📊 النتيجة: {passed}/{total} فحوصات نجحت")
    
    if passed == total:
        print("🎉 البوت جاهز للتشغيل!")
        return True
    else:
        print("❌ يرجى إصلاح المشاكل المذكورة أعلاه")
        return False

if __name__ == "__main__":
    asyncio.run(main())
