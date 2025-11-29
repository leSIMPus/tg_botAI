import os
import requests
import time
import uuid
import json
import sqlite3
from datetime import datetime
from typing import Optional, Dict, List, Tuple
from enum import Enum


class InterviewState(Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class InterviewType(Enum):
    JUNIOR_PYTHON = "junior_python"
    MIDDLE_PYTHON = "middle_python"
    SENIOR_PYTHON = "senior_python"
    DATA_SCIENTIST = "data_scientist"
    PYTHON_TEAM_LEAD = "python_team_lead"


class GigaChatHRClient:
    def __init__(self):
        self.access_token = None
        self.token_expires = 0
        self.interview_sessions = {}
        self._init_database()

    def _init_database(self):
        """Инициализация базы данных для истории собеседований"""
        self.conn = sqlite3.connect('interview_history.db', check_same_thread=False)
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS interviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                interview_type TEXT,
                questions TEXT,
                answers TEXT,
                feedback TEXT,
                score INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()

    def _update_access_token(self) -> bool:
        """Получаем access token используя Authorization key в Basic Auth"""
        try:
            auth_key = os.getenv("GIGACHAT_AUTH_CODE")
            url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
            rq_uid = str(uuid.uuid4())

            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json',
                'RqUID': rq_uid,
                'Authorization': f'Basic {auth_key}'
            }

            data = {'scope': 'GIGACHAT_API_PERS'}

            response = requests.post(
                url,
                headers=headers,
                data=data,
                verify=False,
                timeout=30
            )

            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data['access_token']
                self.token_expires = time.time() + token_data.get('expires_in', 1800) - 60
                return True
            else:
                print(f"❌ Ошибка получения token: {response.status_code}")
                return False

        except Exception as e:
            print(f"💥 Исключение: {str(e)}")
            return False

    def _check_and_refresh_token(self) -> bool:
        if not self.access_token or time.time() > self.token_expires:
            return self._update_access_token()
        return True

    def _get_interview_prompt(self, interview_type: InterviewType) -> str:
        """Генерирует промпт для создания уникальных вопросов"""
        prompts = {
            InterviewType.JUNIOR_PYTHON: """
            Создай 5 уникальных вопросов для собеседования на Junior Python разработчика.
            Вопросы должны охватывать:
            - Базовый синтаксис Python
            - Основные структуры данных
            - Простые алгоритмы
            - Основы ООП
            - Работа с файлами

            Вопросы должны быть практическими и проверять понимание основ.
            Формат: верни только вопросы, каждый с новой строки с номером.
            """,

            InterviewType.MIDDLE_PYTHON: """
            Создай 5 уникальных сложных вопросов для Middle Python разработчика.
            Темы:
            - Продвинутое ООП (инкапсуляция, полиморфизм, наследование)
            - Декораторы, генераторы, контекстные менеджеры
            - Многопоточность и асинхронность
            - Паттерны проектирования
            - Оптимизация и профилирование

            Вопросы должны проверять глубину понимания Python.
            Формат: только вопросы, каждый с новой строки.
            """,

            InterviewType.SENIOR_PYTHON: """
            Создай 5 экспертных вопросов для Senior Python разработчика.
            Фокус на:
            - Архитектурные решения
            - Масштабирование приложений
            - Code review и менторство
            - Системное проектирование
            - Технический долг и рефакторинг

            Вопросы должны быть сложными и ситуационными.
            Формат: только вопросы, каждый с новой строки.
            """,

            InterviewType.DATA_SCIENTIST: """
            Создай 5 вопросов для Data Scientist с использованием Python.
            Темы:
            - Pandas, NumPy, Scikit-learn
            - Визуализация данных
            - Статистический анализ
            - Машинное обучение
            - Предобработка данных

            Вопросы практические, связанные с реальными задачами.
            Формат: только вопросы, каждый с новой строки.
            """,

            InterviewType.PYTHON_TEAM_LEAD: """
            Создай 5 вопросов для Python Team Lead.
            Фокус на:
            - Управление командой
            - Техническое лидерство
            - Процессы разработки
            - Принятие архитектурных решений
            - Коммуникация с заказчиками

            Ситуационные и поведенческие вопросы.
            Формат: только вопросы, каждый с новой строки.
            """
        }
        return prompts.get(interview_type, prompts[InterviewType.MIDDLE_PYTHON])

    def _generate_questions(self, interview_type: InterviewType) -> List[Dict]:
        """Генерирует уникальные вопросы через GigaChat"""
        if not self._check_and_refresh_token():
            # Возвращаем вопросы по умолчанию если GigaChat недоступен
            return self._get_default_questions(interview_type)

        try:
            url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"

            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }

            messages = [
                {"role": "system",
                 "content": "Ты - опытный HR-специалист, который создает уникальные вопросы для технических собеседований."},
                {"role": "user", "content": self._get_interview_prompt(interview_type)}
            ]

            data = {
                'model': 'GigaChat',
                'messages': messages,
                'temperature': 0.9,  # Высокая температура для разнообразия
                'max_tokens': 1000
            }

            response = requests.post(url, headers=headers, json=data, verify=False, timeout=30)

            if response.status_code == 200:
                result = response.json()
                questions_text = result['choices'][0]['message']['content']
                return self._parse_questions(questions_text)
            else:
                return self._get_default_questions(interview_type)

        except Exception as e:
            print(f"💥 Ошибка генерации вопросов: {str(e)}")
            return self._get_default_questions(interview_type)

    def _parse_questions(self, questions_text: str) -> List[Dict]:
        """Парсит сгенерированные вопросы"""
        questions = []
        lines = questions_text.strip().split('\n')

        for line in lines:
            line = line.strip()
            if line and (line[0].isdigit() or '?' in line):
                # Убираем нумерацию "1. ", "2. " и т.д.
                question = line.split('. ', 1)[-1] if '. ' in line else line
                questions.append({
                    "question": question,
                    "type": "technical"
                })

        return questions[:5]  # Берем первые 5 вопросов

    def _get_default_questions(self, interview_type: InterviewType) -> List[Dict]:
        """Вопросы по умолчанию если GigaChat недоступен"""
        default_questions = {
            InterviewType.JUNIOR_PYTHON: [
                {"question": "Что такое список (list) в Python и чем он отличается от кортежа (tuple)?",
                 "type": "basic"},
                {"question": "Как работают циклы for и while в Python?", "type": "basic"},
                {"question": "Что такое функция и как ее объявить в Python?", "type": "basic"},
                {"question": "Как обрабатывать исключения в Python?", "type": "basic"},
                {"question": "Что такое модули и пакеты в Python?", "type": "basic"}
            ],
            InterviewType.MIDDLE_PYTHON: [
                {"question": "Объясните разницу между @classmethod, @staticmethod и обычными методами", "type": "oop"},
                {"question": "Как работают декораторы в Python? Приведите пример", "type": "advanced"},
                {"question": "Что такое GIL и как он влияет на многопоточность?", "type": "concurrency"},
                {"question": "Объясните принципы SOLID на примере Python", "type": "patterns"},
                {"question": "Как оптимизировать производительность Python-приложения?", "type": "performance"}
            ]
        }
        return default_questions.get(interview_type, default_questions[InterviewType.MIDDLE_PYTHON])

    def _get_feedback_prompt(self, interview_type: InterviewType, answers: List[Dict]) -> str:
        """Промпт для генерации фидбека с учетом типа интервью"""
        answers_text = ""
        for i, qa in enumerate(answers, 1):
            answers_text += f"{i}. Вопрос: {qa['question']}\n   Ответ: {qa['answer']}\n\n"

        level_names = {
            InterviewType.JUNIOR_PYTHON: "Junior Python разработчика",
            InterviewType.MIDDLE_PYTHON: "Middle Python разработчика",
            InterviewType.SENIOR_PYTHON: "Senior Python разработчика",
            InterviewType.DATA_SCIENTIST: "Data Scientist",
            InterviewType.PYTHON_TEAM_LEAD: "Python Team Lead"
        }

        return f"""Ты - опытный HR-специалист. Проанализируй ответы кандидата на позицию {level_names[interview_type]}.

Ответы кандидата:
{answers_text}

Дай развернутую обратную связь в формате:
🎯 **Сильные стороны:** (2-3 конкретных пункта)
⚠️ **Области для развития:** (2-3 конструктивных пункта)  
💡 **Рекомендации:** (конкретные шаги для улучшения)
📊 **Общая оценка:** (оценка от 1 до 10 с пояснением)

Будь конкретным, ссылайся на ответы кандидата."""

    def _send_message_to_gigachat(self, messages: List[Dict]) -> Optional[str]:
        """Отправляет сообщение в GigaChat API"""
        if not self._check_and_refresh_token():
            return None

        try:
            url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"

            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }

            data = {
                'model': 'GigaChat',
                'messages': messages,
                'temperature': 0.7,
                'max_tokens': 800
            }

            response = requests.post(url, headers=headers, json=data, verify=False, timeout=30)

            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                return None

        except Exception as e:
            print(f"💥 Ошибка GigaChat: {str(e)}")
            return None

    def start_interview(self, user_id: int, interview_type: InterviewType) -> str:
        """Начинает новое интервью с генерацией уникальных вопросов"""
        print(f"🎯 Генерация вопросов для {interview_type.value}...")
        questions = self._generate_questions(interview_type)

        self.interview_sessions[user_id] = {
            'state': InterviewState.IN_PROGRESS,
            'interview_type': interview_type,
            'current_question': 0,
            'questions': questions,
            'answers': [],
            'start_time': time.time()
        }

        first_question = questions[0]['question']
        type_name = self._get_interview_type_name(interview_type)
        return f"🎯 **Начинаем {type_name}!**\n\n💬 **Вопрос 1/5:**\n{first_question}"

    def process_answer(self, user_id: int, user_answer: str) -> str:
        """Обрабатывает ответ пользователя и возвращает следующий вопрос или фидбек"""
        if user_id not in self.interview_sessions:
            return "❌ Собеседование не начато. Используйте /interview чтобы начать."

        session = self.interview_sessions[user_id]

        # Сохраняем ответ
        current_q_index = session['current_question']
        session['answers'].append({
            'question': session['questions'][current_q_index]['question'],
            'answer': user_answer
        })

        # Переходим к следующему вопросу
        session['current_question'] += 1

        # Проверяем, закончилось ли интервью
        if session['current_question'] >= len(session['questions']):
            return self._generate_feedback(user_id)
        else:
            next_question = session['questions'][session['current_question']]['question']
            progress = f"({session['current_question'] + 1}/{len(session['questions'])})"
            return f"📝 **Вопрос {progress}:**\n{next_question}"

    def _generate_feedback(self, user_id: int) -> str:
        """Генерирует фидбек и сохраняет в историю"""
        session = self.interview_sessions[user_id]
        session['state'] = InterviewState.COMPLETED

        # Генерируем фидбек через GigaChat
        feedback = self._send_message_to_gigachat([
            {"role": "system", "content": self._get_feedback_prompt(
                session['interview_type'],
                session['answers']
            )}
        ])

        if not feedback:
            feedback = self._get_default_feedback(session['interview_type'])

        # Сохраняем в базу данных
        self._save_interview_history(user_id, session, feedback)

        # Очищаем сессию
        del self.interview_sessions[user_id]

        return f"✅ **Собеседование завершено!**\n\n{feedback}"

    def _save_interview_history(self, user_id: int, session: Dict, feedback: str):
        """Сохраняет историю собеседования в базу данных"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO interviews 
                (user_id, interview_type, questions, answers, feedback, score)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                session['interview_type'].value,
                json.dumps([q['question'] for q in session['questions']]),
                json.dumps(session['answers']),
                feedback,
                self._extract_score(feedback)  # Пытаемся извлечь оценку из фидбека
            ))
            self.conn.commit()
        except Exception as e:
            print(f"💥 Ошибка сохранения истории: {str(e)}")

    def _extract_score(self, feedback: str) -> int:
        """Пытается извлечь оценку из текста фидбека"""
        import re
        match = re.search(r'(\d+)/10', feedback)
        return int(match.group(1)) if match else 7

    def _get_default_feedback(self, interview_type: InterviewType) -> str:
        """Фидбек по умолчанию"""
        return """🎯 **Сильные стороны:** Хорошее понимание базовых концепций
⚠️ **Области для развития:** Рекомендуется углубить практический опыт
💡 **Рекомендации:** Реализовать несколько pet-проектов
📊 **Общая оценка:** 7/10 - хороший потенциал для развития"""

    def _get_interview_type_name(self, interview_type: InterviewType) -> str:
        """Возвращает читаемое название типа интервью"""
        names = {
            InterviewType.JUNIOR_PYTHON: "собеседование Junior Python разработчика",
            InterviewType.MIDDLE_PYTHON: "собеседование Middle Python разработчика",
            InterviewType.SENIOR_PYTHON: "собеседование Senior Python разработчика",
            InterviewType.DATA_SCIENTIST: "собеседование Data Scientist",
            InterviewType.PYTHON_TEAM_LEAD: "собеседование Python Team Lead"
        }
        return names.get(interview_type, "собеседование")

    def get_interview_history(self, user_id: int) -> List[Dict]:
        """Возвращает историю собеседований пользователя"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT interview_type, questions, feedback, score, created_at 
            FROM interviews 
            WHERE user_id = ? 
            ORDER BY created_at DESC
            LIMIT 10
        ''', (user_id,))

        history = []
        for row in cursor.fetchall():
            history.append({
                'type': row[0],
                'questions': json.loads(row[1]),
                'feedback': row[2],
                'score': row[3],
                'date': row[4]
            })

        return history

    def get_current_state(self, user_id: int) -> Optional[Dict]:
        return self.interview_sessions.get(user_id)

    def end_interview(self, user_id: int) -> str:
        if user_id in self.interview_sessions:
            del self.interview_sessions[user_id]
            return "❌ Собеседование прервано."
        return "❌ Активное собеседование не найдено."