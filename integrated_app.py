from flask import Flask, render_template, jsonify, request
import random
import time
import threading
import math
from typing import Literal, Dict, List, Tuple, Any
import json
import os
from datetime import datetime

# Импортируем систему агентов
try:
    from agents import run_agent_system, create_agent_graph, clear_active_nodes, add_active_node, add_active_connection
except ImportError as e:
    print(f"Ошибка импорта системы агентов: {e}")
    print("Убедитесь, что файл agents.py создан и все зависимости установлены")
    # Создаем заглушки для случая ошибки импорта
    def run_agent_system(user_input: str):
        return {
            'error': 'Система агентов недоступна',
            'messages': [],
            'result': 'Система агентов не загружена. Проверьте файл agents.py и зависимости.',
            'next_agent': 'general_agent'
        }
    
    def create_agent_graph():
        return {
            'nodes': {},
            'connections': []
        }

app = Flask(__name__)

# Отключаем логи Flask для уменьшения вывода в терминал
import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

class AgentSystem:
    def __init__(self):
        self.conversation_history = []
        self.agent_logs = []
        self.agent_graph = {
            'activeNodes': [],
            'activeConnections': []
        }
        self.is_visualization_running = False
        self.current_query_id = None
        
    def process_query(self, user_input: str) -> Dict[str, Any]:
        # Очищаем логи агентов в начале нового запроса
        self.agent_logs = []
        
        # Генерируем новый ID запроса
        self.current_query_id = datetime.now().isoformat()
        
        # Добавляем начальный лог
        self.add_log(f"Получен запрос: {user_input}")
        
        # Сразу подсвечиваем узел "Запрос"
        self.update_active_nodes(['request'], [])
        
        try:
            # Запускаем систему агентов с промежуточными обновлениями
            result = self.run_agent_system_with_updates(user_input)
            
            # Добавляем финальный лог
            self.add_log("Обработка запроса завершена")
            
            # Добавляем результат в историю
            conversation_entry = {
                'timestamp': datetime.now().isoformat(),
                'user_input': user_input,
                'agent_response': result.get('result', 'Ошибка обработки'),
                'messages': result.get('messages', [])
            }
            
            self.conversation_history.append(conversation_entry)
            
            return {
                'success': True,
                'result': result.get('result', 'Ошибка обработки'),
                'messages': result.get('messages', []),
                'error': result.get('error', None)
            }
            
        except Exception as e:
            error_msg = f"Ошибка при обработке запроса: {str(e)}"
            self.add_log(error_msg, 'error')
            return {
                'success': False,
                'result': error_msg,
                'messages': [],
                'error': str(e)
            }
    
    def run_agent_system_with_updates(self, user_input: str) -> Dict[str, Any]:
        """Запускает систему агентов с промежуточными обновлениями состояния"""
        try:
            # Этап 1: Цензор (сразу после запроса)
            self.add_log("Запуск цензора...")
            time.sleep(0.3)  # Минимальное время подсветки запроса
            
            # Этап 2: Цензор
            self.add_log("Проверка цензора...")
            self.update_active_nodes(['request', 'censor'], ['request_to_censor'])
            time.sleep(0.3)
            
            # Этап 3: Оркестратор
            self.add_log("Запуск оркестратора...")
            self.update_active_nodes(['request', 'censor', 'orchestrator'], 
                                   ['request_to_censor', 'censor_to_orchestrator'])
            time.sleep(0.3)
            
            # Запускаем основную систему агентов
            result = run_agent_system(user_input)
            
            # Синхронизируем логи из agents.py
            from agents import get_agent_logs
            agent_logs = get_agent_logs()
            for log_entry in agent_logs:
                # Проверяем, нет ли уже такого лога
                if not any(existing['message'] == log_entry['message'] and 
                          existing['timestamp'] == log_entry['timestamp'] 
                          for existing in self.agent_logs):
                    self.agent_logs.append({
                        'timestamp': log_entry['timestamp'],
                        'level': log_entry['level'],
                        'message': log_entry['message']
                    })
            
            # Обновляем граф с финальными активными узлами
            if 'active_nodes' in result and 'active_connections' in result:
                self.agent_graph['activeNodes'] = result['active_nodes']
                self.agent_graph['activeConnections'] = result['active_connections']
            
            return result
            
        except Exception as e:
            self.add_log(f"Ошибка в системе агентов: {str(e)}", 'error')
            raise e
    
    def update_active_nodes(self, nodes: List[str], connections: List[str]):
        """Обновляет активные узлы и связи"""
        self.agent_graph['activeNodes'] = nodes
        self.agent_graph['activeConnections'] = connections
    
    def add_log(self, message: str, level: str = 'info'):
        """Добавляет запись в логи агентов"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'message': message
        }
        self.agent_logs.append(log_entry)
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Возвращает историю разговоров"""
        return self.conversation_history
    
    def get_agent_logs(self) -> List[Dict[str, Any]]:
        """Возвращает логи агентов"""
        return self.agent_logs
    
    def start_visualization(self):
        """Запускает визуализацию"""
        self.is_visualization_running = True
        return {'status': 'started'}
    
    def stop_visualization(self):
        """Останавливает визуализацию"""
        self.is_visualization_running = False
        return {'status': 'stopped'}

# Создаем экземпляры систем
agent_system = AgentSystem()

@app.route('/')
def index():
    return render_template('integrated_index.html')

@app.route('/api/start')
def start_processing():
    """Запускает визуализацию и сбрасывает состояние"""
    try:
        # Сначала сбрасываем состояние
        agent_system.agent_graph['activeNodes'] = []
        agent_system.agent_graph['activeConnections'] = []
        agent_system.agent_logs = []
        agent_system.conversation_history = []
        agent_system.current_query_id = None
        clear_active_nodes()
        
        # Затем запускаем визуализацию
        result = agent_system.start_visualization()
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/stop')
def stop_processing():
    """Останавливает визуализацию"""
    result = agent_system.stop_visualization()
    return jsonify(result)

@app.route('/api/reset', methods=['GET', 'POST'])
def reset_state():
    """Сбрасывает состояние системы агентов"""
    try:
        # Очищаем активные узлы и связи
        agent_system.agent_graph['activeNodes'] = []
        agent_system.agent_graph['activeConnections'] = []
        
        # Очищаем логи агентов
        agent_system.agent_logs = []
        
        # Очищаем историю разговоров
        agent_system.conversation_history = []
        
        # Сбрасываем ID запроса
        agent_system.current_query_id = None
        
        # Очищаем активные узлы в системе агентов
        clear_active_nodes()
        
        return jsonify({'success': True, 'message': 'Состояние системы сброшено'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/state')
def get_state():
    """Возвращает текущее состояние системы"""
    try:
        # Получаем граф агентов
        agent_graph_data = create_agent_graph()
        
        # Добавляем информацию об активных узлах и связях
        agent_graph_data['activeNodes'] = agent_system.agent_graph['activeNodes']
        agent_graph_data['activeConnections'] = agent_system.agent_graph['activeConnections']
        
        return jsonify({
            'success': True,
            'agent_graph': agent_graph_data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/agent/query', methods=['POST'])
def agent_query():
    """Обрабатывает запрос к системе агентов"""
    try:
        data = request.get_json()
        user_input = data.get('query', '')
        
        if not user_input:
            return jsonify({
                'success': False,
                'error': 'Пустой запрос'
            })
        
        result = agent_system.process_query(user_input)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Ошибка обработки запроса: {str(e)}'
        })

@app.route('/api/agent/history')
def get_agent_history():
    """Возвращает историю разговоров с агентами"""
    return jsonify({
        'success': True,
        'history': agent_system.get_conversation_history()
    })

@app.route('/api/agent/logs')
def get_agent_logs():
    """Возвращает логи агентов"""
    return jsonify({
        'success': True,
        'logs': agent_system.get_agent_logs()
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 