#!/usr/bin/env python3
"""
Тестовый скрипт для проверки работы системы агентов
"""

import requests
import json
import time

def test_agent_system():
    """Тестирует систему агентов"""
    
    # URL базового адреса
    base_url = "http://localhost:5000"
    
    # Тестовые запросы для разных агентов
    test_queries = [
        "Какие цены на Example Product у конкурентов?",
        "Сколько товара с ID 12345 на складе?",
        "Какой статус поставки TRK123456?",
        "Какие предстоящие поставки?",
        "Какой статус линии LINE-A1?",
        "Какая сводка по производству?",
        "Какой результат проверки партии BATCH-2025-04-01?",
        "Какие партии не прошли контроль?"
    ]
    
    print("🧪 Тестирование системы агентов")
    print("=" * 50)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}. Тестируем запрос: {query}")
        
        try:
            # Отправляем запрос
            response = requests.post(
                f"{base_url}/api/agent/query",
                json={"query": query},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Ответ получен: {result.get('result', 'Нет ответа')[:100]}...")
                
                # Получаем состояние графа
                state_response = requests.get(f"{base_url}/api/state")
                if state_response.status_code == 200:
                    state = state_response.json()
                    active_nodes = state.get('activeNodes', [])
                    active_connections = state.get('activeConnections', [])
                    print(f"🎯 Активные узлы: {active_nodes}")
                    print(f"🔗 Активные соединения: {active_connections}")
                
            else:
                print(f"❌ Ошибка: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Ошибка запроса: {e}")
        
        # Пауза между запросами
        time.sleep(2)
    
    print("\n" + "=" * 50)
    print("✅ Тестирование завершено")

if __name__ == "__main__":
    test_agent_system() 