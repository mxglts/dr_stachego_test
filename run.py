#!/usr/bin/env python3
"""
Скрипт для запуска веб-приложения математического процессора
"""

import webbrowser
import time
import subprocess
import sys
import os

def main():
    print("🚀 Запуск математического процессора...")
    
    # Проверяем наличие Flask
    try:
        import flask
        print("✅ Flask установлен")
    except ImportError:
        print("❌ Flask не установлен. Устанавливаем...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "Flask==2.3.3"])
        print("✅ Flask установлен")
    
    # Запускаем Flask приложение
    print("🌐 Запуск веб-сервера...")
    
    # Импортируем и запускаем приложение
    from app import app
    
    # Открываем браузер через 2 секунды
    def open_browser():
        time.sleep(2)
        webbrowser.open('http://localhost:5000')
        print("🌍 Браузер открыт: http://localhost:5000")
    
    import threading
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    print("📊 Приложение запущено!")
    print("💡 Используйте Ctrl+C для остановки")
    
    # Запускаем Flask
    app.run(debug=False, host='0.0.0.0', port=5000)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Приложение остановлено")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        sys.exit(1) 