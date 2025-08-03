#!/usr/bin/env python3
"""
Скрипт для настройки виртуального окружения с Python 3.11.4
"""

import os
import sys
import subprocess
import platform

def check_python_version():
    """Проверяет версию Python"""
    version = sys.version_info
    print(f"Текущая версия Python: {version.major}.{version.minor}.{version.micro}")
    
    if version.major == 3 and version.minor == 11:
        print("✅ Используется Python 3.11.x")
        return True
    else:
        print("⚠️  Рекомендуется использовать Python 3.11.x")
        return False

def create_venv():
    """Создает виртуальное окружение"""
    venv_name = "venv"
    
    if os.path.exists(venv_name):
        print(f"📁 Виртуальное окружение {venv_name} уже существует")
        return venv_name
    
    print(f"🔧 Создание виртуального окружения {venv_name}...")
    
    try:
        subprocess.check_call([sys.executable, "-m", "venv", venv_name])
        print(f"✅ Виртуальное окружение {venv_name} создано")
        return venv_name
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка создания виртуального окружения: {e}")
        return None

def get_activate_script(venv_name):
    """Возвращает путь к скрипту активации"""
    if platform.system() == "Windows":
        return os.path.join(venv_name, "Scripts", "activate.bat")
    else:
        return os.path.join(venv_name, "bin", "activate")

def install_requirements(venv_name):
    """Устанавливает зависимости в виртуальное окружение"""
    print("📦 Установка зависимостей...")
    
    # Определяем путь к pip в виртуальном окружении
    if platform.system() == "Windows":
        pip_path = os.path.join(venv_name, "Scripts", "pip.exe")
    else:
        pip_path = os.path.join(venv_name, "bin", "pip")
    
    try:
        # Обновляем pip
        subprocess.check_call([pip_path, "install", "--upgrade", "pip"])
        print("✅ pip обновлен")
        
        # Устанавливаем зависимости
        subprocess.check_call([pip_path, "install", "-r", "requirements.txt"])
        print("✅ Зависимости установлены")
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка установки зависимостей: {e}")
        return False

def create_env_file():
    """Создает файл .env если его нет"""
    if os.path.exists(".env"):
        print("✅ Файл .env уже существует")
        return
    
    print("📝 Создание файла .env...")
    
    env_content = """# API ключ для Together AI
# Получите ключ на https://together.ai
TOGETHER_API_KEY=ваш_ключ_здесь

# Настройки приложения
FLASK_ENV=development
FLASK_DEBUG=True
"""
    
    with open(".env", "w", encoding="utf-8") as f:
        f.write(env_content)
    
    print("✅ Файл .env создан")
    print("⚠️  Не забудьте добавить ваш API ключ в файл .env")

def main():
    """Основная функция"""
    print("🚀 Настройка проекта ODS...")
    print("=" * 50)
    
    # Проверяем версию Python
    check_python_version()
    print()
    
    # Создаем виртуальное окружение
    venv_name = create_venv()
    if not venv_name:
        print("❌ Не удалось создать виртуальное окружение")
        return
    
    print()
    
    # Устанавливаем зависимости
    if not install_requirements(venv_name):
        print("❌ Не удалось установить зависимости")
        return
    
    print()
    
    # Создаем файл .env
    create_env_file()
    
    print()
    print("🎉 Настройка завершена!")
    print("=" * 50)
    print("📋 Следующие шаги:")
    print("1. Активируйте виртуальное окружение:")
    
    if platform.system() == "Windows":
        print(f"   {venv_name}\\Scripts\\activate")
    else:
        print(f"   source {venv_name}/bin/activate")
    
    print("2. Добавьте ваш API ключ в файл .env")
    print("3. Запустите приложение:")
    print("   python run_integrated.py")
    print()
    print("💡 Для получения API ключа посетите: https://together.ai")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Настройка прервана")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        sys.exit(1) 