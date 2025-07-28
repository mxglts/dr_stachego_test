#!/usr/bin/env python3
"""
Скрипт для запуска интегрированного приложения
Объединяет математическую визуализацию с системой агентов
"""

import webbrowser
import time
import subprocess
import sys
import os

def main():
    print("🚀 Запуск интегрированной системы...")
    print("📊 Математическая визуализация + Система агентов")
    
    # Проверяем наличие зависимостей
    required_packages = [
        'flask',
        'langchain',
        'langchain-community', 
        'langchain-core',
        'langgraph',
        'llama-index',
        'llama-index-llms-together',
        'together',
        'streamlit',
        'graphviz',
        'wikipedia',
        'python-dotenv'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package} установлен")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package} не установлен")
    
    if missing_packages:
        print(f"\n📦 Устанавливаем недостающие пакеты: {', '.join(missing_packages)}")
        for package in missing_packages:
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                print(f"✅ {package} установлен")
            except subprocess.CalledProcessError:
                print(f"❌ Ошибка установки {package}")
                return
    
    # Проверяем наличие файла .env
    if not os.path.exists('.env'):
        print("\n⚠️  Файл .env не найден!")
        print("📝 Создайте файл .env с вашим API ключом Together AI:")
        print("TOGETHER_API_KEY=ваш_ключ_здесь")
        print("\n💡 Получите ключ на https://together.ai")
        
        # Создаем пример файла .env
        with open('.env.example', 'w') as f:
            f.write("# Скопируйте этот файл в .env и добавьте ваш API ключ\n")
            f.write("TOGETHER_API_KEY=ваш_ключ_здесь\n")
        
        print("📄 Создан файл .env.example для примера")
    
    # Запускаем интегрированное приложение
    print("\n🌐 Запуск веб-сервера...")
    
    # Импортируем и запускаем приложение
    from integrated_app import app
    
    # Открываем браузер через 3 секунды
    def open_browser():
        time.sleep(3)
        webbrowser.open('http://localhost:5000')
        print("🌍 Браузер открыт: http://localhost:5000")
    
    import threading
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    print("📊 Интегрированное приложение запущено!")
    print("💡 Используйте Ctrl+C для остановки")
    print("\n🎯 Возможности:")
    print("   🧮 Математическая визуализация с интерактивным графом")
    print("   🤖 Система агентов с различными специализациями")
    print("   📊 Объединенный веб-интерфейс")
    
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