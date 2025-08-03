"""
Граф агентов для визуализации
Структура: Запрос -> Оркестратор -> Агенты -> Функции
"""

def get_connection_points(node1, node2, nodes):
    """Вычисляет точки соединения между двумя узлами"""
    x1, y1 = nodes[node1]['x'], nodes[node1]['y']
    x2, y2 = nodes[node2]['x'], nodes[node2]['y']
    r1, r2 = nodes[node1]['radius'], nodes[node2]['radius']
    
    # Вычисляем направление от центра к центру
    dx = x2 - x1
    dy = y2 - y1
    distance = (dx**2 + dy**2)**0.5
    
    if distance == 0:
        return [x1, y1], [x2, y2]
    
    # Нормализуем вектор
    dx /= distance
    dy /= distance
    
    # Вычисляем точки на границах кругов
    start_x = x1 + dx * r1
    start_y = y1 + dy * r1
    end_x = x2 - dx * r2
    end_y = y2 - dy * r2
    
    return [start_x, start_y], [end_x, end_y]

def create_agent_graph():
    """Создает граф агентов для визуализации"""
    # Определяем позиции узлов (увеличенные расстояния между уровнями и функциями)
    nodes = {
        'request': {'x': 490, 'y': 100, 'radius': 45, 'type': 'input', 'name': 'Запрос пользователя'},
        'censor': {'x': 490, 'y': 220, 'radius': 45, 'type': 'filter', 'name': 'Цензор'},
        'orchestrator': {'x': 490, 'y': 340, 'radius': 45, 'type': 'orchestrator', 'name': 'Оркестратор'},
        
        # Агенты (в ряд, больше расстояние между ними)
        'buyer': {'x': 115, 'y': 480, 'radius': 45, 'type': 'agent', 'name': 'Агент закупок'},
        'logistics': {'x': 365, 'y': 480, 'radius': 45, 'type': 'agent', 'name': 'Агент логистики'},
        'production': {'x': 615, 'y': 480, 'radius': 45, 'type': 'agent', 'name': 'Агент производства'},
        'quality': {'x': 865, 'y': 480, 'radius': 45, 'type': 'agent', 'name': 'Агент качества'},
        
        # Функции агента закупок (увеличены расстояния)
        'fetch_prices': {'x': 50, 'y': 620, 'radius': 45, 'type': 'function', 'name': 'fetch_competitor_prices'},
        'check_stock': {'x': 180, 'y': 620, 'radius': 45, 'type': 'function', 'name': 'check_stock'},
        
        # Функции агента логистики (увеличены расстояния)
        'track_delivery': {'x': 300, 'y': 620, 'radius': 45, 'type': 'function', 'name': 'track_delivery'},
        'get_deliveries': {'x': 430, 'y': 620, 'radius': 45, 'type': 'function', 'name': 'get_upcoming_deliveries'},
        
        # Функции агента производства (увеличены расстояния)
        'get_line_status': {'x': 550, 'y': 620, 'radius': 45, 'type': 'function', 'name': 'get_line_status'},
        'get_production_summary': {'x': 680, 'y': 620, 'radius': 45, 'type': 'function', 'name': 'get_production_summary'},
        
        # Функции агента качества (увеличены расстояния)
        'check_batch_quality': {'x': 800, 'y': 620, 'radius': 45, 'type': 'function', 'name': 'check_batch_quality'},
        'get_failed_batches': {'x': 930, 'y': 620, 'radius': 45, 'type': 'function', 'name': 'get_failed_batches'}
    }
    
    # Определяем соединения
    connections_data = [
        # Основной поток
        ('request', 'censor'),
        ('censor', 'orchestrator'),
        
        # От оркестратора к агентам
        ('orchestrator', 'buyer'),
        ('orchestrator', 'logistics'),
        ('orchestrator', 'production'),
        ('orchestrator', 'quality'),
        
        # От агента закупок к функциям
        ('buyer', 'fetch_prices'),
        ('buyer', 'check_stock'),
        
        # От агента логистики к функциям
        ('logistics', 'track_delivery'),
        ('logistics', 'get_deliveries'),
        
        # От агента производства к функциям
        ('production', 'get_line_status'),
        ('production', 'get_production_summary'),
        
        # От агента качества к функциям
        ('quality', 'check_batch_quality'),
        ('quality', 'get_failed_batches')
    ]
    
    # Вычисляем точки соединения
    connections = {}
    for i, (from_node, to_node) in enumerate(connections_data):
        start_point, end_point = get_connection_points(from_node, to_node, nodes)
        connection_name = f"{from_node}_to_{to_node}"
        connections[connection_name] = {
            'start': start_point,
            'end': end_point,
            'from': from_node,
            'to': to_node
        }
    
    return {
        'nodes': nodes,
        'connections': connections
    }

def get_agent_hierarchy():
    """Возвращает иерархию агентов для отображения"""
    return {
        'Запрос пользователя': {
            'Цензор': {
                'Оркестратор': {
                    'Агент закупок': {
                        'fetch_competitor_prices': 'Получение цен конкурентов',
                        'check_stock': 'Проверка склада'
                    },
                    'Агент логистики': {
                        'track_delivery': 'Отслеживание поставок',
                        'get_upcoming_deliveries': 'Предстоящие поставки'
                    },
                    'Агент производства': {
                        'get_line_status': 'Статус линий',
                        'get_production_summary': 'Общая сводка'
                    },
                    'Агент качества': {
                        'check_batch_quality': 'Проверка партий',
                        'get_failed_batches': 'Неудачные партии'
                    }
                }
            }
        }
    } 