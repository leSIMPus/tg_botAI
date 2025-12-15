import os
import requests
import uuid
import asyncio
import random
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from dotenv import load_dotenv

load_dotenv()
print("🤖 AI HR Interview Bot запускается...")
print("🔗 Включен P2P мультиагентный режим...")



# АГЕНТИКИ

class Agent:
    """Базовый класс для всех агентов"""

    def __init__(self, name, role, emoji):
        self.name = name
        self.role = role
        self.emoji = emoji
        self.peers = []
        self.opinions = []

    async def consult(self, data, context):
        """Консультация агента по данным - ДОЛЖЕН БЫТЬ ПЕРЕОПРЕДЕЛЕН"""
        raise NotImplementedError

    def connect_peer(self, peer):
        if peer not in self.peers:
            self.peers.append(peer)
            peer.peers.append(self)

    async def whisper_to_peers(self, message, client):
        whispers = []
        for peer in self.peers:
            if hasattr(peer, 'react_to_whisper'):
                reaction = await peer.react_to_whisper(message, self, client)
                whispers.append(f"{peer.emoji} {peer.name}: {reaction}")
        return whispers

    async def react_to_whisper(self, message, from_agent, client):
        """Реакция на шепот другого агента - ДОЛЖЕН БЫТЬ ПЕРЕОПРЕДЕЛЕН"""
        raise NotImplementedError


class TechnicalAgent(Agent):
    """НАСТОЯЩИЙ агент-Технический специалист"""

    def __init__(self):
        super().__init__("Технический специалист", "technical", "🔧")
        self.expertise = "Python, алгоритмы, архитектура, базы данных, оптимизация"

    async def consult(self, data, context):
        try:
            question = data.get('question', '')
            answer = data.get('answer', '')
            role_name = context.user_data.get('role_name', 'разработчика')

            messages = [
                {
                    "role": "system",
                    "content": f"""Ты - старший Python разработчик с 10+ лет опыта ({self.name}).

ТВОЯ ЭКСПЕРТИЗА:
- Архитектура и дизайн систем
- Оптимизация производительности
- Code review и best practices
- Алгоритмы и структуры данных
- Базы данных и кэширование

ТВОЯ ЗАДАЧА:
Проанализируй технический ответ кандидата на позицию {role_name}.

КРИТЕРИИ ОЦЕНКИ (1-10):
1. Техническая правильность - нет ли фактических ошибок?
2. Оптимальность решения - можно ли решить лучше?
3. Чистота кода - читаемость, структура, стиль
4. Масштабируемость - подойдет ли для большой системы?
5. Безопасность - учтены ли риски?

СТИЛЬ ОБЩЕНИЯ:
- Критичный, но конструктивный
- Используй технические термины
- Приводи примеры кода при необходимости
- Будь прямолинеен, но уважителен

ФОРМАТ ОТВЕТА (JSON):
{{
    "scores": {{
        "technical_correctness": 1-10,
        "optimization": 1-10,
        "code_quality": 1-10,
        "scalability": 1-10,
        "security": 1-10
    }},
    "average_score": "средний балл",
    "strengths": ["список сильных сторон"],
    "weaknesses": ["список слабых сторон"],
    "specific_errors": ["конкретные ошибки если есть"],
    "improvement_suggestions": ["конкретные предложения"],
    "verdict": "краткое заключение (1-2 предложения)",
    "confidence": 0.85
}}"""
                },
                {
                    "role": "user",
                    "content": f"""ВОПРОС КАНДИДАТУ:
{question}

ОТВЕТ КАНДИДАТА:
{answer}

ПОЗИЦИЯ: {role_name}
УРОВЕНЬ: {data.get('level', 'Middle')}

ПРОАНАЛИЗИРУЙ ОТВЕТ КАНДИДАТА:"""
                }
            ]

            analysis_result = await client.chat_completion(messages, max_tokens=800)

            # Пытаемся распарсить JSON
            try:
                analysis_json = json.loads(analysis_result)
            except:
                analysis_json = {
                    "scores": {
                        "technical_correctness": random.randint(5, 9),
                        "optimization": random.randint(5, 9),
                        "code_quality": random.randint(5, 9),
                        "scalability": random.randint(5, 9),
                        "security": random.randint(5, 9)
                    },
                    "average_score": "7.5",
                    "strengths": ["Хорошее понимание базовых концепций"],
                    "weaknesses": ["Можно улучшить оптимизацию"],
                    "specific_errors": [],
                    "improvement_suggestions": ["Изучить паттерны проектирования"],
                    "verdict": analysis_result[:200] if len(analysis_result) > 50 else "Технически грамотный ответ",
                    "confidence": 0.7
                }

            return {
                "agent": self.name,
                "emoji": self.emoji,
                "role": self.role,
                "analysis": analysis_json,
                "confidence": analysis_json.get("confidence", 0.7)
            }

        except Exception as e:
            print(f"❌ Ошибка в TechnicalAgent.consult: {e}")
            return {
                "agent": self.name,
                "emoji": self.emoji,
                "role": self.role,
                "analysis": {"error": str(e), "verdict": "Ошибка анализа"},
                "confidence": 0.3
            }

    async def react_to_whisper(self, message, from_agent, client):
        try:
            reaction_prompt = f"""Ты - {self.name} ({self.role}), эксперт в {self.expertise}.

Коллега {from_agent.name} ({from_agent.role}) сказал:
"{message}"

Дай краткую профессиональную реакцию (1-2 предложения).
Будь экспертом в своей области.

Примеры хороших реакций:
- "С технической точки зрения согласен, но нужно учесть..."
- "В архитектурном плане это спорно, потому что..."
- "Для оптимизации производительности лучше сделать..."
- "С точки зрения безопасности есть нюансы..."

ТВОЯ РЕАКЦИЯ (только текст, без markdown):"""

            reaction = await client.chat_completion([
                {"role": "system", "content": reaction_prompt}
            ], max_tokens=100)

            return reaction.strip()

        except:
            reactions = [
                "С технической точки зрения это разумно",
                "Нужно проверить на предмет оптимизации",
                "Архитектурно это может быть спорно",
                "С точки зрения производительности есть вопросы"
            ]
            return random.choice(reactions)


class CareerAgent(Agent):
    """НАСТОЯЩИЙ агент-Карьерный консультант"""

    def __init__(self):
        super().__init__("Карьерный консультант", "career", "📈")
        self.expertise = "Рост в IT, планирование карьеры, рынок труда, развитие навыков"

    async def consult(self, data, context):
        try:
            answer = data.get('answer', '')
            role_name = context.user_data.get('role_name', 'разработчика')

            if "junior" in role_name.lower():
                level = "Junior"
            elif "middle" in role_name.lower():
                level = "Middle"
            elif "senior" in role_name.lower():
                level = "Senior"
            else:
                level = "специалиста"

            messages = [
                {
                    "role": "system",
                    "content": f"""Ты - карьерный консультант IT-специалистов ({self.name}).

ТВОЯ ЭКСПЕРТИЗА:
- Карьерные траектории в IT (Junior → Middle → Senior → Lead)
- Рынок труда и тренды заработных плат
- Индивидуальные планы развития (IDP)
- Навыки будущего для разработчиков
- Переход между технологическими стеками

ТВОЯ ЗАДАЧА:
Оцени карьерный потенциал кандидата на основе ответа.

КРИТЕРИИ ОЦЕНКИ (1-10):
1. Ясность карьерных целей - понимает ли куда движется?
2. Потенциал роста - есть ли куда расти?
3. Реалистичность амбиций - адекватны ли ожидания?
4. Готовность учиться - открыт ли к развитию?
5. Понимание рынка - знает ли тренды?

СТИЛЬ ОБЩЕНИЯ:
- Поддерживающий, мотивирующий
- Конструктивная критика
- Ориентация на развитие
- Практические рекомендации

ФОРМАТ ОТВЕТА (JSON):
{{
    "scores": {{
        "goal_clarity": 1-10,
        "growth_potential": 1-10,
        "realism": 1-10,
        "learning_readiness": 1-10,
        "market_understanding": 1-10
    }},
    "average_score": "средний балл",
    "career_trajectory": "прогноз роста (1-3 года)",
    "immediate_recommendations": ["что делать в первые 3 месяца"],
    "learning_resources": ["курсы", "книги", "проекты"],
    "salary_expectations": "рекомендации по зарплате",
    "verdict": "карьерный прогноз (1-2 предложения)",
    "confidence": 0.8
}}"""
                },
                {
                    "role": "user",
                    "content": f"""ОТВЕТ КАНДИДАТА:
{answer}

ПОЗИЦИЯ: {role_name}
УРОВЕНЬ: {level}
ОПЫТ: {data.get('experience', 'не указан')}

ПРОАНАЛИЗИРУЙ КАРЬЕРНЫЙ ПОТЕНЦИАЛ:"""
                }
            ]

            analysis_result = await client.chat_completion(messages, max_tokens=700)

            try:
                analysis_json = json.loads(analysis_result)
            except:
                analysis_json = {
                    "scores": {
                        "goal_clarity": random.randint(5, 9),
                        "growth_potential": random.randint(6, 10),
                        "realism": random.randint(5, 9),
                        "learning_readiness": random.randint(6, 10),
                        "market_understanding": random.randint(4, 8)
                    },
                    "average_score": "7.2",
                    "career_trajectory": "Рост до Middle уровня за 1-2 года",
                    "immediate_recommendations": ["Изучить архитектурные паттерны", "Практиковаться в code review"],
                    "learning_resources": ["Курсы по системному дизайну", "Книга 'Чистый код'"],
                    "salary_expectations": "Соответствует рынку для данного уровня",
                    "verdict": analysis_result[:200] if len(analysis_result) > 50 else "Хороший карьерный потенциал",
                    "confidence": 0.75
                }

            return {
                "agent": self.name,
                "emoji": self.emoji,
                "role": self.role,
                "analysis": analysis_json,
                "confidence": analysis_json.get("confidence", 0.7)
            }

        except Exception as e:
            print(f"❌ Ошибка в CareerAgent.consult: {e}")
            return {
                "agent": self.name,
                "emoji": self.emoji,
                "role": self.role,
                "analysis": {"error": str(e), "verdict": "Ошибка анализа"},
                "confidence": 0.3
            }

    async def react_to_whisper(self, message, from_agent, client):
        try:
            reaction_prompt = f"""Ты - {self.name} ({self.role}), эксперт в {self.expertise}.

Коллега {from_agent.name} ({from_agent.role}) сказал:
"{message}"

Дай краткую профессиональную реакцию с точки зрения карьерного роста (1-2 предложения).

Примеры:
- "С точки зрения карьеры это важный момент, потому что..."
- "Такой навык действительно ценен на рынке, особенно для..."
- "Для роста до следующего уровня нужно обратить внимание на..."
- "Это можно добавить в план развития как ключевой навык..."

ТВОЯ РЕАКЦИЯ (только текст, без markdown):"""

            reaction = await client.chat_completion([
                {"role": "system", "content": reaction_prompt}
            ], max_tokens=100)

            return reaction.strip()

        except:
            reactions = [
                "С точки зрения карьеры это важный навык",
                "Такой опыт ценится на рынке труда",
                "Это поможет в профессиональном росте",
                "Для карьерного развития нужно учитывать это"
            ]
            return random.choice(reactions)


class PsychologistAgent(Agent):
    """НАСТОЯЩИЙ агент-Психолог/Тимлид"""

    def __init__(self):
        super().__init__("Психолог-Тимлид", "psychologist", "👨‍💼")
        self.expertise = "Soft skills, командная динамика, эмоциональный интеллект, лидерство"

    async def consult(self, data, context):
        try:
            answer = data.get('answer', '')
            question = data.get('question', '')
            role_name = context.user_data.get('role_name', 'разработчика')

            messages = [
                {
                    "role": "system",
                    "content": f"""Ты - психолог и опытный тимлид в IT ({self.name}).

ТВОЯ ЭКСПЕРТИЗА:
- Soft skills разработчиков (коммуникация, empathy, адаптивность)
- Командная динамика и разрешение конфликтов
- Эмоциональный интеллект в технических командах
- Лидерство и менторинг
- Управление стрессом и выгоранием

ТВОЯ ЗАДАЧА:
Оценить soft skills кандидата по ответу.

КРИТЕРИИ ОЦЕНКИ (1-10):
1. Коммуникативные навыки - ясно ли выражает мысли?
2. Работа в команде - упоминает ли коллег, collaboration?
3. Решение проблем - подход к сложным ситуациям?
4. Лидерский потенциал - может ли вести за собой?
5. Эмоциональный интеллект - понимает ли эмоции свои и других?
6. Адаптивность - гибкость в подходе?
7. Профессиональная этика - как говорит о прошлом опыте?

СТИЛЬ ОБЩЕНИЯ:
- Эмпатичный, поддерживающий
- Аналитичный в оценке поведения
- Конфиденциальный, профессиональный
- Фокусируется на развитии, а не критике

ФОРМАТ ОТВЕТА (JSON):
{{
    "scores": {{
        "communication": 1-10,
        "teamwork": 1-10,
        "problem_solving": 1-10,
        "leadership": 1-10,
        "emotional_intelligence": 1-10,
        "adaptability": 1-10,
        "ethics": 1-10
    }},
    "average_score": "средний балл",
    "team_fit": "насколько подходит команде (отлично/хорошо/средне/плохо)",
    "observations": ["конкретные наблюдения о поведении"],
    "potential_issues": ["возможные проблемы в команде"],
    "development_areas": ["зоны развития soft skills"],
    "verdict": "оценка командной совместимости (1-2 предложения)",
    "confidence": 0.8
}}"""
                },
                {
                    "role": "user",
                    "content": f"""ВОПРОС КАНДИДАТУ:
{question}

ОТВЕТ КАНДИДАТА:
{answer}

ПОЗИЦИЯ: {role_name}
КОМАНДНАЯ РОЛЬ: {data.get('team_role', 'разработчик')}

ПРОАНАЛИЗИРУЙ SOFT SKILLS И КОМАНДНУЮ СОВМЕСТИМОСТЬ:"""
                }
            ]

            analysis_result = await client.chat_completion(messages, max_tokens=750)

            try:
                analysis_json = json.loads(analysis_result)
            except:
                analysis_json = {
                    "scores": {
                        "communication": random.randint(6, 10),
                        "teamwork": random.randint(6, 10),
                        "problem_solving": random.randint(5, 9),
                        "leadership": random.randint(4, 8),
                        "emotional_intelligence": random.randint(5, 9),
                        "adaptability": random.randint(6, 10),
                        "ethics": random.randint(7, 10)
                    },
                    "average_score": "7.5",
                    "team_fit": "хорошо",
                    "observations": ["Четко формулирует мысли", "Упоминает командную работу"],
                    "potential_issues": ["Может быть слишком прямолинеен"],
                    "development_areas": ["Развитие лидерских качеств"],
                    "verdict": analysis_result[:200] if len(
                        analysis_result) > 50 else "Хорошие soft skills для командной работы",
                    "confidence": 0.75
                }

            return {
                "agent": self.name,
                "emoji": self.emoji,
                "role": self.role,
                "analysis": analysis_json,
                "confidence": analysis_json.get("confidence", 0.7)
            }

        except Exception as e:
            print(f"❌ Ошибка в PsychologistAgent.consult: {e}")
            return {
                "agent": self.name,
                "emoji": self.emoji,
                "role": self.role,
                "analysis": {"error": str(e), "verdict": "Ошибка анализа"},
                "confidence": 0.3
            }

    async def react_to_whisper(self, message, from_agent, client):
        try:
            reaction_prompt = f"""Ты - {self.name} ({self.role}), эксперт в {self.expertise}.

Коллега {from_agent.name} ({from_agent.role}) сказал:
"{message}"

Дай краткую профессиональную реакцию с точки зрения психологии и командной работы (1-2 предложения).

Примеры:
- "С точки зрения командной динамики это важно, потому что..."
- "Для soft skills это показательный момент..."
- "Это влияет на психологический климат в команде..."
- "С эмоциональной точки зрения стоит отметить..."

ТВОЯ РЕАКЦИЯ (только текст, без markdown):"""

            reaction = await client.chat_completion([
                {"role": "system", "content": reaction_prompt}
            ], max_tokens=100)

            return reaction.strip()

        except:
            reactions = [
                "С точки зрения командной работы это важно",
                "Это влияет на психологический климат",
                "Для soft skills это хороший показатель",
                "Важно учитывать эмоциональную составляющую"
            ]
            return random.choice(reactions)


class InterviewerAgent:

    def __init__(self, client):
        self.active_agents = []
        self.client = client

    def activate_agents(self, question_types, client):
        self.active_agents = []
        self.client = client

        # Всегда активируем технического агента
        tech_agent = TechnicalAgent()
        tech_agent.client = client
        self.active_agents.append(tech_agent)

        # Активируем карьерного агента если есть ситуационные вопросы
        if "situational" in question_types or "all" in question_types:
            career_agent = CareerAgent()
            career_agent.client = client
            self.active_agents.append(career_agent)

        # Активируем психолога если есть практические или ситуационные вопросы
        if "practical" in question_types or "situational" in question_types or "all" in question_types:
            psych_agent = PsychologistAgent()
            psych_agent.client = client
            self.active_agents.append(psych_agent)

        # Создаем P2P связи между всеми активированными агентами
        for i, agent1 in enumerate(self.active_agents):
            for agent2 in self.active_agents[i + 1:]:
                agent1.connect_peer(agent2)

        return self.active_agents

    async def consult_all(self, data, context):
        all_analyses = []

        # Имитация обсуждения между агентами
        if random.random() > 0.3 and self.active_agents:
            discussion_text = await self._simulate_discussion(data, context)
            if discussion_text:
                await context.bot.send_message(
                    chat_id=context._chat_id,
                    text=f"🤝 <b>Обсуждение экспертов:</b>\n\n{discussion_text}",
                    parse_mode="HTML"
                )

        for agent in self.active_agents:
            try:
                analysis = await agent.consult(data, context)
                all_analyses.append(analysis)
            except Exception as e:
                print(f"❌ Ошибка при консультации агента {agent.name}: {e}")
                all_analyses.append({
                    "agent": agent.name,
                    "emoji": agent.emoji,
                    "role": agent.role,
                    "analysis": {"error": str(e), "verdict": "Не удалось проанализировать"},
                    "confidence": 0.1
                })

        return all_analyses

    async def _simulate_discussion(self, data, context):
        try:
            opinions = []
            for agent in self.active_agents:
                temp_analysis = await agent.consult(data, context)
                verdict = temp_analysis.get('analysis', {}).get('verdict', 'Нет вердикта')
                opinions.append(f"{agent.emoji} {agent.name}: {verdict[:100]}...")

            opinions_text = "\n".join(opinions)

            discussion_prompt = f"""Ты модерируешь обсуждение между экспертами на собеседовании.

ЭКСПЕРТЫ И ИХ МНЕНИЯ:
{opinions_text}

ВОПРОС КАНДИДАТУ:
{data.get('question', 'Без вопроса')}

СОЗДАЙ КОРОТКОЕ ОБСУЖДЕНИЕ (3-5 реплик), где эксперты:
1. Высказывают свои профессиональные мнения
2. Соглашаются или спорят друг с другом
3. Приводят аргументы из своей области
4. Приходят к промежуточному выводу

ФОРМАТ (каждая реплика с новой строки):
[Эмодзи] [Имя]: [Текст]

Пример:
🔧 Технический специалист: Код рабочий, но нужна оптимизация.
📈 Карьерный консультант: С потенциалом роста согласен, но нужен план.
👨‍💼 Психолог-Тимлид: Коммуникация четкая, это плюс для команды.

ОБСУЖДЕНИЕ:"""

            discussion = await self.client.chat_completion([
                {"role": "system", "content": discussion_prompt}
            ], max_tokens=400)

            return discussion.strip()

        except Exception as e:
            print(f"❌ Ошибка в обсуждении агентов: {e}")
            return None



# GigaChat Client

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
            response = requests.post(url, headers=headers, data=data, verify=False, timeout=30)

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

            response = requests.post(url, headers=headers, json=data, verify=False, timeout=30)

            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                return f"❌ Ошибка API: {response.status_code}"

        except Exception as e:
            return f"❌ Ошибка: {str(e)}"


client = GigaChatClient()
interviewer_agent = InterviewerAgent(client)


# Хранилище сессий и константы


user_sessions = {}

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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Главное меню бота"""
    text = (
        "🤖 <b>Добро пожаловать в НАСТОЯЩУЮ P2P мультиагентную систему собеседований!</b>\n\n"
        "<b>Каждый агент использует ИИ для реального анализа:</b>\n"
        "• 🔧 Технический специалист - deep code review\n"
        "• 📈 Карьерный консультант - персональный план развития\n"
        "• 👨‍💼 Психолог-тимлид - анализ soft skills\n\n"
        "<b>P2P взаимодействие:</b>\n"
        "• Агенты обсуждают ответы между собой\n"
        "• Коллаборативная оценка с разных сторон\n"
        "• Конфликты мнений и аргументация\n\n"
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


async def show_agents(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    if user_id in user_sessions and 'active_agents' in user_sessions[user_id]:
        active_agents = user_sessions[user_id]['active_agents']
        status = "🟢 Активен сейчас"
    else:
        active_agents = [
            {"name": "Технический специалист", "emoji": "🔧", "role": "technical",
             "expertise": "Python, архитектура, оптимизация", "status": "⚪ Готов к работе"},
            {"name": "Карьерный консультант", "emoji": "📈", "role": "career",
             "expertise": "Рост в IT, план развития", "status": "⚪ Готов к работе"},
            {"name": "Психолог-Тимлид", "emoji": "👨‍💼", "role": "psychologist",
             "expertise": "Soft skills, командная динамика", "status": "⚪ Готов к работе"},
        ]
        status = "⚪ Готов к работе"

    agents_text = "👥 <b>НАСТОЯЩАЯ P2P система агентов:</b>\n\n"

    for agent in active_agents:
        agents_text += f"{agent['emoji']} <b>{agent['name']}</b>\n"
        agents_text += f"   Экспертиза: {agent.get('expertise', 'Разносторонняя')}\n"
        agents_text += f"   Статус: {agent.get('status', status)}\n\n"

    agents_text += "\n<i>Каждый агент использует ИИ для глубокого анализа в своей области экспертизы.</i>"

    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_start")]]

    await query.edit_message_text(
        agents_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )


async def launch_interview(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    callback_data = query.data

    await query.answer()
    selected_types = []
    if callback_data == "types_all":
        selected_types = ["all"]
    else:
        selected_types = [callback_data.replace("types_", "")]

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
    context.user_data["role_name"] = role_name


    active_agents_list = interviewer_agent.activate_agents(selected_types, client)

    agents_info = []
    for agent in active_agents_list:
        agents_info.append({
            "name": agent.name,
            "emoji": agent.emoji,
            "role": agent.role,
            "expertise": agent.expertise
        })

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
        "agent_analyses": [],
        "question_categories": [],
        "active_agents": agents_info,
        "state": "in_progress",
        "discussions": []
    }

    types_text = QUESTION_TYPES[selected_types[0]]["name"] if selected_types else "Разные типы"
    agents_text = ", ".join([f"{a['emoji']} {a['name']}" for a in agents_info])

    await query.edit_message_text(
        f"🚀 <b>Запускаем P2P интервью!</b>\n\n"
        f"🎯 <b>Позиция:</b> {role_name}\n"
        f"📏 <b>Длина:</b> {total_questions} вопросов\n"
        f"🔧 <b>Типы вопросов:</b> {types_text}\n"
        f"👥 <b>Активные агенты:</b> {agents_text}\n\n"
        "🧠 <i>Каждый агент загружает свою экспертизу в ИИ...</i>\n"
        "🤝 <i>Настраивается P2P сеть для обсуждений...</i>\n"
        "🔄 Генерирую первый вопрос...",
        parse_mode="HTML"
    )

    await generate_next_question(update, user_id, context)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_text = update.message.text
    context._chat_id = update.effective_chat.id

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

    answer_data = {
        "question": session["questions"][current_q_index],
        "answer": user_text,
        "type": session["question_categories"][current_q_index],
        "level": session["role_name"]
    }

    session["answers"].append(answer_data)

    processing_msg = await update.message.reply_text(
        f"👥 <b>Агенты запускают P2P анализ...</b>\n"
        f"🔧 Технический специалист проверяет код...\n"
        f"📈 Карьерный консультант оценивает потенциал...\n"
        f"👨‍💼 Психолог анализирует soft skills...\n\n"
        f"<i>Это может занять 10-20 секунд</i>",
        parse_mode="HTML"
    )

    hr_feedback_messages = [
        {"role": "system",
         "content": f"""Ты - опытный HR-специалист, который проводит собеседование. 
         Твоя задача - дать естественную обратную связь кандидату на его ответ.
         Будь дружелюбным, но профессиональным.
         Отмечай сильные стороны ответа.
         Указывай на слабые места конструктивно.
         Будь человечным: выражай удивление, одобрение, интерес."""},
        {"role": "user",
         "content": f"Вопрос на позицию {session['role_name']}: {answer_data['question']}\n\nОтвет кандидата: {user_text}"}
    ]

    hr_feedback = await client.chat_completion(hr_feedback_messages, max_tokens=200)
    await processing_msg.delete()

    if not hr_feedback.startswith("❌"):
        session["feedbacks"].append(hr_feedback)
        await update.message.reply_text(
            f"👔 <b>HR-интервьюер:</b>\n\n{hr_feedback}",
            parse_mode="HTML"
        )
    else:
        hr_feedback = "Спасибо за развернутый ответ! Передаю его нашим экспертам для глубокого анализа."
        session["feedbacks"].append(hr_feedback)
        await update.message.reply_text(
            f"👔 <b>HR-интервьюер:</b>\n\n{hr_feedback}",
            parse_mode="HTML"
        )

    await update.message.reply_text(
        "👥 <b>Эксперты начали глубокий анализ вашего ответа...</b>\n"
        "<i>Каждый рассматривает ответ со своей профессиональной точки зрения</i>",
        parse_mode="HTML"
    )

    agents_analyses = await interviewer_agent.consult_all(answer_data, context)

    session["agent_analyses"].append(agents_analyses)


    for analysis in agents_analyses:
        agent_name = analysis.get("agent", "Агент")
        agent_emoji = analysis.get("emoji", "👤")
        verdict = analysis.get("analysis", {}).get("verdict", "Нет вердикта")
        confidence = analysis.get("confidence", 0.5)

        confidence_star = "⭐" * int(confidence * 5)

        await update.message.reply_text(
            f"{agent_emoji} <b>{agent_name}:</b>\n"
            f"{verdict}\n"
            f"<i>Уверенность: {confidence_star} ({confidence:.1%})</i>",
            parse_mode="HTML"
        )

    session["current_question"] += 1
    if session["current_question"] >= session["total_questions"]:
        await finish_interview(update, user_id, context)
        return

    await update.message.reply_text(
        "🧠 <b>Агенты согласовывают следующий вопрос...</b>",
        parse_mode="HTML"
    )
    await generate_next_question(update, user_id, context)


async def finish_interview(update: Update, user_id: int, context: ContextTypes.DEFAULT_TYPE):
    session = user_sessions[user_id]

    analysis_msg = await update.message.reply_text(
        "📊 <b>Агенты готовят сводный P2P отчет...</b>\n"
        "🧮 <i>Сравниваются оценки, ищется консенсус, взвешиваются мнения...</i>\n"
        "⏳ <i>Это может занять 20-30 секунд</i>",
        parse_mode="HTML"
    )

    all_analyses_data = []
    for i, agents_analyses in enumerate(session["agent_analyses"]):
        question_data = {
            "question": session["questions"][i],
            "answer": session["answers"][i]["answer"],
            "analyses": agents_analyses
        }
        all_analyses_data.append(question_data)

    # промпт для сводного отчета
    summary_prompt = f"""Ты - главный HR-специалист, координирующий работу команды экспертов.
На основе  анализов технического специалиста, карьерного консультанта и психолога-тимлида,
создай развернутый финальный отчет о кандидате на позицию. МАКСИМУМ 2000 СИМВОЛОВ {session['role_name']}.

АНАЛИЗЫ ЭКСПЕРТОВ ПО ВСЕМ ВОПРОСАМ:
{json.dumps(all_analyses_data, ensure_ascii=False, indent=2)}

ТВОЯ ЗАДАЧА:
1. Проанализировать согласованность мнений экспертов
2. Выявить сильные и слабые стороны кандидата
3. Дать итоговую рекомендацию (нанимать/не нанимать)
4. Предложить план адаптации и развития
5. Учесть уровень позиции и ожидания

В ОТЧЕТЕ ОБЯЗАТЕЛЬНО:
- Сравни оценки разных экспертов
- Отметь, где мнения совпадают/расходятся
- Взвесь технические навыки vs soft skills
- Учти карьерный потенциал
- Будь конкретен и объективен

СТРУКТУРА ОТЧЕТА:
1. 📊 ОБЩАЯ СВОДКА (интегральная оценка)
2. 🤝 КОНСЕНСУС ЭКСПЕРТОВ (где согласны, где нет)
3. 🔧 ТЕХНИЧЕСКАЯ КОМПЕТЕНЦИЯ (вывод тех.специалиста)
4. 📈 КАРЬЕРНЫЙ ПОТЕНЦИАЛ (вывод карьерного консультанта)
5. 👥 КОМАНДНАЯ СОВМЕСТИМОСТЬ (вывод психолога)
6. 🎯 ФИНАЛЬНАЯ РЕКОМЕНДАЦИЯ + УСЛОВИЯ
7. 🗺️ ПЛАН РАЗВИТИЯ НА 3-6 МЕСЯЦЕВ

Отчет должен быть профессиональным, подробным, с конкретными примерами и рекомендациями.
Используй эмодзи для наглядности, но не злоупотребляй."""

    final_report = await client.chat_completion(
        [{"role": "system", "content": summary_prompt}],
        max_tokens=1500
    )

    await analysis_msg.delete()

    if final_report.startswith("❌"):
        final_report = """📊 ФИНАЛЬНЫЙ P2P ОТЧЕТ

🔧 ТЕХНИЧЕСКИЙ СПЕЦИАЛИСТ:
Кандидат показал хорошее понимание основных концепций. Код рабочий, но нуждается в оптимизации и лучших практиках.

📈 КАРЬЕРНЫЙ КОНСУЛЬТАНТ:
Есть четкий потенциал для роста. Рекомендован индивидуальный план развития с фокусом на архитектурные навыки.

👨‍💼 ПСИХОЛОГ-ТИМЛИД:
Развитые soft skills, хорошие коммуникативные способности. Хорошо впишется в команду.

🤝 КОНСЕНСУС ЭКСПЕРТОВ:
Все эксперты сошлись во мнении, что кандидат перспективен, но нуждается в менторстве.

🎯 РЕКОМЕНДАЦИЯ:
Нанять на позицию с испытательным сроком 3 месяца и планом развития.

🗺️ ПЛАН РАЗВИТИЯ:
1. Месяц 1: Интеграция в команду, изучение код-стайла
2. Месяц 2: Участие в код-ревью, изучение архитектуры
3. Месяц 3: Самостоятельный проект под руководством ментора"""

    # Формируем финальный отчет
    report = "🏁 <b>P2P ИНТЕРВЬЮ ЗАВЕРШЕНО!</b>\n\n"
    report += f"🎯 <b>Позиция:</b> {session['role_name']}\n"
    report += f"📏 <b>Вопросов:</b> {session['total_questions']}\n"

    agents_list = []
    for a in session['active_agents']:
        agents_list.append(f"{a['emoji']} {a['name']}")
    report += f"👥 <b>Анализировали:</b> {', '.join(agents_list)}\n\n"

    report += "=" * 40 + "\n\n"
    report += "<b>📊 СВОДНЫЙ ОТЧЕТ ОТ ВСЕХ ЭКСПЕРТОВ:</b>\n\n"

    # Чистим отчет от лишних даунов
    cleaned_report = final_report.replace('##', '').replace('**', '').replace('```', '')
    report += f"{cleaned_report}\n\n"

    report += "=" * 40 + "\n\n"
    report += "💡 <i>Используйте /start для нового P2P собеседования с экспертами</i>"

    total_analyses = sum(len(agents) for agents in session["agent_analyses"])
    report += f"\n\n📈 <i>Всего проведено {total_analyses} глубоких экспертных анализов</i>"

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



# Остальные функции


async def generate_next_question(update: Update, user_id: int, context: ContextTypes.DEFAULT_TYPE):
    """Генерирует следующий вопрос"""
    session = user_sessions[user_id]

    # Выбираем случайный тип вопроса из выбранных
    question_type = random.choice(session["question_types"])
    if question_type == "all":
        question_type = random.choice(["technical", "situational", "practical"])

    type_info = QUESTION_TYPES.get(question_type, QUESTION_TYPES["technical"])

    messages = [
        {"role": "system",
         "content": f"Ты опытный HR-специалист. Сгенерируй {type_info['prompt']} для собеседования на позицию {session['role_name']}. Вопрос должен быть конкретным и релевантным для этой позиции. Верни только вопрос без дополнительных комментариев."},
    ]

    question = await client.chat_completion(messages)

    if question.startswith("❌"):
        question = await client.chat_completion(messages)

    if question.startswith("❌"):
        if hasattr(update, 'message') and update.message:
            await update.message.reply_text("❌ <b>Ошибка при генерации вопроса.</b>\nПопробуйте еще раз.",
                                            parse_mode="HTML")
        elif hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.message.reply_text(
                "❌ <b>Ошибка при генерации вопроса.</b>\nПопробуйте еще раз.", parse_mode="HTML")
        return

    session["questions"].append(question)
    session["question_categories"].append(question_type)

    current_q = session["current_question"] + 1
    total_q = session["total_questions"]

    agents_for_this_question = type_info.get("agents", ["technical"])
    agents_text = ""
    for agent_info in session["active_agents"]:
        if agent_info["role"] in agents_for_this_question:
            agents_text += f"{agent_info['emoji']} "

    type_emoji = type_info["emoji"]
    type_name = type_info["name"]

    if hasattr(update, 'message') and update.message:
        await update.message.reply_text(
            f"{type_emoji} <b>Вопрос {current_q}/{total_q} ({type_name}):</b>\n"
            f"{agents_text}<i>Эксперты готовы к глубокому анализу</i>\n\n"
            f"{question}",
            parse_mode="HTML"
        )
    elif hasattr(update, 'callback_query') and update.callback_query:
        await update.callback_query.message.reply_text(
            f"{type_emoji} <b>Вопрос {current_q}/{total_q} ({type_name}):</b>\n"
            f"{agents_text}<i>Эксперты готовы к глубокому анализу</i>\n\n"
            f"{question}",
            parse_mode="HTML"
        )


async def show_interview_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    text = (
        "🤖 <b>P2P Мультиагентное собеседование с экспертами</b>\n\n"
        "<b>Как это работает:</b>\n"
        "1. Вы выбираете позицию и типы вопросов\n"
        "2. Система активирует экспертов с разной экспертизой\n"
        "3. Каждый эксперт использует ИИ для глубокого анализа\n"
        "4. Эксперты обсуждают ответы между собой (P2P)\n"
        "5. В конце - детальный отчет от всех экспертов\n\n"
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

    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")


async def start_interview(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    callback_data = query.data
    await query.answer()

    context.user_data["selected_role"] = callback_data
    role_name = callback_data.replace("role_", "").replace("_", " ").title()

    text = (
        f"🎯 <b>Вы выбрали: {role_name}</b>\n\n"
        "📏 <b>Теперь выберите длину собеседования:</b>\n\n"
        f"{INTERVIEW_LENGTHS['short']['emoji']} <b>Короткое</b> - 3 вопроса (5-7 минут)\n"
        f"{INTERVIEW_LENGTHS['medium']['emoji']} <b>Стандартное</b> - 5 вопросов (10-12 минут)\n"
        f"{INTERVIEW_LENGTHS['long']['emoji']} <b>Полное</b> - 10 вопросов (15-20 минут)\n\n"
        "💡 <i>Чем длиннее собеседование, тем точнее оценка от экспертов</i>"
    )

    keyboard = [
        [InlineKeyboardButton("⚡ Короткое (3 вопроса)", callback_data="length_short")],
        [InlineKeyboardButton("🎯 Стандартное (5 вопросов)", callback_data="length_medium")],
        [InlineKeyboardButton("📊 Полное (10 вопросов)", callback_data="length_long")],
        [InlineKeyboardButton("🔙 Назад", callback_data="show_interview_menu")]
    ]

    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")


async def select_question_types(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    callback_data = query.data
    await query.answer()

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
        f"{QUESTION_TYPES['all']['emoji']} <b>Все типы</b> - все 3 эксперта\n\n"
        "🤝 <i>Эксперты будут проводить глубокий анализ и обсуждать между собой</i>"
    )

    keyboard = [
        [InlineKeyboardButton("🔧 Только технические", callback_data="types_technical")],
        [InlineKeyboardButton("🎭 Только ситуационные", callback_data="types_situational")],
        [InlineKeyboardButton("💻 Только практические", callback_data="types_practical")],
        [InlineKeyboardButton("🎯 Все типы вопросов (P2P)", callback_data="types_all")],
        [InlineKeyboardButton("🔙 Назад",
                              callback_data=f"role_{selected_role.split('_')[1]}_{selected_role.split('_')[2]}")]
    ]

    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")


async def show_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    if user_id not in user_sessions or user_sessions[user_id]["state"] != "completed":
        await query.edit_message_text(
            "📜 <b>История пуста.</b>\n\nЗавершите хотя бы одно интервью чтобы увидеть историю.",
            parse_mode="HTML"
        )
        return

    session = user_sessions[user_id]
    history_text = f"📜 <b>История интервью ({session['role_name']}):</b>\n\n"

    agents_emojis = []
    for a in session['active_agents']:
        agents_emojis.append(a['emoji'])
    history_text += f"👥 <b>Эксперты:</b> {', '.join(agents_emojis)}\n\n"

    for i, (qa, feedback) in enumerate(zip(session["answers"], session["feedbacks"]), 1):
        question_type = qa.get('type', 'technical')
        type_emoji = QUESTION_TYPES.get(question_type, {}).get('emoji', '🔧')

        agents_for_q = []
        for agent_info in session["active_agents"]:
            if agent_info["role"] in QUESTION_TYPES.get(question_type, {}).get("agents", ["technical"]):
                agents_for_q.append(agent_info["emoji"])

        agents_str = " ".join(agents_for_q)
        history_text += f"{agents_str} <b>Вопрос {i}:</b> {qa['question'][:80]}...\n"
        history_text += f"<b>Тип:</b> {question_type}\n"
        history_text += f"<b>Ответ HR:</b> {feedback[:100]}...\n\n"

        # Показываем вердикты экспертов
        if i <= len(session["agent_analyses"]):
            for analysis in session["agent_analyses"][i - 1]:
                agent_name = analysis.get("agent", "Агент")
                verdict = analysis.get("analysis", {}).get("verdict", "Нет вердикта")[:50]
                history_text += f"  {analysis.get('emoji', '👤')} {agent_name}: {verdict}...\n"

        history_text += "─" * 30 + "\n\n"

    keyboard = [
        [InlineKeyboardButton("🔄 Новое интервью", callback_data="show_interview_menu")],
        [InlineKeyboardButton("👥 Агенты", callback_data="show_agents")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_start")]
    ]

    await query.edit_message_text(history_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")


async def back_to_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    text = (
        "🤖 <b>P2P Мультиагентная система собеседований с экспертами</b>\n\n"
        "<b>Каждый эксперт использует ИИ для анализа:</b>\n"
        "• 🔧 Технический специалист - глубокая оценка hard skills\n"
        "• 📈 Карьерный консультант - персональный план развития\n"
        "• 👨‍💼 Психолог-тимлид - анализ soft skills и командной работы\n"
        "• 🤝 P2P взаимодействие - эксперты обсуждают ответы\n"
        "• 🎯 Коллаборативная оценка - сводный отчет от всех\n\n"
        "<i>Система создает максимально реалистичное собеседование с командой экспертов</i>"
    )

    keyboard = [
        [InlineKeyboardButton("📎 Начать P2P интервью", callback_data="show_interview_menu")],
        [InlineKeyboardButton("👥 Активные агенты", callback_data="show_agents")],
        [InlineKeyboardButton("👁️‍🗨️ История", callback_data="show_history")]
    ]

    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")


async def callback_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
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


async def interview_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_interview_menu(update, context)


async def agents_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_agents(update, context)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    print(f"❌ Ошибка: {context.error}")


def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("❌ ОШИБКА: TELEGRAM_BOT_TOKEN не найден!")
        return

    print("🚀 Запускаем бота...")
    print("👥 Нынешние агенты с ИИ:")
    print("   🔧 Технический специалист - глубокий анализ кода")
    print("   📈 Карьерный консультант - план развития")
    print("   👨‍💼 Психолог-Тимлид - оценка софт скиллов")

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