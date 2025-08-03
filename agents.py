import os, json, random
from llama_index.llms.openai_like import OpenAILike
from llama_index.core.tools import FunctionTool
from llama_index.core.agent import ReActAgent
from llama_index.core.llms import ChatMessage
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("TOGETHER_API_KEY")

# Модель
MODEL_NAME = 'meta-llama/Llama-3.3-70B-Instruct-Turbo'

llm = OpenAILike(
    model=MODEL_NAME,
    api_base="https://api.together.xyz/v1",
    api_key=API_KEY,
    is_chat_model=True,
    is_function_calling_model=True,
    temperature=0.3
)

SYSTEM_PROMPT = '''Вы — специализированный агент производственной системы. Ваша основная задача — обрабатывать запросы, связанные с определённой областью деятельности завода, и использовать доступные инструменты только тогда, когда это необходимо для выполнения конкретной операционной задачи.

Вы должны:
1. Анализировать входящий запрос на предмет его отношения к вашей предметной области: {DOMAIN_DESCRIPTION}.
2. Если запрос попадает в вашу зону ответственности и требует получения данных или выполнения действия — использовать соответствующий инструмент.
3. Если запрос не связан с вашей областью, является общим, теоретическим, бытовым или не требует вызова инструмента — отвечать кратко и нейтрально, **не пытаясь использовать инструменты**.
4. Никогда не выдумывать факты, не генерировать предположения о данных, которые можно получить через инструмент, если он ещё не был вызван.
5. Сохранять формально-деловой тон, избегать избыточных пояснений и отклонений от темы.

{ADDITIONAL_INSTRUCTIONS}

Ваша цель — обеспечить точность, эффективность и уместность ответов в рамках вашей функции на производстве. Все операционные данные доступны только через инструменты. Не отвечайте за другие отделы. Не комбинируйте информацию из других доменов.'''.strip()

# === Создаём папку data, если её нет ===
DATA_DIR = 'data'
os.makedirs(DATA_DIR, exist_ok=True)

# === Файлы с тестовыми данными (в папке data/) ===
LOGISTICS_FILE = os.path.join(DATA_DIR, 'logistics.json')
PRODUCTION_FILE = os.path.join(DATA_DIR, 'production.json')
QUALITY_FILE = os.path.join(DATA_DIR, 'quality.json')
PRICES_FILE = os.path.join(DATA_DIR, 'prices.json')
STOCK_FILE = os.path.join(DATA_DIR, 'stock.json')

# === Генерация тестовых данных ===
def generate_mock_data():
    # Закупщик
    with open(PRICES_FILE, 'w', encoding='utf-8') as f:
        json.dump([
            {'product':'Example Product','firm':'Competitor A','price':random.randint(100,200)},
            {'product':'Example Product','firm':'Competitor B','price':random.randint(100,200)}
        ], f, ensure_ascii=False, indent=2)
    with open(STOCK_FILE, 'w', encoding='utf-8') as f:
        json.dump([{'product_id':'12345','quantity':random.randint(0,50)}], f, ensure_ascii=False, indent=2)

    # Логистика: поставки сырья
    with open(LOGISTICS_FILE, 'w', encoding='utf-8') as f:
        json.dump([
            {
                'supplier': 'RawMaterial Inc.',
                'product': 'Пластик ПЭ-300',
                'delivery_date': '2025-04-10',
                'status': 'в пути',
                'tracking_id': 'TRK123456'
            },
            {
                'supplier': 'SteelGlobal',
                'product': 'Сталь Ст3',
                'delivery_date': '2025-04-05',
                'status': 'доставлено',
                'tracking_id': 'TRK789012'
            }
        ], f, ensure_ascii=False, indent=2)

    # Производство: загрузка линий
    with open(PRODUCTION_FILE, 'w', encoding='utf-8') as f:
        json.dump([
            {
                'line_id': 'LINE-A1',
                'product': 'Тостер Модель X',
                'status': 'работает',
                'output_per_hour': 120,
                'defect_rate': 1.2
            },
            {
                'line_id': 'LINE-B2',
                'product': 'Чайник Эко 2000',
                'status': 'в ремонте',
                'output_per_hour': 0,
                'defect_rate': 0.0
            }
        ], f, ensure_ascii=False, indent=2)

    # Контроль качества: инциденты и проверки
    with open(QUALITY_FILE, 'w', encoding='utf-8') as f:
        json.dump([
            {
                'batch_id': 'BATCH-2025-04-01',
                'product': 'Фен TurboDry',
                'inspection_date': '2025-04-01',
                'result': 'прошёл',
                'defects_found': 2,
                'certified': True
            },
            {
                'batch_id': 'BATCH-2025-04-02',
                'product': 'Миксер PowerMix',
                'inspection_date': '2025-04-02',
                'result': 'не прошёл',
                'defects_found': 15,
                'certified': False,
                'reason': 'нарушение изоляции'
            }
        ], f, ensure_ascii=False, indent=2)

# Генерируем тестовые данные
generate_mock_data()

# === АГЕНТ ЗАКУПЩИК ===
# Инструменты
def fetch_competitor_prices(product_name: str) -> str:
    """Получает цены конкурентов для указанного продукта"""
    add_active_node('fetch_prices')
    add_active_connection('buyer_to_fetch_prices')
    add_agent_log(f"Вызвана функция fetch_competitor_prices для продукта: {product_name}")
    data = json.load(open(PRICES_FILE, 'r', encoding='utf-8'))
    results = [f"{e['firm']}: ${e['price']}" for e in data if e['product'] == product_name]
    return "\n".join(results) if results else "Не найдено данных о ценах"

def check_stock(product_id: str) -> str:
    """Проверяет количество товара на складе по ID"""
    add_active_node('check_stock')
    add_active_connection('buyer_to_check_stock')
    add_agent_log(f"Вызвана функция check_stock для ID: {product_id}")
    data = json.load(open(STOCK_FILE, 'r', encoding='utf-8'))
    for e in data:
        if e['product_id'] == product_id:
            return f"На складе: {e['quantity']} шт."
    return "Товар не найден"

# Создание инструментов
tool_prices = FunctionTool.from_defaults(
    name="fetch_competitor_prices",
    description="Получает информацию о ценах конкурентов для указанного продукта",
    fn=fetch_competitor_prices
)

tool_stock = FunctionTool.from_defaults(
    name="check_stock",
    description="Проверяет количество товара на складе по идентификатору",
    fn=check_stock
)

DOMAIN_DESCRIPTION = "мониторинг рыночных цен конкурентов и управление складскими запасами"
ADDITIONAL_INSTRUCTIONS = "Для запросов о ценах используйте fetch_competitor_prices с названием продукта. Для проверки наличия применяйте check_stock с идентификатором товара. На все прочие запросы отвечайте строго: 'Извините, данная функция не входит в список моих обязанностей. Я могу выполнять только: 1) проверку цен конкурентов по названию продукта; 2) проверку наличия товара на складе по идентификатору.' Запрещено обрабатывать запросы вне указанных функций или генерировать информацию без данных инструментов."

agent_buyer = ReActAgent.from_tools(
    [tool_prices, tool_stock],
    llm=llm,
    verbose=True,
    system_prompt=SYSTEM_PROMPT.format(
        DOMAIN_DESCRIPTION=DOMAIN_DESCRIPTION,
        ADDITIONAL_INSTRUCTIONS=ADDITIONAL_INSTRUCTIONS,
    )
)

# === АГЕНТ ЛОГИСТИКА ===
# Инструменты для Логистики
def track_delivery(tracking_id: str) -> str:
    """Отслеживает статус поставки по трек-номеру"""
    add_active_node('track_delivery')
    add_active_connection('logistics_to_track_delivery')
    add_agent_log(f"Вызвана функция track_delivery для трек-номера: {tracking_id}")
    data = json.load(open(LOGISTICS_FILE, 'r', encoding='utf-8'))
    for item in data:
        if item['tracking_id'] == tracking_id:
            return (f"Поставка {tracking_id}:\n"
                    f"Поставщик: {item['supplier']}\n"
                    f"Товар: {item['product']}\n"
                    f"Дата доставки: {item['delivery_date']}\n"
                    f"Статус: {item['status']}")
    return "Поставка не найдена"

def get_upcoming_deliveries() -> str:
    """Возвращает список предстоящих поставок"""
    add_active_node('get_deliveries')
    add_active_connection('logistics_to_get_deliveries')
    add_agent_log("Вызвана функция get_upcoming_deliveries")
    data = json.load(open(LOGISTICS_FILE, 'r', encoding='utf-8'))
    upcoming = [d for d in data if d['status'] == 'в пути']
    if not upcoming:
        return "Нет активных поставок."
    result = "Предстоящие поставки:\n"
    for d in upcoming:
        result += f"- {d['product']} от {d['supplier']}, до {d['delivery_date']} (ID: {d['tracking_id']})\n"
    return result

# Логистика
tool_track_delivery = FunctionTool.from_defaults(
    fn=track_delivery,
    name="track_delivery",
    description="Отслеживает статус поставки по трек-номеру"
)

tool_upcoming_deliveries = FunctionTool.from_defaults(
    fn=get_upcoming_deliveries,
    name="get_upcoming_deliveries",
    description="Возвращает список предстоящих поставок сырья"
)

DOMAIN_DESCRIPTION = "управление поставками сырья и материалов: отслеживание статуса доставок, сроков прибытия, данных о поставщиках и логистических операциях"
ADDITIONAL_INSTRUCTIONS = "При запросах о статусе поставки используйте данные о трек-номерах и сроках. Если поставка задерживается, сообщайте только факт из данных. Не предлагайте альтернативы и не прогнозируйте последствия."

# Агент-логист
agent_logistics = ReActAgent.from_tools(
    [tool_track_delivery, tool_upcoming_deliveries],
    llm=llm,
    verbose=True,
    system_prompt=SYSTEM_PROMPT.format(
        DOMAIN_DESCRIPTION=DOMAIN_DESCRIPTION,
        ADDITIONAL_INSTRUCTIONS=ADDITIONAL_INSTRUCTIONS,
    )
)

# === АГЕНТ ПРОИЗВОДСТВА ===
# Инструменты для Производства
def get_line_status(line_id: str) -> str:
    """Возвращает статус производственной линии"""
    add_active_node('get_line_status')
    add_active_connection('production_to_get_line_status')
    add_agent_log(f"Вызвана функция get_line_status для линии: {line_id}")
    data = json.load(open(PRODUCTION_FILE, 'r', encoding='utf-8'))
    for line in data:
        if line['line_id'] == line_id:
            return (f"Линия {line_id}:\n"
                    f"Продукт: {line['product']}\n"
                    f"Состояние: {line['status']}\n"
                    f"Выпуск: {line['output_per_hour']} шт/час\n"
                    f"Брак: {line['defect_rate']}%")
    return "Линия не найдена"

def get_production_summary() -> str:
    """Общая информация о производстве"""
    add_active_node('get_production_summary')
    add_active_connection('production_to_get_production_summary')
    add_agent_log("Вызвана функция get_production_summary")
    data = json.load(open(PRODUCTION_FILE, 'r', encoding='utf-8'))
    total_lines = len(data)
    active_lines = len([l for l in data if l['status'] == 'работает'])
    result = f"Всего линий: {total_lines}, активных: {active_lines}\n\nДетали:\n"
    for line in data:
        result += f"{line['line_id']} - {line['product']} ({line['status']})\n"
    return result

# Производство
tool_line_status = FunctionTool.from_defaults(
    fn=get_line_status,
    name="get_line_status",
    description="Возвращает текущий статус производственной линии по ID"
)

tool_production_summary = FunctionTool.from_defaults(
    fn=get_production_summary,
    name="get_production_summary",
    description="Показывает общий статус производства: сколько линий работает"
)

DOMAIN_DESCRIPTION = "контроль состояния производственных линий, загрузки оборудования, объёмов выпуска и уровня простоев"
ADDITIONAL_INSTRUCTIONS = "Фокусируйтесь на текущем статусе линий: работает, в ремонте, остановлена. При запросах о производительности указывайте выпуск в штуках в час и уровень брака. Не объясняйте причины простоев, если они не указаны в данных."

# Агент-производства
agent_production = ReActAgent.from_tools(
    [tool_line_status, tool_production_summary],
    llm=llm,
    verbose=True,
    system_prompt=SYSTEM_PROMPT.format(
        DOMAIN_DESCRIPTION=DOMAIN_DESCRIPTION,
        ADDITIONAL_INSTRUCTIONS=ADDITIONAL_INSTRUCTIONS,
    )
)

# === АГЕНТ КОНТРОЛЯ КАЧЕСТВА ===
# Инструменты для Контроля Качества
def check_batch_quality(batch_id: str) -> str:
    """Проверяет результаты контроля качества по номеру партии"""
    add_active_node('check_batch_quality')
    add_active_connection('quality_to_check_batch_quality')
    add_agent_log(f"Вызвана функция check_batch_quality для партии: {batch_id}")
    data = json.load(open(QUALITY_FILE, 'r', encoding='utf-8'))
    for batch in data:
        if batch['batch_id'] == batch_id:
            status = "✅ Сертифицировано" if batch['certified'] else "❌ Не прошло контроль"
            reason = f"\nПричина: {batch['reason']}" if not batch['certified'] else ""
            return (f"Партия {batch_id} ({batch['product']}):\n"
                    f"Результат: {batch['result']}\n"
                    f"Найдено дефектов: {batch['defects_found']}\n"
                    f"{status}{reason}")
    return "Партия не найдена"

def get_failed_batches() -> str:
    """Возвращает список партий, не прошедших контроль"""
    add_active_node('get_failed_batches')
    add_active_connection('quality_to_get_failed_batches')
    add_agent_log("Вызвана функция get_failed_batches")
    data = json.load(open(QUALITY_FILE, 'r', encoding='utf-8'))
    failed = [b for b in data if b['result'] == 'не прошёл']
    if not failed:
        return "Все партии прошли контроль."
    result = "Партии, не прошедшие контроль:\n"
    for b in failed:
        result += f"- {b['batch_id']} ({b['product']}): {b['reason']}\n"
    return result

# Качество
tool_check_batch = FunctionTool.from_defaults(
    fn=check_batch_quality,
    name="check_batch_quality",
    description="Проверяет результаты контроля качества по номеру партии"
)

tool_failed_batches = FunctionTool.from_defaults(
    fn=get_failed_batches,
    name="get_failed_batches",
    description="Возвращает список партий, не прошедших контроль качества"
)

DOMAIN_DESCRIPTION = "контроль качества выпускаемой продукции, проверка результатов тестирования партий, анализ выявленных дефектов и статуса сертификации"
ADDITIONAL_INSTRUCTIONS = "При проверке партии указывайте результат контроля, количество дефектов и причину отказа, если она есть. Если партия не прошла контроль, явно сообщайте об этом. Не давайте рекомендаций по устранению дефектов."

# Агент-качества
agent_quality = ReActAgent.from_tools(
    [tool_check_batch, tool_failed_batches],
    llm=llm,
    verbose=True,
    system_prompt=SYSTEM_PROMPT.format(
        DOMAIN_DESCRIPTION=DOMAIN_DESCRIPTION,
        ADDITIONAL_INSTRUCTIONS=ADDITIONAL_INSTRUCTIONS,
    )
)

def call_agent(agent, query: str) -> str:
    """Функция для взаимодействия с любым агентом"""
    response = agent.chat(query)
    return str(response)

# === ОРКЕСТРАТОР АГЕНТОВ ===
ORCHESTRATOR_SYSTEM_PROMPT = """Вы — **Оркестратор агентов**, центральный координатор, управляющий несколькими специализированными агентами:

1. **Агент-закупщик** — отвечает за цены конкурентов и наличие на складе.
2. **Агент-логист** — отвечает за статус поставок, сроки, трек-номера.
3. **Агент-производства** — отвечает за статус линий, выпуск, простои.
4. **Агент-качества** — отвечает за результаты проверки партий, брак, сертификацию.

### Ваши правила:
- Внимательно анализируйте запрос пользователя.
- Используйте **только те инструменты (агенты), которые необходимы**.
- Если вопрос требует данных из нескольких доменов — вызовите несколько агентов.
- После получения всех данных — **объедините ответ в один связный, лаконичный ответ**.
- Говорите на языке пользователя (обычно русский), избегайте технических терминов, если не требуется.
- Не вымышляйте информацию. Всегда полагайтесь на ответы агентов.
- Не объясняйте, как вы работали — просто дайте ответ.

Пример:
> Пользователь: Почему задерживается выпуск продукции?
> Вы: Проверяю статус поставок компонентов и состояние производственной линии...
> (вызов agent_logistics и agent_production)
> Ответ: Поставка компонентов задерживается на 2 дня. Линия 4 простаивает в ожидании.
""".strip()

def query_buyer_agent(query: str) -> str:
    """Передаёт запрос агенту-закупщику."""
    import io
    import sys
    
    add_active_node('buyer')
    add_active_connection('orchestrator_to_buyer')
    add_agent_log("Buyer agent started...")
    
    # Очищаем предыдущие активные функции этого агента
    remove_agent_functions('buyer')
    
    # Перехватываем вывод агента для логирования мыслей
    old_stdout = sys.stdout
    captured_output = io.StringIO()
    sys.stdout = captured_output
    
    try:
        response = agent_buyer.chat(query)
        # Получаем перехваченный вывод
        agent_output = captured_output.getvalue()
        sys.stdout = old_stdout
        
        # Логируем мысли агента
        for line in agent_output.split('\n'):
            line = line.strip()
            if line:
                if 'Thought:' in line:
                    add_agent_log(f"Buyer thought: {line.split('Thought:')[-1].strip()}")
                elif 'Action:' in line:
                    add_agent_log(f"Buyer action: {line.split('Action:')[-1].strip()}")
                elif 'Observation:' in line:
                    add_agent_log(f"Buyer observation: {line.split('Observation:')[-1].strip()}")
                elif 'Answer:' in line:
                    add_agent_log(f"Buyer answer: {line.split('Answer:')[-1].strip()}")
                elif 'Running step' in line:
                    add_agent_log(f"Buyer step: {line}")
        
        add_agent_log("Buyer agent completed")
        return str(response)
        
    except Exception as e:
        sys.stdout = old_stdout
        raise e

def query_logistics_agent(query: str) -> str:
    """Передаёт запрос агенту-логисту."""
    import io
    import sys
    
    add_active_node('logistics')
    add_active_connection('orchestrator_to_logistics')
    add_agent_log("Logistics agent started...")
    
    # Очищаем предыдущие активные функции этого агента
    remove_agent_functions('logistics')
    
    # Перехватываем вывод агента для логирования мыслей
    old_stdout = sys.stdout
    captured_output = io.StringIO()
    sys.stdout = captured_output
    
    try:
        response = agent_logistics.chat(query)
        # Получаем перехваченный вывод
        agent_output = captured_output.getvalue()
        sys.stdout = old_stdout
        
        # Логируем мысли агента
        for line in agent_output.split('\n'):
            line = line.strip()
            if line:
                if 'Thought:' in line:
                    add_agent_log(f"Logistics thought: {line.split('Thought:')[-1].strip()}")
                elif 'Action:' in line:
                    add_agent_log(f"Logistics action: {line.split('Action:')[-1].strip()}")
                elif 'Observation:' in line:
                    add_agent_log(f"Logistics observation: {line.split('Observation:')[-1].strip()}")
                elif 'Answer:' in line:
                    add_agent_log(f"Logistics answer: {line.split('Answer:')[-1].strip()}")
                elif 'Running step' in line:
                    add_agent_log(f"Logistics step: {line}")
        
        add_agent_log("Logistics agent completed")
        return str(response)
        
    except Exception as e:
        sys.stdout = old_stdout
        raise e

def query_production_agent(query: str) -> str:
    """Передаёт запрос агенту-производства."""
    import io
    import sys
    
    add_active_node('production')
    add_active_connection('orchestrator_to_production')
    add_agent_log("Production agent started...")
    
    # Очищаем предыдущие активные функции этого агента
    remove_agent_functions('production')
    
    # Перехватываем вывод агента для логирования мыслей
    old_stdout = sys.stdout
    captured_output = io.StringIO()
    sys.stdout = captured_output
    
    try:
        response = agent_production.chat(query)
        # Получаем перехваченный вывод
        agent_output = captured_output.getvalue()
        sys.stdout = old_stdout
        
        # Логируем мысли агента
        for line in agent_output.split('\n'):
            line = line.strip()
            if line:
                if 'Thought:' in line:
                    add_agent_log(f"Production thought: {line.split('Thought:')[-1].strip()}")
                elif 'Action:' in line:
                    add_agent_log(f"Production action: {line.split('Action:')[-1].strip()}")
                elif 'Observation:' in line:
                    add_agent_log(f"Production observation: {line.split('Observation:')[-1].strip()}")
                elif 'Answer:' in line:
                    add_agent_log(f"Production answer: {line.split('Answer:')[-1].strip()}")
                elif 'Running step' in line:
                    add_agent_log(f"Production step: {line}")
        
        add_agent_log("Production agent completed")
        return str(response)
        
    except Exception as e:
        sys.stdout = old_stdout
        raise e

def query_quality_agent(query: str) -> str:
    """Передаёт запрос агенту-качества."""
    import io
    import sys
    
    add_active_node('quality')
    add_active_connection('orchestrator_to_quality')
    add_agent_log("Quality agent started...")
    
    # Очищаем предыдущие активные функции этого агента
    remove_agent_functions('quality')
    
    # Перехватываем вывод агента для логирования мыслей
    old_stdout = sys.stdout
    captured_output = io.StringIO()
    sys.stdout = captured_output
    
    try:
        response = agent_quality.chat(query)
        # Получаем перехваченный вывод
        agent_output = captured_output.getvalue()
        sys.stdout = old_stdout
        
        # Логируем мысли агента
        for line in agent_output.split('\n'):
            line = line.strip()
            if line:
                if 'Thought:' in line:
                    add_agent_log(f"Quality thought: {line.split('Thought:')[-1].strip()}")
                elif 'Action:' in line:
                    add_agent_log(f"Quality action: {line.split('Action:')[-1].strip()}")
                elif 'Observation:' in line:
                    add_agent_log(f"Quality observation: {line.split('Observation:')[-1].strip()}")
                elif 'Answer:' in line:
                    add_agent_log(f"Quality answer: {line.split('Answer:')[-1].strip()}")
                elif 'Running step' in line:
                    add_agent_log(f"Quality step: {line}")
        
        add_agent_log("Quality agent completed")
        return str(response)
        
    except Exception as e:
        sys.stdout = old_stdout
        raise e

# --- Создание инструментов ---
tool_buyer = FunctionTool.from_defaults(
    fn=query_buyer_agent,
    name="agent_buyer",
    description="Используйте, если вопрос о ценах конкурентов или наличии на складе."
)

tool_logistics = FunctionTool.from_defaults(
    fn=query_logistics_agent,
    name="agent_logistics",
    description="Используйте, если вопрос о статусе поставок, доставках, трек-номерах."
)

tool_production = FunctionTool.from_defaults(
    fn=query_production_agent,
    name="agent_production",
    description="Используйте, если вопрос о статусе линий, объёме выпуска, простоях."
)

tool_quality = FunctionTool.from_defaults(
    fn=query_quality_agent,
    name="agent_quality",
    description="Используйте, если вопрос о контроле качества, браке, результатах проверки партий."
)

# --- Создаём оркестратор ---
orchestrator = ReActAgent.from_tools(
    tools=[
        tool_buyer,
        tool_logistics,
        tool_production,
        tool_quality,
    ],
    llm=llm,
    verbose=True,
    system_prompt=ORCHESTRATOR_SYSTEM_PROMPT,
)

# === ЦЕНЗОР ===
# Системный промпт — строгий фильтр
system_prompt = '''
Ты — фильтр запросов. Определи, относится ли вопрос к деловой сфере производства:
- Производственные процессы
- Управление поставками, логистика
- Закупки сырья и материалов
- Контроль качества, выпуск продукции
- Работа оборудования, простои

Если запрос относится к этим темам — верни **исходный вопрос без изменений**.
Если НЕ относится — верни **точно**: "Запрос не относится к деловой сфере производства."

Правила:
- Никаких пояснений, комментариев, вежливостей.
- Не используй форматирование, кавычки, маркеры.
- Не добавляй "Ответ:", "Результат:" и т.п.
- Возвращай ТОЛЬКО один из двух вариантов:
      1. Исходный вопрос (дословно)
      2. "Запрос не относится к деловой сфере производства."

Примеры:
Вопрос: Сколько стоит тонна алюминия у поставщиков?
Ответ: Сколько стоит тонна алюминия у поставщиков?

Вопрос: Как приготовить кофе?
Ответ: Запрос не относится к деловой сфере производства.
'''.strip()

def check_message(text):
    # Создаем сообщения
    messages = [
        ChatMessage(role="system", content=system_prompt),
        ChatMessage(role="user", content=text)
    ]

    # Вызываем chat
    response = llm.chat(messages)
    return response.message.blocks[0].text

# === ОСНОВНЫЕ ФУНКЦИИ ДЛЯ ИНТЕГРАЦИИ ===
def run_agent_system(user_input: str):
    """Запускает систему агентов для обработки запроса пользователя"""
    from typing import Dict, Any
    import io
    import sys
    
    # Очищаем логи и активные узлы для нового запроса
    clear_agent_logs()
    clear_active_nodes()
    
    # Инициализируем базовые активные узлы и соединения
    add_active_node('request')
    
    try:
        add_agent_log(f"Request entry: {user_input}")
        
        # Проверяем запрос через цензор
        add_agent_log("Censor started...")
        add_active_node('censor')
        add_active_connection('request_to_censor')
        
        filtered_query = check_message(user_input)
        
        if filtered_query == "Запрос не относится к деловой сфере производства.":
            add_agent_log("Censor passed? N")
            add_agent_log("Запрос отклонен цензором", 'warning')
            return {
                'error': 'Запрос не относится к производственной системе',
                'messages': [],
                'result': 'Пожалуйста, уточните ваш запрос. Система работает только с вопросами, связанными с производством.',
                'next_agent': 'general_agent',
                'active_nodes': get_active_nodes(),
                'active_connections': get_active_connections()
            }
        
        add_agent_log("Censor passed? Y")
        add_agent_log(f"Запрос прошел цензуру: {filtered_query}")
        
        # Обрабатываем запрос через оркестратор
        add_agent_log("Orchestrator started...")
        add_active_node('orchestrator')
        add_active_connection('censor_to_orchestrator')
        
        # Перехватываем вывод оркестратора для логирования мыслей
        old_stdout = sys.stdout
        captured_output = io.StringIO()
        sys.stdout = captured_output
        
        try:
            response = orchestrator.chat(filtered_query)
            # Получаем перехваченный вывод
            orchestrator_output = captured_output.getvalue()
            sys.stdout = old_stdout
            
            # Логируем мысли оркестратора
            for line in orchestrator_output.split('\n'):
                line = line.strip()
                if line:
                    if 'Thought:' in line:
                        add_agent_log(f"Orchestrator thought: {line.split('Thought:')[-1].strip()}")
                    elif 'Action:' in line:
                        add_agent_log(f"Orchestrator action: {line.split('Action:')[-1].strip()}")
                    elif 'Observation:' in line:
                        add_agent_log(f"Orchestrator observation: {line.split('Observation:')[-1].strip()}")
                    elif 'Answer:' in line:
                        add_agent_log(f"Orchestrator answer: {line.split('Answer:')[-1].strip()}")
                    elif 'Running step' in line:
                        add_agent_log(f"Orchestrator step: {line}")
            
            add_agent_log(f"Orchestrator completed")
            
        except Exception as e:
            sys.stdout = old_stdout
            raise e
        
        # Активные узлы и соединения теперь автоматически отслеживаются
        # через вызовы add_active_node() и add_active_connection() в функциях агентов
        
        return {
            'messages': [str(response)],
            'result': str(response),
            'next_agent': 'orchestrator',
            'active_nodes': get_active_nodes(),
            'active_connections': get_active_connections()
        }
        
    except Exception as e:
        add_agent_log(f"Ошибка обработки запроса: {e}", 'error')
        return {
            'error': str(e),
            'messages': [],
            'result': f'Ошибка обработки запроса: {e}',
            'next_agent': 'general_agent',
            'active_nodes': get_active_nodes(),
            'active_connections': get_active_connections()
        }

# Глобальные переменные для хранения логов и активных узлов
agent_logs = []
active_nodes = []
active_connections = []

def add_agent_log(message: str, level: str = 'info'):
    """Добавляет лог в глобальный список"""
    from datetime import datetime
    timestamp = datetime.now().strftime('%H:%M:%S')
    log_entry = {
        'timestamp': timestamp,
        'message': message,
        'level': level
    }
    agent_logs.append(log_entry)

def get_agent_logs():
    """Возвращает все логи агентов"""
    return agent_logs.copy()

def clear_agent_logs():
    """Очищает логи агентов"""
    agent_logs.clear()

def clear_active_nodes():
    """Очищает активные узлы и соединения"""
    global active_nodes, active_connections
    active_nodes = []
    active_connections = []

def add_active_node(node_name: str):
    """Добавляет активный узел"""
    global active_nodes
    if node_name not in active_nodes:
        active_nodes.append(node_name)

def add_active_connection(connection_name: str):
    """Добавляет активное соединение"""
    global active_connections
    if connection_name not in active_connections:
        active_connections.append(connection_name)

def get_active_nodes():
    """Возвращает активные узлы"""
    return active_nodes.copy()

def get_active_connections():
    """Возвращает активные соединения"""
    return active_connections.copy()

def remove_agent_functions(agent_name: str):
    """Удаляет все функции указанного агента из активных узлов и соединений"""
    global active_nodes, active_connections
    
    # Определяем функции для каждого агента
    agent_functions = {
        'buyer': ['fetch_prices', 'check_stock'],
        'logistics': ['track_delivery', 'get_deliveries'],
        'production': ['get_line_status', 'get_production_summary'],
        'quality': ['check_batch_quality', 'get_failed_batches']
    }
    
    if agent_name in agent_functions:
        for func in agent_functions[agent_name]:
            if func in active_nodes:
                active_nodes.remove(func)
            connection_name = f'{agent_name}_to_{func}'
            if connection_name in active_connections:
                active_connections.remove(connection_name)
    """Очищает логи агентов"""
    global agent_logs
    agent_logs = []

def create_agent_graph():
    """Создает граф агентов для визуализации"""
    try:
        from agent_graph import create_agent_graph as create_graph
        return create_graph()
    except ImportError:
        # Fallback если файл agent_graph.py недоступен
        return {
            'nodes': {
                'request': {'type': 'input', 'name': 'Запрос пользователя'},
                'censor': {'type': 'filter', 'name': 'Цензор'},
                'orchestrator': {'type': 'orchestrator', 'name': 'Оркестратор'},
                'buyer': {'type': 'agent', 'name': 'Агент закупок'},
                'logistics': {'type': 'agent', 'name': 'Агент логистики'},
                'production': {'type': 'agent', 'name': 'Агент производства'},
                'quality': {'type': 'agent', 'name': 'Агент качества'}
            },
            'connections': [
                {'from': 'request', 'to': 'censor'},
                {'from': 'censor', 'to': 'orchestrator'},
                {'from': 'orchestrator', 'to': 'buyer'},
                {'from': 'orchestrator', 'to': 'logistics'},
                {'from': 'orchestrator', 'to': 'production'},
                {'from': 'orchestrator', 'to': 'quality'}
            ]
        } 