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
from agents import run_agent_system, create_agent_graph

app = Flask(__name__)

class MathProcessor:
    def __init__(self):
        self.running = False
        self.processing_thread = None
        self.current_operation = None
        self.current_numbers = None
        self.current_result = None
        self.operation_status = "idle"  # idle, request, calculation, result
        
    def start_processing(self):
        if not self.running:
            self.running = True
            self.processing_thread = threading.Thread(target=self._run_processing_loop)
            self.processing_thread.daemon = True
            self.processing_thread.start()
            
    def stop_processing(self):
        self.running = False
        
    def _run_processing_loop(self):
        while self.running:
            # Случайный выбор операции
            operation = random.choice(["sum", "product"])
            a = random.randint(1, 100)
            b = random.randint(1, 100)
            
            # Запрос операции
            self.operation_status = "request"
            self.current_operation = operation
            self.current_numbers = (a, b)
            time.sleep(1)
            
            # Вычисление
            self.operation_status = "calculation"
            if operation == "sum":
                result = self.calculate_sum(a, b)
            else:
                result = self.calculate_product(a, b)
            
            # Возврат результата
            self.operation_status = "result"
            self.current_result = result
            time.sleep(1)
            
            # Сброс статуса
            self.operation_status = "idle"
            self.current_operation = None
            self.current_numbers = None
            self.current_result = None
            
            # Случайная задержка между циклами
            delay = random.uniform(1, 5)
            time.sleep(delay)
    
    def calculate_sum(self, a: int, b: int) -> int:
        return a + b
    
    def calculate_product(self, a: int, b: int) -> int:
        return a * b
    
    def get_current_state(self) -> Dict[str, Any]:
        return {
            "status": self.operation_status,
            "operation": self.current_operation,
            "numbers": self.current_numbers,
            "result": self.current_result
        }

# Глобальный экземпляр процессора
math_processor = MathProcessor()

class GraphVisualizer:
    def __init__(self):
        self.node_positions = {
            'request': (200, 300),
            'sum': (400, 200),
            'product': (400, 400)
        }
        self.node_radius = 30
        
    def get_connection_points(self, x: float, y: float, radius: float) -> List[Tuple[float, float]]:
        """Возвращает 8 точек на окружности"""
        points = []
        for i in range(8):
            angle = i * math.pi / 4
            px = x + radius * math.cos(angle)
            py = y + radius * math.sin(angle)
            points.append((px, py))
        return points
    
    def find_optimal_connection(self, start_x: float, start_y: float, end_x: float, end_y: float, 
                              start_radius: float, end_radius: float) -> Tuple[Tuple[float, float], Tuple[float, float]]:
        """Находит оптимальные точки соединения между двумя узлами"""
        start_points = self.get_connection_points(start_x, start_y, start_radius)
        end_points = self.get_connection_points(end_x, end_y, end_radius)
        
        best_start = start_points[0]
        best_end = end_points[0]
        min_distance = float('inf')
        
        for start_point in start_points:
            for end_point in end_points:
                distance = math.sqrt((end_point[0] - start_point[0])**2 + (end_point[1] - start_point[1])**2)
                if distance < min_distance:
                    min_distance = distance
                    best_start = start_point
                    best_end = end_point
        
        return best_start, best_end
    
    def get_graph_data(self) -> Dict[str, Any]:
        """Возвращает данные графа для фронтенда"""
        req_x, req_y = self.node_positions['request']
        sum_x, sum_y = self.node_positions['sum']
        prod_x, prod_y = self.node_positions['product']
        
        # Находим оптимальные соединения
        req_to_sum_start, req_to_sum_end = self.find_optimal_connection(req_x, req_y, sum_x, sum_y, self.node_radius, self.node_radius)
        req_to_prod_start, req_to_prod_end = self.find_optimal_connection(req_x, req_y, prod_x, prod_y, self.node_radius, self.node_radius)
        sum_to_req_start, sum_to_req_end = self.find_optimal_connection(sum_x, sum_y, req_x, req_y, self.node_radius, self.node_radius)
        prod_to_req_start, prod_to_req_end = self.find_optimal_connection(prod_x, prod_y, req_x, req_y, self.node_radius, self.node_radius)
        
        return {
            "nodes": {
                "request": {"x": req_x, "y": req_y, "radius": self.node_radius},
                "sum": {"x": sum_x, "y": sum_y, "radius": self.node_radius},
                "product": {"x": prod_x, "y": prod_y, "radius": self.node_radius}
            },
            "connections": {
                "req_to_sum": {"start": req_to_sum_start, "end": req_to_sum_end},
                "req_to_product": {"start": req_to_prod_start, "end": req_to_prod_end},
                "sum_to_req": {"start": sum_to_req_start, "end": sum_to_req_end},
                "product_to_req": {"start": prod_to_req_start, "end": prod_to_req_end}
            }
        }
    
    def update_node_position(self, node_name: str, x: float, y: float):
        """Обновляет позицию узла"""
        self.node_positions[node_name] = (x, y)

# Глобальный экземпляр визуализатора
graph_visualizer = GraphVisualizer()

# Система агентов
class AgentSystem:
    def __init__(self):
        self.agent_graph = create_agent_graph()
        self.conversation_history = []
        
    def process_query(self, user_input: str) -> Dict[str, Any]:
        """Обрабатывает запрос пользователя через систему агентов"""
        try:
            result = run_agent_system(user_input)
            self.conversation_history.append({
                'timestamp': datetime.now().isoformat(),
                'input': user_input,
                'result': result
            })
            return result
        except Exception as e:
            return {
                'error': str(e),
                'messages': [],
                'result': f'Ошибка обработки запроса: {e}',
                'next_agent': 'general_agent'
            }
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Возвращает историю разговоров"""
        return self.conversation_history

# Глобальный экземпляр системы агентов
agent_system = AgentSystem()

@app.route('/')
def index():
    return render_template('integrated_index.html')

@app.route('/api/start')
def start_processing():
    math_processor.start_processing()
    return jsonify({"status": "started"})

@app.route('/api/stop')
def stop_processing():
    math_processor.stop_processing()
    return jsonify({"status": "stopped"})

@app.route('/api/state')
def get_state():
    processor_state = math_processor.get_current_state()
    graph_data = graph_visualizer.get_graph_data()
    
    return jsonify({
        "processor": processor_state,
        "graph": graph_data
    })

@app.route('/api/update_node', methods=['POST'])
def update_node():
    data = request.get_json()
    node_name = data.get('node')
    x = data.get('x')
    y = data.get('y')
    
    if node_name and x is not None and y is not None:
        graph_visualizer.update_node_position(node_name, x, y)
        return jsonify({"status": "updated"})
    
    return jsonify({"status": "error", "message": "Invalid data"})

@app.route('/api/agent/query', methods=['POST'])
def agent_query():
    """Обрабатывает запрос к системе агентов"""
    data = request.get_json()
    user_input = data.get('query', '')
    
    if not user_input:
        return jsonify({"error": "Query is required"})
    
    result = agent_system.process_query(user_input)
    return jsonify(result)

@app.route('/api/agent/history')
def get_agent_history():
    """Возвращает историю разговоров с агентами"""
    history = agent_system.get_conversation_history()
    return jsonify(history)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 