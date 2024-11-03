import streamlit as st
import google.generativeai as genai
import time
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import seaborn as sns

# Настройка API ключа и модели

api_key = st.secrets["GOOGLE_API_KEY"]
genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-1.5-pro-exp-0827")

# Обновленный системный промпт

system_prompt = """Ты ассистент по бизнес-анализу (ритейл и продажи). Действуй как система из трех агентов:

АГЕНТ 1 (Аналитик):
- Использует Chain-of-Thought (CoT)
- Разбивает задачу на этапы
- Оценивает каждый этап (rewards 0-1)
- При rewards < 0.9 запускает новую итерацию

АГЕНТ 2 (Программист):
- Пишет и выполняет Python код
- Создает визуализации (Matplotlib/Plotly/Seaborn)
- Передает результаты Агенту 3

АГЕНТ 3 (Валидатор):
- Проверяет результаты (rewards 0-1)
- Формирует структурированный ответ
- Обеспечивает вывод пользователю

При анализе данных:
- Оценивай динамику по столбцу "доля от всех запросов, %"
- Используй табличный формат где возможно
- Следуй точным требованиям конкретного анализа
"""

# Интерфейс загрузки файла и вопроса

st.title("📊 Retail Analytics Assistant")
st.write("Загрузите Excel файл и задайте вопрос – я помогу с анализом!")

uploaded_file = st.file_uploader("Загрузите файл", type=['xlsx', 'csv'])
question = st.text_area(
    "Задайте вопрос по данным",
    placeholder="Например: Проведи ABC-анализ или Создай график топ-3",
    disabled=not uploaded_file
)

# Обработка данных и генерация ответа
if uploaded_file and question:
    try:
        # Чтение данных
        if uploaded_file.name.endswith('.xlsx'):
            df = pd.read_excel(uploaded_file)
        else:
            df = pd.read_csv(uploaded_file)
        
        # Подготовка контекста с данными
        data_context = f"Данные из файла:\n{df.head().to_string()}\n\nРазмерность: {df.shape}"
        
        # Формирование промпта
        prompt = f"""{system_prompt}
        
        Данные:
        {data_context}
        
        Вопрос: {question}
        
        Пожалуйста, проанализируйте данные и ответьте на вопрос."""

        # Генерация ответа
        response = model.generate_content(prompt, stream=True)
        
        # Контейнер для вывода
        response_container = st.empty()
        viz_container = st.empty()
        full_response = ""

        # Обработка ответа
        for chunk in response:
            if chunk.text:
                full_response += chunk.text
                response_container.markdown(full_response)
                
                # Если в ответе есть код для визуализации
                if "```python" in full_response and "plt" in full_response:
                    try:
                        # Извлечение и выполнение кода визуализации
                        code = full_response.split("```python")[1].split("```")[0]
                        exec(code)
                        viz_container.pyplot(plt.gcf())
                        plt.close()
                    except Exception as e:
                        st.error(f"Ошибка при создании визуализации: {str(e)}")

    except Exception as e:
        st.error(f"Произошла ошибка: {str(e)}")

# Обработка визуализаций

def create_visualization(df, viz_type, params):
    if viz_type == "bar":
        fig = px.bar(df, **params)
    elif viz_type == "line":
        fig = px.line(df, **params)
    elif viz_type == "scatter":
        fig = px.scatter(df, **params)
    return fig

# Добавляем в основной код
if "создай график" in question.lower():
    try:
        # Генерация кода визуализации через Gemini
        viz_prompt = f"Напиши код на Python для создания графика. Данные: {df.head().to_string()}"
        viz_response = model.generate_content(viz_prompt)
        
        # Выполнение кода и отображение графика
        exec(viz_response.text)
        st.plotly_chart(fig)
    except Exception as e:
        st.error(f"Ошибка при создании визуализации: {str(e)}")
