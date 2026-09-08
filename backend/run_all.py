# -*- coding: utf-8 -*-
"""
Script untuk menjalankan Flask App dan Telegram Bot bersamaan
"""
import subprocess
import sys
import time
import os
from threading import Thread

def run_flask():
    """Run Flask application"""
    print("🌐 Starting Flask App on http://localhost:5000...")
    subprocess.run([sys.executable, "app.py"])

def run_telegram_bot():
    """Run Telegram Bot"""
    print("🤖 Starting Telegram Bot...")
    time.sleep(2)  # Wait a bit for Flask to start
    subprocess.run([sys.executable, "bot_telegram.py"])

def main():
    print("=" * 60)
    print("🚀 MURENA - Starting All Services")
    print("=" * 60)
    print()
    
    # Start Flask in a thread
    flask_thread = Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # Run Telegram bot in main thread (so Ctrl+C works)
    try:
        run_telegram_bot()
    except KeyboardInterrupt:
        print("\n\n⏹️  Stopping all services...")
        print("✅ Services stopped. Goodbye!")

if __name__ == '__main__':
    main()
