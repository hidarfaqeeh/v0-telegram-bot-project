#!/usr/bin/env python3
"""
سكريبت بدء تشغيل البوت مع فحوصات أولية
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# إضافة المجلد الحالي إلى مسار Python
sys.path.insert(0, str(Path(__file__).parent))

async def pre_start_checks():
    """فحوصات ما قبل التشغيل"""
    print("🔍 تشغيل فحوصات ما قبل البدء...")
    
    # استيراد سكريبت الفحص
    try:
        from scripts.check_setup import main as check_setup
        setup_ok = await check_setup()
        
        if not setup_ok:
            print("❌ فشلت فحوصات الإعداد. لا يمكن تشغيل البوت.")
            return False
        
        print("✅ جميع فحوصات الإعداد نجحت")
        return True
        
    except ImportError as e:
        print(f"❌ خطأ في استيراد سكريبت الفحص: {e}")
        return False
    except Exception as e:
        print(f"❌ خطأ في فحوصات الإعداد: {e}")
        return False

async def start_bot():
    """بدء تشغيل البوت"""
    try:
        print("🚀 بدء تشغيل البوت...")
        
        # استيراد الدالة الرئيسية للبوت
        from bot import main
        await main()
        
    except KeyboardInterrupt:
        print("\n⏹️ تم إيقاف البوت بواسطة المستخدم")
    except Exception as e:
        print(f"❌ خطأ في تشغيل البوت: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """الدالة الرئيسية"""
    # تكوين التسجيل
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    
    print("=" * 50)
    print("🤖 بوت توجيه الرسائل المتقدم")
    print("=" * 50)
    
    # تشغيل فحوصات ما قبل البدء
    if not await pre_start_checks():
        sys.exit(1)
    
    # بدء تشغيل البوت
    await start_bot()

if __name__ == "__main__":
    asyncio.run(main())
