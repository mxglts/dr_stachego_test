#!/usr/bin/env python3
"""
Тест системы агентов
"""

import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

def test_agents():
    print("🧪 Тестирование системы агентов...")
    
    # Проверяем API ключ
    api_key = os.getenv("TOGETHER_API_KEY")
    if api_key:
        print(f"✅ API ключ найден: {api_key[:10]}...")
    else:
        print("❌ API ключ не найден!")
        return False
    
    try:
        # Импортируем систему агентов
        from agents import run_agent_system, create_agent_graph
        
        print("✅ Модули агентов импортированы успешно")
        
        # Тестируем простой запрос
        print("\n🔍 Тестируем запрос: 'Сколько сейчас времени?'")
        result = run_agent_system("Сколько сейчас времени?")
        
        print(f"✅ Результат: {result.get('result', 'Нет результата')}")
        print(f"✅ Использованный агент: {result.get('next_agent', 'Неизвестно')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

if __name__ == "__main__":
    success = test_agents()
    if success:
        print("\n🎉 Система агентов работает корректно!")
    else:
        print("\n💥 Есть проблемы с системой агентов") 