#!/usr/bin/env python3
"""
Telegram Forwarder Bot - Main Runner
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from bot import main
from bot import TelegramForwarderBot

if __name__ == "__main__":
    print("🚀 Starting Telegram Forwarder Bot...")
    print("=" * 50)
    
    bot = None
    try:
        bot = TelegramForwarderBot()
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if bot:
            try:
                # تنظيف الموارد
                pass
            except:
                pass
        sys.exit(0)
