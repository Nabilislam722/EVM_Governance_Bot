#!/usr/bin/env python3
"""
Entry point for the Discord Governance Bot.
This script sets up the proper asyncio event loop and starts the bot.
"""

import os
import sys
import asyncio
import platform
from pathlib import Path

# Add the bot directory to the Python path
bot_dir = Path(__file__).parent / "bot"
sys.path.insert(0, str(bot_dir))

def setup_event_loop():
    """
    Set up the event loop policy for different platforms and Python versions.
    This fixes compatibility issues with Python 3.9+ and Discord.py.
    """
    if platform.system() == "Windows":
        # On Windows, use ProactorEventLoop for better compatibility
        if hasattr(asyncio, 'WindowsProactorEventLoopPolicy'):
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    else:
        # On Unix-like systems, ensure we have a proper event loop policy
        if hasattr(asyncio, 'DefaultEventLoopPolicy'):
            asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())

def main():
    """Main entry point for the bot."""
    # Set up the event loop policy
    setup_event_loop()
    
    # Change to the bot directory
    os.chdir(bot_dir)
    
    # Import and run the bot main function
    try:
        from main import main as bot_main
        asyncio.run(bot_main())
    except KeyboardInterrupt:
        print("\nBot stopped by user.")
    except Exception as e:
        print(f"Error starting bot: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
