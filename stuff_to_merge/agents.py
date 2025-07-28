import os
from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END, START
from langchain_core.messages import HumanMessage, AIMessage
from llama_index.llms.together import TogetherLLM
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()
API_KEY = os.getenv("TOGETHER_API_KEY")

# Инициализируем LLM
model = "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo"
llm = TogetherLLM(model=model, api_key=API_KEY)

# Определяем состояние для агентов
class AgentState(TypedDict):
    messages: List[HumanMessage | AIMessage]
    current_agent: str
    task_description: str
    result: str
    next_agent: str

# Инструменты для разных агентов (без декоратора @tool)

def get_current_time() -> str:
    """Возвращает текущее время"""
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def search_wikipedia(query: str) -> str:
    """Ищет информацию в Wikipedia"""
    import wikipedia
    wikipedia.set_lang('ru')
    try:
        return wikipedia.summary(query, sentences=2)
    except Exception as e:
        return f"Ошибка поиска: {e}"

def calculate_math(expression: str) -> str:
    """Вычисляет математическое выражение"""
    try:
        # Безопасное вычисление
        allowed_names = {
            k: v for k, v in __builtins__.items() 
            if k in ['abs', 'round', 'min', 'max', 'sum']
        }
        allowed_names.update({
            'sin': lambda x: __import__('math').sin(x),
            'cos': lambda x: __import__('math').cos(x),
            'sqrt': lambda x: __import__('math').sqrt(x),
        })
        result = eval(expression, {"__builtins__": {}}, allowed_names)
        return f"Результат: {result}"
    except Exception as e:
        return f"Ошибка вычисления: {e}"

def translate_text(text: str, target_language: str = "английский") -> str:
    """Переводит текст на указанный язык"""
    # Простая имитация перевода
    translations = {
        "английский": f"[EN] {text}",
        "немецкий": f"[DE] {text}",
        "французский": f"[FR] {text}"
    }
    return translations.get(target_language, f"[{target_language.upper()}] {text}")

# Агент-координатор
def coordinator_agent(state: AgentState) -> AgentState:
    """Определяет, какой агент должен обработать задачу"""
    messages = state["messages"]
    task = state["task_description"]
    
    # Определяем тип задачи и назначаем агента
    if any(word in task.lower() for word in ["время", "час", "дата"]):
        next_agent = "time_agent"
    elif any(word in task.lower() for word in ["вики", "информация", "что такое", "кто такой"]):
        next_agent = "research_agent"
    elif any(word in task.lower() for word in ["вычисли", "посчитай", "математика", "+", "-", "*", "/"]):
        next_agent = "math_agent"
    elif any(word in task.lower() for word in ["переведи", "перевод", "translate"]):
        next_agent = "translation_agent"
    else:
        next_agent = "general_agent"
    
    state["next_agent"] = next_agent
    state["messages"].append(AIMessage(content=f"Задача передана агенту: {next_agent}"))
    return state

# Агент времени
def time_agent(state: AgentState) -> AgentState:
    """Обрабатывает запросы, связанные со временем"""
    time_info = get_current_time()
    response = f"Текущее время: {time_info}"
    state["result"] = response
    state["messages"].append(AIMessage(content=response))
    return state

# Агент исследований
def research_agent(state: AgentState) -> AgentState:
    """Ищет информацию в Wikipedia"""
    task = state["task_description"]
    # Извлекаем ключевые слова для поиска
    search_query = task.replace("что такое", "").replace("кто такой", "").strip()
    if len(search_query) > 3:
        info = search_wikipedia(search_query)
        response = f"Информация о '{search_query}': {info}"
    else:
        response = "Не удалось определить, что искать. Уточните запрос."
    
    state["result"] = response
    state["messages"].append(AIMessage(content=response))
    return state

# Агент математики
def math_agent(state: AgentState) -> AgentState:
    """Выполняет математические вычисления"""
    task = state["task_description"]
    # Извлекаем математическое выражение
    import re
    math_pattern = r'(\d+[\+\-\*\/\s]+\d+)'
    match = re.search(math_pattern, task)
    
    if match:
        expression = match.group(1).replace(" ", "")
        result = calculate_math(expression)
        response = f"Вычисление: {expression} = {result}"
    else:
        response = "Не удалось найти математическое выражение для вычисления."
    
    state["result"] = response
    state["messages"].append(AIMessage(content=response))
    return state

# Агент перевода
def translation_agent(state: AgentState) -> AgentState:
    """Переводит текст"""
    task = state["task_description"]
    # Простая логика извлечения текста для перевода
    if "переведи" in task.lower():
        # Извлекаем текст после "переведи"
        text_start = task.lower().find("переведи") + 8
        text_to_translate = task[text_start:].strip()
        
        # Определяем язык перевода
        target_lang = "английский"
        if "на английский" in task.lower():
            target_lang = "английский"
        elif "на немецкий" in task.lower():
            target_lang = "немецкий"
        elif "на французский" in task.lower():
            target_lang = "французский"
        
        result = translate_text(text_to_translate, target_lang)
        response = f"Перевод: {result}"
    else:
        response = "Не удалось определить текст для перевода."
    
    state["result"] = response
    state["messages"].append(AIMessage(content=response))
    return state

# Общий агент
def general_agent(state: AgentState) -> AgentState:
    """Обрабатывает общие запросы"""
    messages = state["messages"]
    response = llm.chat(messages)
    result = response.message.blocks[0].text
    state["result"] = result
    state["messages"].append(AIMessage(content=result))
    return state

# Функция маршрутизации
def route_to_agent(state: AgentState) -> str:
    """Определяет следующий агент на основе состояния"""
    return state["next_agent"]

# Создаем граф агентов
def create_agent_graph():
    workflow = StateGraph(AgentState)
    
    # Добавляем узлы
    workflow.add_node("coordinator", coordinator_agent)
    workflow.add_node("time_agent", time_agent)
    workflow.add_node("research_agent", research_agent)
    workflow.add_node("math_agent", math_agent)
    workflow.add_node("translation_agent", translation_agent)
    workflow.add_node("general_agent", general_agent)
    
    # Добавляем ребра - ВАЖНО: начинаем с START
    workflow.add_edge(START, "coordinator")
    
    # Используем conditional_edges для маршрутизации
    workflow.add_conditional_edges(
        "coordinator",
        route_to_agent,
        {
            "time_agent": "time_agent",
            "research_agent": "research_agent", 
            "math_agent": "math_agent",
            "translation_agent": "translation_agent",
            "general_agent": "general_agent"
        }
    )
    
    # Добавляем конечные точки
    workflow.add_edge("time_agent", END)
    workflow.add_edge("research_agent", END)
    workflow.add_edge("math_agent", END)
    workflow.add_edge("translation_agent", END)
    workflow.add_edge("general_agent", END)
    
    return workflow.compile()

# Функция для запуска агентов
def run_agent_system(user_input: str) -> dict:
    """Запускает систему агентов"""
    graph = create_agent_graph()
    
    # Инициализируем состояние
    initial_state = {
        "messages": [HumanMessage(content=user_input)],
        "current_agent": "coordinator",
        "task_description": user_input,
        "result": "",
        "next_agent": ""
    }
    
    # Запускаем граф
    result = graph.invoke(initial_state)
    return result

if __name__ == "__main__":
    # Тест системы
    test_query = "Сколько сейчас времени?"
    result = run_agent_system(test_query)
    print(f"Результат: {result['result']}") 