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

# Global flag for shutdown
shutdown_requested = False

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    global shutdown_requested
    print(f"\n🛑 Received signal {signum}, shutting down...")
    shutdown_requested = True

async def run_bot():
    """Run the bot with proper signal handling"""
    global shutdown_requested
    
    from bot import initialize_bot, start_bot, stop_bot
    from bot import is_running
    
    try:
        # Initialize bot
        await initialize_bot()
        
        # Start bot
        await start_bot()
        
        # Keep running until shutdown requested
        while not shutdown_requested:
            await asyncio.sleep(1)
        
        print("\n🛑 Shutdown requested, stopping bot...")
        
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        # Stop bot
        await stop_bot()

if __name__ == "__main__":
    print("🚀 Starting Telegram Forwarder Bot...")
    print("=" * 50)
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        asyncio.run(run_bot())
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
