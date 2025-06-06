#!/usr/bin/env python3
"""
Telegram Forwarder Bot - Main Runner
"""

import asyncio
import sys
import os
import signal
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from bot import main, shutdown_event

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print(f"\n🛑 Received signal {signum}, shutting down...")
    # Set shutdown event to stop the bot
    if not shutdown_event.is_set():
        shutdown_event.set()

if __name__ == "__main__":
    print("🚀 Starting Telegram Forwarder Bot...")
    print("=" * 50)
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        print("\n✅ Bot shutdown complete")
        sys.exit(0)
