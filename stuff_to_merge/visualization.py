import streamlit as st
from graphviz import Digraph
from agents import run_agent_system
import json

def create_agent_interaction_graph(agent_state: dict) -> Digraph:
    """Создает граф взаимодействия агентов"""
    dot = Digraph()
    dot.attr(rankdir='TB')
    
    # Настройки стилей
    dot.attr('node', shape='box', style='filled', fontname='Arial')
    
    # Добавляем узлы
    messages = agent_state.get('messages', [])
    
    # Начальный узел
    dot.node('user', '👤 Пользователь', fillcolor='lightblue')
    
    # Узлы агентов
    coordinator_color = 'lightgreen'
    agent_colors = {
        'time_agent': 'lightyellow',
        'research_agent': 'lightcoral', 
        'math_agent': 'lightcyan',
        'translation_agent': 'lightpink',
        'general_agent': 'lightgray'
    }
    
    # Координатор
    dot.node('coordinator', '🎯 Координатор', fillcolor=coordinator_color)
    dot.edge('user', 'coordinator')
    
    # Определяем какой агент был использован
    next_agent = agent_state.get('next_agent', 'general_agent')
    agent_name = next_agent.replace('_', ' ').title()
    agent_color = agent_colors.get(next_agent, 'lightgray')
    
    # Агент-исполнитель
    dot.node('executor', f'🤖 {agent_name}', fillcolor=agent_color)
    dot.edge('coordinator', 'executor')
    
    # Результат
    result = agent_state.get('result', 'Нет результата')
    dot.node('result', f'📋 Результат\n{result[:50]}...', fillcolor='lightgreen')
    dot.edge('executor', 'result')
    
    return dot

def create_message_flow_graph(agent_state: dict) -> Digraph:
    """Создает граф потока сообщений"""
    dot = Digraph()
    dot.attr(rankdir='LR')
    
    messages = agent_state.get('messages', [])
    
    for i, message in enumerate(messages):
        if hasattr(message, 'content'):
            content = message.content
            # Обрезаем длинные сообщения
            if len(content) > 100:
                content = content[:100] + "..."
            
            if hasattr(message, 'type') and message.type == 'human':
                dot.node(f'msg_{i}', f'👤 {content}', 
                        shape='box', fillcolor='lightblue')
            else:
                dot.node(f'msg_{i}', f'🤖 {content}', 
                        shape='box', fillcolor='lightyellow')
            
            if i > 0:
                dot.edge(f'msg_{i-1}', f'msg_{i}')
    
    return dot

def display_agent_analytics(agent_state: dict):
    """Отображает аналитику работы агентов"""
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Статистика")
        
        # Подсчитываем статистику
        messages = agent_state.get('messages', [])
        agent_used = agent_state.get('next_agent', 'general_agent')
        
        st.metric("Количество сообщений", len(messages))
        st.metric("Использованный агент", agent_used.replace('_', ' ').title())
        
        # Время выполнения (если есть)
        if 'execution_time' in agent_state:
            st.metric("Время выполнения", f"{agent_state['execution_time']:.2f}с")
    
    with col2:
        st.subheader("🔧 Инструменты")
        
        # Показываем использованные инструменты
        tools_used = []
        if agent_used == 'time_agent':
            tools_used.append('get_current_time')
        elif agent_used == 'research_agent':
            tools_used.append('search_wikipedia')
        elif agent_used == 'math_agent':
            tools_used.append('calculate_math')
        elif agent_used == 'translation_agent':
            tools_used.append('translate_text')
        
        for tool in tools_used:
            st.write(f"• {tool}")

def main():
    st.set_page_config(
        page_title="Система агентов с визуализацией",
        page_icon="🤖",
        layout="wide"
    )
    
    st.title("🤖 Система взаимодействующих агентов")
    st.markdown("---")
    
    # Боковая панель с примерами
    with st.sidebar:
        st.header("💡 Примеры запросов")
        
        examples = [
            "Сколько сейчас времени?",
            "Что такое искусственный интеллект?",
            "Посчитай 15 + 27",
            "Переведи 'Привет мир' на английский",
        ]
        
        for example in examples:
            if st.button(example, key=example):
                st.session_state.user_input = example
    
    # Основная область
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("💬 Ввод запроса")
        
        # Поле ввода
        user_input = st.text_input(
            "Введите ваш запрос:",
            value=st.session_state.get('user_input', ''),
            placeholder="Например: Сколько сейчас времени?"
        )
        
        if st.button("🚀 Отправить", type="primary"):
            if user_input.strip():
                with st.spinner("Агенты обрабатывают запрос..."):
                    # Запускаем систему агентов
                    result = run_agent_system(user_input)
                    
                    # Сохраняем результат в session state
                    st.session_state.last_result = result
                    st.session_state.user_input = user_input
                    
                    st.success("✅ Запрос обработан!")
    
    with col2:
        st.subheader("📈 Быстрая статистика")
        if 'last_result' in st.session_state:
            result = st.session_state.last_result
            agent_used = result.get('next_agent', 'general_agent')
            st.info(f"Использован агент: {agent_used.replace('_', ' ').title()}")
    
    # Отображение результатов
    if 'last_result' in st.session_state:
        st.markdown("---")
        result = st.session_state.last_result
        
        # Вкладки для разных типов визуализации
        tab1, tab2, tab3, tab4 = st.tabs([
            "📋 Результат", 
            "🔄 Граф агентов", 
            "💬 Поток сообщений",
            "📊 Аналитика"
        ])
        
        with tab1:
            st.subheader("🎯 Результат выполнения")
            st.write(result.get('result', 'Нет результата'))
            
            st.subheader("📝 Полная история")
            messages = result.get('messages', [])
            for i, msg in enumerate(messages):
                if hasattr(msg, 'content'):
                    if hasattr(msg, 'type') and msg.type == 'human':
                        st.write(f"**👤 Вы:** {msg.content}")
                    else:
                        st.write(f"**🤖 Агент:** {msg.content}")
                    st.markdown("---")
        
        with tab2:
            st.subheader("🔄 Граф взаимодействия агентов")
            graph = create_agent_interaction_graph(result)
            st.graphviz_chart(graph)
        
        with tab3:
            st.subheader("💬 Поток сообщений")
            flow_graph = create_message_flow_graph(result)
            st.graphviz_chart(flow_graph)
        
        with tab4:
            display_agent_analytics(result)
            
            # JSON для разработчиков
            with st.expander("🔧 JSON данные (для разработчиков)"):
                st.json(result)

if __name__ == "__main__":
    main() 