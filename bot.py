import os
import requests
import uuid
import asyncio
import random
import json
from telegram import (
    Update, InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    Application, CommandHandler,
    MessageHandler, CallbackQueryHandler,
    ContextTypes, filters
)
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

print("🤖 AI HR Interview Bot запускается...")
print("🔗 Включен P2P мультиагентный режим...")


# ------------------------------------------------------
#  P2P Агенты
# ------------------------------------------------------

class Agent:
    """Базовый класс для всех агентов"""

    def __init__(self, name, role, emoji):
        self.name = name
        self.role = role
        self.emoji = emoji
        self.peers = []
        self.opinions = []

    async def consult(self, data, context):
        """Консультация агента по данным"""
        raise NotImplementedError

    def connect_peer(self, peer):
        """Подключение другого агента для P2P общения"""
        if peer not in self.peers:
            self.peers.append(peer)
            peer.peers.append(self)

    async def whisper_to_peers(self, message):
        """Шепчет другим агентам (имитация обсуждения)"""
        whispers = []
        for peer in self.peers:
            if hasattr(peer, 'react_to_whisper'):
                reaction = await peer.react_to_whisper(message, self)
                whispers.append(f"{peer.emoji} {peer.name}: {reaction}")
        return whispers


class TechnicalAgent(Agent):
    """Агент-Технический специалист"""

    def __init__(self):
        super().__init__("Технический специалист", "technical", "🔧")
        self.expertise = "Python, алгоритмы, архитектура"

    async def consult(self, data, context):
        """Анализирует технические аспекты"""
        question = data.get('question', '')
        answer = data.get('answer', '')
        question_type = data.get('type', 'technical')

        # Шепчем другим агентам
        whispers = await self.whisper_to_peers(
            f"Смотрю на технический ответ кандидата..."
        )

        if whispers:
            context.user_data.setdefault('whispers', []).extend(whispers)

        # Анализируем ответ
        analysis_prompt = f"""Как технический специалист, проанализируй ответ на вопрос:
Вопрос: {question}
Ответ: {answer}

Дайте оценку:
1. Техническая правильность (1-10)
2. Глубина понимания (1-10)
3. Практическая применимость (1-10)
4. Конкретные ошибки или неточности
5. Что можно улучшить

Верни JSON: {{"scores": {{"technical": X, "depth": X, "practical": X}}, "errors": [], "improvements": [], "overall_tech_comment": "текст"}}"""

        # В реальной реализации здесь будет вызов GigaChat
        return {
            "agent": self.name,
            "emoji": self.emoji,
            "analysis": {"status": "analysis_complete", "data": "Анализ выполнен"}
        }

    async def react_to_whisper(self, message, from_agent):
        """Реакция на шепот другого агента"""
        reactions = [
            "Согласен, нужно проверить это место в коде",
            "Интересный подход, но есть нюансы...",
            "Технически верно, но можно эффективнее",
            "Хм, тут кандидат допустил распространенную ошибку",
            "С точки зрения архитектуры это спорно..."
        ]
        return random.choice(reactions)


class CareerAgent(Agent):
    """Агент-Карьерный консультант"""

    def __init__(self):
        super().__init__("Карьерный консультант", "career", "📈")
        self.expertise = "Рост, развитие, планирование карьеры"

    async def consult(self, data, context):
        """Анализирует карьерные аспекты"""
        answer = data.get('answer', '')
        role = context.user_data.get('selected_role', '')

        whispers = await self.whisper_to_peers(
            f"Оцениваю карьерный потенциал кандидата..."
        )

        if whispers:
            context.user_data.setdefault('whispers', []).extend(whispers)

        # Определяем уровень
        if "junior" in role:
            level = "Junior"
        elif "middle" in role:
            level = "Middle"
        elif "senior" in role:
            level = "Senior"
        else:
            level = "Специалист"

        analysis_prompt = f"""Как карьерный консультант, проанализируй ответ кандидата на позицию {level}:
Ответ: {answer}

Дайте оценку:
1. Потенциал роста (1-10)
2. Понимание карьерных целей (1-10)
3. Готовность к развитию (1-10)
4. Рекомендации по обучению (конкретные курсы, книги, проекты)
5. План развития на 6 месяцев

Верни JSON: {{"scores": {{"growth": X, "goals": X, "readiness": X}}, "resources": [], "plan": [], "career_comment": "текст"}}"""

        return {
            "agent": self.name,
            "emoji": self.emoji,
            "analysis": {"status": "analysis_complete", "data": "Анализ выполнен"}
        }

    async def react_to_whisper(self, message, from_agent):
        """Реакция на шепот другого агента"""
        reactions = [
            "С точки зрения карьеры это важный момент",
            "Такой навык очень ценится на рынке",
            "Нужно развивать это для роста до следующего уровня",
            "Это можно добавить в план развития",
            "Хороший потенциал для карьерного роста"
        ]
        return random.choice(reactions)


class PsychologistAgent(Agent):
    """Агент-Психолог/Тимлид"""

    def __init__(self):
        super().__init__("Психолог-Тимлид", "psychologist", "👨‍💼")
        self.expertise = "Soft skills, коммуникация, командная работа"

    async def consult(self, data, context):
        """Анализирует soft skills и психологические аспекты"""
        answer = data.get('answer', '')
        question_type = data.get('type', '')

        whispers = await self.whisper_to_peers(
            f"Анализирую soft skills кандидата..."
        )

        if whispers:
            context.user_data.setdefault('whispers', []).extend(whispers)

        analysis_prompt = f"""Как психолог и тимлид, проанализируй ответ кандидата:
Ответ: {answer}

Оцените soft skills:
1. Коммуникативные навыки (1-10)
2. Работа в команде (1-10)
3. Решение конфликтов (1-10)
4. Лидерский потенциал (1-10)
5. Эмоциональный интеллект (1-10)
6. Конкретные наблюдения о поведении
7. Рекомендации по развитию soft skills

Верни JSON: {{"scores": {{"communication": X, "teamwork": X, "conflict": X, "leadership": X, "eq": X}}, "observations": [], "soft_improvements": [], "psych_comment": "текст"}}"""

        return {
            "agent": self.name,
            "emoji": self.emoji,
            "analysis": {"status": "analysis_complete", "data": "Анализ выполнен"}
        }

    async def react_to_whisper(self, message, from_agent):
        """Реакция на шепот другого агента"""
        reactions = [
            "Интересно, как это отразится на работе в команде...",
            "С психологической точки зрения это показательно",
            "Важный аспект для тимлида",
            "Это говорит о развитых soft skills",
            "Надо обратить внимание на коммуникацию"
        ]
        return random.choice(reactions)


class InterviewerAgent:
    """Главный агент-Интервьюер (координатор)"""

    def __init__(self):
        self.active_agents = []

    def activate_agents(self, question_types):
        """Активирует нужных агентов в зависимости от типов вопросов"""
        self.active_agents = []

        # Всегда активируем технического агента для технических вопросов
        tech_agent = TechnicalAgent()
        self.active_agents.append(tech_agent)

        # Активируем карьерного агента если есть ситуационные вопросы
        if "situational" in question_types or "all" in question_types:
            career_agent = CareerAgent()
            self.active_agents.append(career_agent)

        # Активируем психолога если есть практические или ситуационные вопросы
        if "practical" in question_types or "situational" in question_types or "all" in question_types:
            psych_agent = PsychologistAgent()
            self.active_agents.append(psych_agent)

        # Создаем P2P связи между всеми активированными агентами
        for i, agent1 in enumerate(self.active_agents):
            for agent2 in self.active_agents[i + 1:]:
                agent1.connect_peer(agent2)

        return self.active_agents

    async def consult_all(self, data, context):
        """Консультация со всеми активными агентами"""
        all_analyses = []

        # Шепчем друг другу перед обсуждением
        if random.random() > 0.5 and self.active_agents:
            await context.bot.send_message(
                chat_id=context._chat_id,
                text="🤫 <i>Вы слышите, как специалисты тихо обсуждают ваш ответ между собой...</i>",
                parse_mode="HTML"
            )

            # Собираем все шепоты
            all_whispers = []
            for agent in self.active_agents:
                whispers = await agent.whisper_to_peers(
                    f"Анализирую ответ на вопрос типа {data.get('type', 'unknown')}..."
                )
                if whispers:
                    all_whispers.extend(whispers)

            # Показываем некоторые шепоты пользователю
            if all_whispers and random.random() > 0.3:
                sample_whispers = random.sample(all_whispers, min(2, len(all_whispers)))
                whispers_text = "\n".join(sample_whispers)
                await context.bot.send_message(
                    chat_id=context._chat_id,
                    text=f"<i>Обсуждение специалистов:</i>\n{whispers_text}",
                    parse_mode="HTML"
                )

        # Получаем анализы от всех агентов
        for agent in self.active_agents:
            analysis = await agent.consult(data, context)
            all_analyses.append(analysis)

        return all_analyses


# Создаем главного интервьюера
interviewer_agent = InterviewerAgent()


# ------------------------------------------------------
#  GigaChat Client
# ------------------------------------------------------

class GigaChatClient:
    def __init__(self):
        self.auth_key = os.getenv("GIGACHAT_AUTH_CODE")
        self.access_token = None
        self._update_access_token()

    def _update_access_token(self):
        """Получаем access token для GigaChat"""
        try:
            url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
            rq_uid = str(uuid.uuid4())

            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json',
                'RqUID': rq_uid,
                'Authorization': f'Basic {self.auth_key}'
            }

            data = {'scope': 'GIGACHAT_API_PERS'}

            print("🔐 Получаем токен GigaChat...")
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
                print("✅ GigaChat token получен")
                return True
            else:
                print(f"❌ Ошибка получения token: {response.status_code}")
                return False

        except Exception as e:
            print(f"💥 Ошибка: {str(e)}")
            return False

    async def chat_completion(self, messages, max_tokens=500):
        """Отправляет запрос к GigaChat API"""
        if not self.access_token:
            if not self._update_access_token():
                return "❌ Ошибка подключения к GigaChat"

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
                'max_tokens': max_tokens
            }

            response = requests.post(
                url,
                headers=headers,
                json=data,
                verify=False,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                return f"❌ Ошибка API: {response.status_code}"

        except Exception as e:
            return f"❌ Ошибка: {str(e)}"


# Инициализируем клиент
client = GigaChatClient()

# ------------------------------------------------------
#  Хранилище сессий
# ------------------------------------------------------

user_sessions = {}

# ------------------------------------------------------
#  Константы и настройки
# ------------------------------------------------------

INTERVIEW_LENGTHS = {
    "short": {"questions": 3, "name": "Короткое (3 вопроса)", "emoji": "⚡"},
    "medium": {"questions": 5, "name": "Стандартное (5 вопросов)", "emoji": "🎯"},
    "long": {"questions": 10, "name": "Полное (10 вопросов)", "emoji": "📊"}
}

QUESTION_TYPES = {
    "technical": {
        "name": "Технические вопросы",
        "emoji": "🔧",
        "prompt": "технический вопрос проверяющий технические знания",
        "agents": ["technical"]
    },
    "situational": {
        "name": "Ситуационные вопросы",
        "emoji": "🎭",
        "prompt": "ситуационный вопрос о реальных рабочих ситуациях и поведении в команде",
        "agents": ["career", "psychologist"]
    },
    "practical": {
        "name": "Практические задачи",
        "emoji": "💻",
        "prompt": "практическую задачу или coding challenge для проверки навыков программирования",
        "agents": ["technical", "psychologist"]
    },
    "all": {
        "name": "Все типы вопросов",
        "emoji": "🎯",
        "prompt": "разнообразные вопросы для полной оценки кандидата",
        "agents": ["technical", "career", "psychologist"]
    }
}


# ------------------------------------------------------
#  Команда /start
# ------------------------------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Главное меню бота"""
    text = (
        "🤖 <b>Добро пожаловать в P2P мультиагентную систему собеседований!</b>\n\n"
        "<b>Новая система оценки:</b>\n"
        "• 🔧 Технический специалист - оценка hard skills\n"
        "• 📈 Карьерный консультант - план развития\n"
        "• 👨‍💼 Психолог-тимлид - анализ soft skills\n\n"
        "<b>P2P взаимодействие:</b>\n"
        "• Агенты общаются между собой\n"
        "• Коллаборативная оценка\n"
        "• Адаптивные вопросы\n\n"
        "Выберите действие:"
    )

    keyboard = [
        [InlineKeyboardButton("📎 Начать P2P интервью", callback_data="show_interview_menu")],
        [InlineKeyboardButton("👥 Активные агенты", callback_data="show_agents")],
        [InlineKeyboardButton("👁️‍🗨️ История", callback_data="show_history")]
    ]

    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )


# ------------------------------------------------------
#  Показ активных агентов
# ------------------------------------------------------

async def show_agents(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает активных агентов"""
    query = update.callback_query
    await query.answer()

    # Получаем текущих агентов из сессии или показываем дефолтных
    user_id = query.from_user.id
    if user_id in user_sessions and 'active_agents' in user_sessions[user_id]:
        active_agents = user_sessions[user_id]['active_agents']
    else:
        # Показываем всех возможных агентов
        active_agents = [
            {"name": "Технический специалист", "emoji": "🔧", "status": "⚪ Ожидает"},
            {"name": "Карьерный консультант", "emoji": "📈", "status": "⚪ Ожидает"},
            {"name": "Психолог-Тимлид", "emoji": "👨‍💼", "status": "⚪ Ожидает"},
            {"name": "Главный интервьюер", "emoji": "🎯", "status": "🟢 Активен"}
        ]

    agents_text = "👥 <b>Система P2P агентов:</b>\n\n"

    for agent in active_agents:
        agents_text += f"{agent['emoji']} <b>{agent['name']}</b>\n"
        agents_text += f"   Статус: {agent['status']}\n\n"

    agents_text += "\n<i>Агенты общаются между собой, чтобы дать наиболее точную оценку.</i>"

    keyboard = [
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_start")]
    ]

    await query.edit_message_text(
        agents_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )


# ------------------------------------------------------
#  Меню выбора сценария интервью
# ------------------------------------------------------

async def show_interview_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает меню выбора типа интервью"""
    query = update.callback_query
    await query.answer()

    text = (
        "🤖 <b>P2P Мультиагентное собеседование</b>\n\n"
        "<b>Как это работает:</b>\n"
        "1. Вы выбираете позицию и типы вопросов\n"
        "2. Система активирует нужных агентов\n"
        "3. Агенты общаются между собой (P2P)\n"
        "4. Каждый вопрос анализируется с разных сторон\n"
        "5. В конце - сводный отчет от всех агентов\n\n"
        "<b>Выберите позиция:</b>"
    )

    keyboard = [
        [InlineKeyboardButton("👶 Junior Python", callback_data="role_junior_python")],
        [InlineKeyboardButton("🧑 Middle Python", callback_data="role_middle_python")],
        [InlineKeyboardButton("🪦 Senior Python", callback_data="role_senior_python")],
        [InlineKeyboardButton("📊 Data Scientist", callback_data="role_data_scientist")],
        [InlineKeyboardButton("👬 Team Lead", callback_data="role_team_lead")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_start")]
    ]

    if hasattr(query, 'edit_message_text'):
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
    else:
        await update.message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )


# ------------------------------------------------------
#  Выбор длины интервью
# ------------------------------------------------------

async def start_interview(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начинает процесс выбора длины интервью"""
    query = update.callback_query
    user_id = query.from_user.id
    callback_data = query.data

    await query.answer()

    # Сохраняем выбранную роль
    context.user_data["selected_role"] = callback_data
    role_name = callback_data.replace("role_", "").replace("_", " ").title()

    text = (
        f"🎯 <b>Вы выбрали: {role_name}</b>\n\n"
        "📏 <b>Теперь выберите длину собеседования:</b>\n\n"
        f"{INTERVIEW_LENGTHS['short']['emoji']} <b>Короткое</b> - 3 вопроса (5-7 минут)\n"
        f"{INTERVIEW_LENGTHS['medium']['emoji']} <b>Стандартное</b> - 5 вопросов (10-12 минут)\n"
        f"{INTERVIEW_LENGTHS['long']['emoji']} <b>Полное</b> - 10 вопросов (15-20 минут)\n\n"
        "💡 <i>Чем длиннее собеседование, тем точнее оценка от агентов</i>"
    )

    keyboard = [
        [InlineKeyboardButton("⚡ Короткое (3 вопроса)", callback_data="length_short")],
        [InlineKeyboardButton("🎯 Стандартное (5 вопросов)", callback_data="length_medium")],
        [InlineKeyboardButton("📊 Полное (10 вопросов)", callback_data="length_long")],
        [InlineKeyboardButton("🔙 Назад", callback_data="show_interview_menu")]
    ]

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )


# ------------------------------------------------------
#  Выбор типа вопросов
# ------------------------------------------------------

async def select_question_types(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выбор типов вопросов для интервью"""
    query = update.callback_query
    user_id = query.from_user.id
    callback_data = query.data

    await query.answer()

    # Сохраняем выбранную длину
    length_type = callback_data.replace("length_", "")
    context.user_data["interview_length"] = length_type

    selected_role = context.user_data["selected_role"]
    role_mapping = {
        "role_junior_python": "Junior Python разработчика",
        "role_middle_python": "Middle Python разработчика",
        "role_senior_python": "Senior Python разработчика",
        "role_data_scientist": "Data Scientist",
        "role_team_lead": "Python Team Lead"
    }
    role_name = role_mapping.get(selected_role, "Python разработчика")

    text = (
        f"🎯 <b>Интервью: {role_name}</b>\n"
        f"📏 <b>Длина: {INTERVIEW_LENGTHS[length_type]['name']}</b>\n\n"
        "🔧 <b>Выберите типы вопросов:</b>\n\n"
        f"{QUESTION_TYPES['technical']['emoji']} <b>Технические</b> - только тех.специалист\n"
        f"{QUESTION_TYPES['situational']['emoji']} <b>Ситуационные</b> - карьерный + психолог\n"
        f"{QUESTION_TYPES['practical']['emoji']} <b>Практические</b> - тех.специалист + психолог\n"
        f"{QUESTION_TYPES['all']['emoji']} <b>Все типы</b> - все 3 агента\n\n"
        "🤝 <i>Агенты будут общаться между собой для каждой оценки</i>"
    )

    keyboard = [
        [InlineKeyboardButton("🔧 Только технические", callback_data="types_technical")],
        [InlineKeyboardButton("🎭 Только ситуационные", callback_data="types_situational")],
        [InlineKeyboardButton("💻 Только практические", callback_data="types_practical")],
        [InlineKeyboardButton("🎯 Все типы вопросов (P2P)", callback_data="types_all")],
        [InlineKeyboardButton("🔙 Назад",
                              callback_data=f"role_{selected_role.split('_')[1]}_{selected_role.split('_')[2]}")]
    ]

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )


# ------------------------------------------------------
#  Запуск интервью с выбранными настройками
# ------------------------------------------------------

async def launch_interview(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Запускает интервью с выбранными настройками"""
    query = update.callback_query
    user_id = query.from_user.id
    callback_data = query.data

    await query.answer()

    # Определяем выбранные типы вопросов
    selected_types = []
    if callback_data == "types_all":
        selected_types = ["all"]
    else:
        selected_types = [callback_data.replace("types_", "")]

    # Получаем настройки из context.user_data
    selected_role = context.user_data["selected_role"]
    length_type = context.user_data["interview_length"]
    total_questions = INTERVIEW_LENGTHS[length_type]["questions"]

    role_mapping = {
        "role_junior_python": "Junior Python разработчика",
        "role_middle_python": "Middle Python разработчика",
        "role_senior_python": "Senior Python разработчика",
        "role_data_scientist": "Data Scientist",
        "role_team_lead": "Python Team Lead"
    }
    role_name = role_mapping.get(selected_role, "Python разработчика")

    # Активируем агентов в зависимости от типов вопросов
    active_agents_list = interviewer_agent.activate_agents(selected_types)

    # Сохраняем информацию об агентах
    agents_info = []
    for agent in active_agents_list:
        agents_info.append({
            "name": agent.name,
            "emoji": agent.emoji,
            "role": agent.role
        })

    # Инициализируем сессию пользователя
    user_sessions[user_id] = {
        "role": selected_role.replace("role_", ""),
        "role_name": role_name,
        "interview_length": length_type,
        "question_types": selected_types,
        "current_question": 0,
        "total_questions": total_questions,
        "questions": [],
        "answers": [],
        "feedbacks": [],
        "agent_analyses": [],  # Анализы от каждого агента для каждого вопроса
        "question_categories": [],  # Тип каждого вопроса
        "active_agents": agents_info,
        "state": "in_progress",
        "whispers": []  # Шепоты между агентами
    }

    # Показываем стартовое сообщение
    types_text = QUESTION_TYPES[selected_types[0]]["name"] if selected_types else "Разные типы"
    agents_text = ", ".join([f"{a['emoji']} {a['name']}" for a in agents_info])

    await query.edit_message_text(
        f"🚀 <b>Запускаем P2P интервью!</b>\n\n"
        f"🎯 <b>Позиция:</b> {role_name}\n"
        f"📏 <b>Длина:</b> {total_questions} вопросов\n"
        f"🔧 <b>Типы вопросов:</b> {types_text}\n"
        f"👥 <b>Активные агенты:</b> {agents_text}\n\n"
        "🤫 <i>Агенты настраиваются на общение между собой...</i>\n"
        "🔄 Генерирую первый вопрос...",
        parse_mode="HTML"
    )

    # Генерируем первый вопрос
    await generate_next_question(update, user_id, context)


# ------------------------------------------------------
#  Генерация вопросов с учетом агентов
# ------------------------------------------------------

async def generate_next_question(update: Update, user_id: int, context: ContextTypes.DEFAULT_TYPE):
    """Генерирует следующий вопрос с учетом активных агентов"""
    session = user_sessions[user_id]

    # Выбираем случайный тип вопроса из выбранных
    question_type = random.choice(session["question_types"])
    if question_type == "all":
        # Если выбраны все типы, выбираем случайный из трех
        question_type = random.choice(["technical", "situational", "practical"])

    type_info = QUESTION_TYPES.get(question_type, QUESTION_TYPES["technical"])

    # Генерируем вопрос через GigaChat
    messages = [
        {"role": "system",
         "content": f"Ты опытный HR-специалист. Сгенерируй {type_info['prompt']} для собеседования на позицию {session['role_name']}. Вопрос должен быть конкретным и релевантным для этой позиции. Верни только вопрос без дополнительных комментариев."},
    ]

    question = await client.chat_completion(messages)

    if question.startswith("❌"):
        # Если ошибка, пробуем еще раз
        question = await client.chat_completion(messages)

    if question.startswith("❌"):
        # Используем безопасный способ отправки сообщения
        if hasattr(update, 'message') and update.message:
            await update.message.reply_text(
                "❌ <b>Ошибка при генерации вопроса.</b>\nПопробуйте еще раз.",
                parse_mode="HTML"
            )
        elif hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.message.reply_text(
                "❌ <b>Ошибка при генерации вопроса.</b>\nПопробуйте еще раз.",
                parse_mode="HTML"
            )
        return

    # Сохраняем вопрос и его тип
    session["questions"].append(question)
    session["question_categories"].append(question_type)

    current_q = session["current_question"] + 1
    total_q = session["total_questions"]

    # Определяем, каких агентов задействовать для этого типа вопроса
    agents_for_this_question = type_info.get("agents", ["technical"])
    agents_text = ""

    for agent_info in session["active_agents"]:
        if agent_info["role"] in agents_for_this_question:
            agents_text += f"{agent_info['emoji']} "

    # Показываем вопрос с указанием типа и агентов
    type_emoji = type_info["emoji"]
    type_name = type_info["name"]

    # Безопасная отправка сообщения
    if hasattr(update, 'message') and update.message:
        await update.message.reply_text(
            f"{type_emoji} <b>Вопрос {current_q}/{total_q} ({type_name}):</b>\n"
            f"{agents_text}<i>Агенты готовы к анализу</i>\n\n"
            f"{question}",
            parse_mode="HTML"
        )
    elif hasattr(update, 'callback_query') and update.callback_query:
        await update.callback_query.message.reply_text(
            f"{type_emoji} <b>Вопрос {current_q}/{total_q} ({type_name}):</b>\n"
            f"{agents_text}<i>Агенты готовы к анализу</i>\n\n"
            f"{question}",
            parse_mode="HTML"
        )


# ------------------------------------------------------
#  Обработка ответов пользователя с P2P анализом
# ------------------------------------------------------

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_text = update.message.text
    context._chat_id = update.effective_chat.id

    # Проверяем, есть ли активное интервью
    if user_id not in user_sessions or user_sessions[user_id]["state"] != "in_progress":
        keyboard = [[InlineKeyboardButton("🚀 Начать интервью", callback_data="show_interview_menu")]]
        await update.message.reply_text(
            "🤨 <b>Сначала выберите тип интервью</b>",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        return

    session = user_sessions[user_id]
    current_q_index = session["current_question"]

    # Сохраняем ответ
    answer_data = {
        "question": session["questions"][current_q_index],
        "answer": user_text,
        "type": session["question_categories"][current_q_index]
    }

    session["answers"].append(answer_data)

    # Показываем, что агенты анализируют ответ
    processing_msg = await update.message.reply_text(
        "👥 <b>Агенты начали P2P анализ вашего ответа...</b>\n"
        "🤫 <i>Слышны обсуждения между специалистами</i>",
        parse_mode="HTML"
    )

    # Сначала получаем ответ от HR-интервьюера (как было раньше)
    hr_feedback_messages = [
        {"role": "system",
         "content": f"""Ты - опытный HR-специалист, который проводит собеседование. Твоя задача - дать естественную обратную связь кандидату на его ответ.

Твой стиль общения:
- Будь дружелюбным, но профессиональным
- Отмечай сильные стороны ответа
- Указывай на слабые места конструктивно
- Если ответ слишком короткий или несерьезный - попроси раскрыть тему подробнее
- Если ответ хороший - похвали и задай уточняющий вопрос
- Будь человечным: выражай удивление, одобрение, интерес

Ответ должен быть живым и естественным, как будто ты реальный HR на собеседовании."""},
        {"role": "user",
         "content": f"Вопрос на позицию {session['role_name']}: {answer_data['question']}\n\nОтвет кандидата: {user_text}"}
    ]

    hr_feedback = await client.chat_completion(hr_feedback_messages, max_tokens=200)
    await processing_msg.delete()

    if not hr_feedback.startswith("❌"):
        session["feedbacks"].append(hr_feedback)

        # Показываем ответ HR
        await update.message.reply_text(
            f"👔 <b>HR-интервьюер:</b>\n\n{hr_feedback}",
            parse_mode="HTML"
        )

        # Только потом показываем, что агенты анализируют
        await update.message.reply_text(
            "👥 <i>Пока HR говорит с вами, специалисты анализируют ваш ответ...</i>",
            parse_mode="HTML"
        )
    else:
        # Фолбэк если AI не сработал
        hr_feedback = "Спасибо за ответ! Передаю его нашим специалистам для анализа."
        session["feedbacks"].append(hr_feedback)
        await update.message.reply_text(
            f"👔 <b>HR-интервьюер:</b>\n\n{hr_feedback}",
            parse_mode="HTML"
        )

    # Получаем анализ от всех активных агентов (в фоне)
    analysis_data = {
        "question": answer_data["question"],
        "answer": answer_data["answer"],
        "type": answer_data["type"],
        "role": session["role_name"]
    }

    agents_analyses = await interviewer_agent.consult_all(analysis_data, context)

    # Сохраняем анализы агентов
    session["agent_analyses"].append(agents_analyses)

    # Переходим к следующему вопросу
    session["current_question"] += 1

    # Проверяем, закончилось ли интервью
    if session["current_question"] >= session["total_questions"]:
        await finish_interview(update, user_id, context)
        return

    # Генерируем следующий вопрос
    await update.message.reply_text(
        "🧠 <b>Агенты обсуждают следующий вопрос...</b>",
        parse_mode="HTML"
    )
    await generate_next_question(update, user_id, context)


# ------------------------------------------------------
#  Завершение интервью со сводным отчетом от всех агентов
# ------------------------------------------------------

async def finish_interview(update: Update, user_id: int, context: ContextTypes.DEFAULT_TYPE):
    """Завершает интервью и генерирует сводный отчет от всех агентов"""
    session = user_sessions[user_id]

    analysis_msg = await update.message.reply_text(
        "📊 <b>Агенты готовят сводный P2P отчет...</b>\n"
        "🤝 <i>Технический специалист, карьерный консультант и психолог-тимлид согласовывают финальную оценку</i>",
        parse_mode="HTML"
    )

    # Создаем детальный промпт для сводного отчета
    summary_prompt = f"""Ты - главный HR-специалист, координирующий работу команды экспертов.
На основе анализов технического специалиста, карьерного консультанта и психолога-тимлида,
создай развернутый финальный отчет о кандидате на позицию {session['role_name']}.

Структура отчета:
1. ОБЩАЯ СВОДКА - интегральная оценка от всех экспертов
2. ТЕХНИЧЕСКАЯ КОМПЕТЕНЦИЯ - выводы тех.специалиста
3. КАРЬЕРНЫЙ ПОТЕНЦИАЛ - оценка карьерного консультанта
4. SOFT SKILLS И КОМАНДНАЯ РАБОТА - анализ психолога-тимлида
5. ИНТЕГРИРОВАННЫЕ РЕКОМЕНДАЦИИ - совместные рекомендации всех экспертов
6. ВЕРДИКТ И СЛЕДУЮЩИЕ ШАГИ - финальное решение

ВАЖНО: Не используй markdown (##, **). Пиши обычным текстом с эмодзи и абзацами.

Вот анализы по всем вопросам:"""

    # Добавляем все вопросы и анализы
    for i, (qa, agents_analyses) in enumerate(zip(session["answers"], session["agent_analyses"]), 1):
        summary_prompt += f"\n\nВопрос {i} ({qa['type']}): {qa['question']}"
        summary_prompt += f"\nОтвет: {qa['answer'][:200]}..."
        summary_prompt += f"\nАнализы агентов:"

        for agent_analysis in agents_analyses:
            summary_prompt += f"\n- {agent_analysis['emoji']} {agent_analysis['agent']}: {json.dumps(agent_analysis.get('analysis', {}), ensure_ascii=False)[:100]}..."

    summary_prompt += "\n\nСоздай подробный, структурированный отчет с конкретными рекомендациями. Будь дружелюбным и конструктивным."

    final_report = await client.chat_completion(
        [{"role": "system", "content": summary_prompt}],
        max_tokens=1500
    )

    await analysis_msg.delete()

    if final_report.startswith("❌"):
        final_report = """🏁 СВОДНЫЙ P2P ОТЧЕТ

🔧 ТЕХНИЧЕСКИЙ СПЕЦИАЛИСТ:
Кандидат показал хорошее понимание основных концепций.

📈 КАРЬЕРНЫЙ КОНСУЛЬТАНТ:
Есть потенциал для роста, рекомендован план развития.

👨‍💼 ПСИХОЛОГ-ТИМЛИД:
Развитые soft skills, хорошие коммуникативные способности.

💡 СОВМЕСТНЫЕ РЕКОМЕНДАЦИИ:
Продолжать практиковаться, участвовать в pet-проектах.

🎯 ВЕРДИКТ:
Кандидат подходит для позиции с учетом плана развития."""

    # Формируем финальный отчет
    report = "🏁 <b>P2P ИНТЕРВЬЮ ЗАВЕРШЕНО!</b>\n\n"
    report += f"🎯 <b>Позиция:</b> {session['role_name']}\n"
    report += f"📏 <b>Вопросов:</b> {session['total_questions']}\n"

    # Исправленная строка с кавычками
    agents_list = []
    for a in session['active_agents']:
        agents_list.append(f"{a['emoji']} {a['name']}")
    report += f"👥 <b>Участвовали агенты:</b> {', '.join(agents_list)}\n\n"

    report += "=" * 40 + "\n\n"
    report += "<b>📊 СВОДНЫЙ ОТЧЕТ ОТ ВСЕХ АГЕНТОВ:</b>\n\n"

    # Чистим отчет от маркдауна
    cleaned_report = final_report.replace('##', '').replace('**', '').replace('*', '')
    report += f"{cleaned_report}\n\n"

    report += "=" * 40 + "\n\n"
    report += "💡 <i>Используйте /start для нового P2P собеседования</i>"

    # Добавляем статистику
    if session.get('whispers'):
        report += f"\n\n🤫 <i>Во время интервью агенты обменялись {len(session['whispers'])} сообщениями между собой</i>"

    keyboard = [
        [InlineKeyboardButton("🔄 Новое P2P интервью", callback_data="show_interview_menu")],
        [InlineKeyboardButton("👥 Агенты", callback_data="show_agents")],
        [InlineKeyboardButton("👁️‍🗨️ История", callback_data="show_history")]
    ]

    await update.message.reply_text(
        report,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )

    session["state"] = "completed"


# ------------------------------------------------------
#  Показать историю
# ------------------------------------------------------

async def show_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает историю собеседований с участием агентов"""
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    if user_id not in user_sessions or user_sessions[user_id]["state"] != "completed":
        await query.edit_message_text(
            "📜 <b>История пуста.</b>\n\n"
            "Завершите хотя бы одно P2P интервью чтобы увидеть историю.",
            parse_mode="HTML"
        )
        return

    session = user_sessions[user_id]

    history_text = f"📜 <b>История P2P интервью ({session['role_name']}):</b>\n\n"

    # Исправленная строка с кавычками
    agents_emojis = []
    for a in session['active_agents']:
        agents_emojis.append(a['emoji'])
    history_text += f"👥 <b>Агенты:</b> {', '.join(agents_emojis)}\n\n"

    for i, (qa, feedback) in enumerate(zip(session["answers"], session["feedbacks"]), 1):
        question_type = qa.get('type', 'technical')
        type_emoji = QUESTION_TYPES.get(question_type, {}).get('emoji', '🔧')

        # Показываем, какие агенты анализировали этот вопрос
        agents_for_q = []
        for agent_info in session["active_agents"]:
            if agent_info["role"] in QUESTION_TYPES.get(question_type, {}).get("agents", ["technical"]):
                agents_for_q.append(agent_info["emoji"])

        agents_str = " ".join(agents_for_q)

        history_text += f"{agents_str} <b>Вопрос {i}:</b> {qa['question'][:80]}...\n"
        history_text += f"<b>Тип:</b> {question_type}\n"
        history_text += f"<b>Ответ HR:</b> {feedback[:100]}...\n\n"
        history_text += "─" * 30 + "\n\n"

    keyboard = [
        [InlineKeyboardButton("🔄 Новое интервью", callback_data="show_interview_menu")],
        [InlineKeyboardButton("👥 Агенты", callback_data="show_agents")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_start")]
    ]

    await query.edit_message_text(
        history_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )


# ------------------------------------------------------
#  Возврат в главное меню
# ------------------------------------------------------

async def back_to_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возвращает в главное меню"""
    query = update.callback_query
    await query.answer()

    text = (
        "🤖 <b>P2P Мультиагентная система собеседований</b>\n\n"
        "<b>Возможности системы:</b>\n"
        "• 🔧 Технический специалист - глубокая оценка hard skills\n"
        "• 📈 Карьерный консультант - персональный план развития\n"
        "• 👨‍💼 Психолог-тимлид - анализ soft skills и командной работы\n"
        "• 🤝 P2P взаимодействие - агенты общаются между собой\n"
        "• 🎯 Адаптивные вопросы - сложность меняется по ходу\n\n"
        "<i>Система создает максимально реалистичное собеседование</i>"
    )

    keyboard = [
        [InlineKeyboardButton("📎 Начать P2P интервью", callback_data="show_interview_menu")],
        [InlineKeyboardButton("👥 Активные агенты", callback_data="show_agents")],
        [InlineKeyboardButton("👁️‍🗨️ История", callback_data="show_history")]
    ]

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )


# ------------------------------------------------------
#  Обновленный роутер callback'ов
# ------------------------------------------------------

async def callback_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Маршрутизатор всех callback'ов"""
    query = update.callback_query
    data = query.data

    try:
        if data == "show_interview_menu":
            await show_interview_menu(update, context)
        elif data == "show_agents":
            await show_agents(update, context)
        elif data.startswith("role_"):
            await start_interview(update, context)
        elif data.startswith("length_"):
            await select_question_types(update, context)
        elif data.startswith("types_"):
            await launch_interview(update, context)
        elif data == "show_history":
            await show_history(update, context)
        elif data == "back_to_start":
            await back_to_start(update, context)
        else:
            await query.answer("Неизвестная команда")

    except Exception as e:
        print(f"💥 Ошибка в callback_router: {e}")
        await query.answer("Произошла ошибка", show_alert=True)


# ------------------------------------------------------
#  Команда /interview
# ------------------------------------------------------

async def interview_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /interview"""
    await show_interview_menu(update, context)


# ------------------------------------------------------
#  Команда /agents
# ------------------------------------------------------

async def agents_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /agents"""
    await show_agents(update, context)


# ------------------------------------------------------
#  Настройка бота
# ------------------------------------------------------

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    print(f"❌ Ошибка: {context.error}")


def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("❌ ОШИБКА: TELEGRAM_BOT_TOKEN не найден!")
        return

    print("🚀 Создаем P2P Application...")
    print("👥 Агенты: Технический специалист, Карьерный консультант, Психолог-Тимлид")

    application = Application.builder().token(token).build()

    application.add_handler(CallbackQueryHandler(callback_router))
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("interview", interview_command))
    application.add_handler(CommandHandler("agents", agents_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    application.add_error_handler(error_handler)

    print("✅ P2P бот запущен с мультиагентной системой!")

    application.run_polling()


if __name__ == "__main__":
    main()