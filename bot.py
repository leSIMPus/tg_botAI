import os
import requests
import uuid
import asyncio
import random
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
        "prompt": "технический вопрос проверяющий технические знания"
    },
    "situational": {
        "name": "Ситуационные вопросы",
        "emoji": "🎭",
        "prompt": "ситуационный вопрос о реальных рабочих ситуациях и поведении в команде"
    },
    "practical": {
        "name": "Практические задачи",
        "emoji": "💻",
        "prompt": "практическую задачу или coding challenge для проверки навыков программирования"
    }
}


# ------------------------------------------------------
#  Команда /start
# ------------------------------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Главное меню бота"""
    text = (
        "Добро пожаловать! Я проведу для вас реалистичное HR-собеседование.\n\n"
        "<b>Как это работает:</b>\n"
        "• Вы отвечаете на вопросы\n"
        "• После каждого ответа я даю краткую обратную связь\n"
        "• В конце - полный разбор ваших ответов\n\n"
        "👀 <b>Каждое собеседование уникально!</b>\n"
        "Вопросы генерируются мною специально для вас.\n\n"
        "Выберите действие:"
    )

    keyboard = [
        [InlineKeyboardButton("📎 Начать интервью", callback_data="show_interview_menu")],
        [InlineKeyboardButton("👁️‍🗨️ История", callback_data="show_history")]
    ]

    await update.message.reply_text(
        text,
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
        "Добро пожаловать! Я проведу для вас реалистичное HR-собеседование.\n\n"
        "<b>Как это работает:</b>\n"
        "• Вы отвечаете на вопросы\n"
        "• После каждого ответа я даю краткую обратную связь\n"
        "• В конце - полный разбор ваших ответов\n\n"
        "👀 <b>Каждое собеседование уникально!</b>\n"
        "Вопросы генерируются мною специально для вас.\n\n"
        "Выберите действие:"
    )

    keyboard = [
        [InlineKeyboardButton("👶 Junior Python", callback_data="role_junior_python")],
        [InlineKeyboardButton("🧑 Middle Python", callback_data="role_middle_python")],
        [InlineKeyboardButton("🪦 Senior Python", callback_data="role_senior_python")],
        [InlineKeyboardButton("📊 Data Scientist", callback_data="role_data_scientist")],
        [InlineKeyboardButton("👬 Team Lead", callback_data="role_team_lead")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_start")]
    ]

    await query.edit_message_text(
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
        "💡 <i>Чем длиннее собеседование, тем точнее оценка</i>"
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
        f"{QUESTION_TYPES['technical']['emoji']} <b>Технические</b> - проверка знаний и навыков\n"
        f"{QUESTION_TYPES['situational']['emoji']} <b>Ситуационные</b> - поведение в рабочих ситуациях\n"
        f"{QUESTION_TYPES['practical']['emoji']} <b>Практические</b> - задачи и coding challenges\n\n"
        "💡 <i>Рекомендуем выбрать все типы для полной оценки</i>"
    )

    keyboard = [
        [InlineKeyboardButton("🔧 Только технические", callback_data="types_technical")],
        [InlineKeyboardButton("🎭 Только ситуационные", callback_data="types_situational")],
        [InlineKeyboardButton("💻 Только практические", callback_data="types_practical")],
        [InlineKeyboardButton("🎯 Все типы вопросов", callback_data="types_all")],
        [InlineKeyboardButton("🔙 Назад", callback_data=f"{selected_role}")]
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
        selected_types = list(QUESTION_TYPES.keys())
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
        "question_categories": [],  # Тип каждого вопроса
        "state": "in_progress"
    }

    # Показываем стартовое сообщение
    types_text = ", ".join([QUESTION_TYPES[t]["name"] for t in selected_types])
    await query.edit_message_text(
        f"🚀 <b>Запускаем интервью!</b>\n\n"
        f"🎯 <b>Позиция:</b> {role_name}\n"
        f"📏 <b>Длина:</b> {total_questions} вопросов\n"
        f"🔧 <b>Типы вопросов:</b> {types_text}\n\n"
        "🔄 Генерирую первый вопрос...",
        parse_mode="HTML"
    )

    # Генерируем первый вопрос
    await generate_next_question(update, user_id)


async def generate_next_question(update: Update, user_id: int):
    """Генерирует следующий вопрос"""
    session = user_sessions[user_id]

    # Выбираем случайный тип вопроса из выбранных
    question_type = random.choice(session["question_types"])
    type_info = QUESTION_TYPES[question_type]

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

    # Показываем вопрос с указанием типа
    type_emoji = type_info["emoji"]
    type_name = type_info["name"]

    # Безопасная отправка сообщения
    if hasattr(update, 'message') and update.message:
        await update.message.reply_text(
            f"{type_emoji} <b>Вопрос {current_q}/{total_q} ({type_name}):</b>\n\n{question}",
            parse_mode="HTML"
        )
    elif hasattr(update, 'callback_query') and update.callback_query:
        await update.callback_query.message.reply_text(
            f"{type_emoji} <b>Вопрос {current_q}/{total_q} ({type_name}):</b>\n\n{question}",
            parse_mode="HTML"
        )
# ------------------------------------------------------
#  Обработка ответов пользователя
# ------------------------------------------------------

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_text = update.message.text

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
    session["answers"].append({
        "question": session["questions"][current_q_index],
        "answer": user_text,
        "type": session["question_categories"][current_q_index]
    })

    # Показываем, что обрабатываем ответ
    processing_msg = await update.message.reply_text(
        "⏳ <b>HR анализирует ваш ответ...</b>",
        parse_mode="HTML"
    )

    # Генерируем КРАТКУЮ обратную связь
    feedback_messages = [
        {"role": "system",
         "content": "Ты опытный HR-специалист. Дай краткую обратную связь на ответ кандидата (1-2 предложения). Отвечай естественно и обращаясь именно к кандидату. Веди себя по-человечески: выражай непонимание, удовлетворение или другие подходящие чувства. Будь конкретным и конструктивным."},
        {"role": "user", "content": f"Вопрос: {session['questions'][current_q_index]}\nОтвет кандидата: {user_text}"}
    ]

    quick_feedback = await client.chat_completion(feedback_messages, max_tokens=150)
    await processing_msg.delete()

    if not quick_feedback.startswith("❌"):
        session["feedbacks"].append(quick_feedback)
        await update.message.reply_text(
            f"\n{quick_feedback}",
            parse_mode="HTML"
        )

    # Переходим к следующему вопросу
    session["current_question"] += 1

    # Проверяем, закончилось ли интервью
    if session["current_question"] >= session["total_questions"]:
        await finish_interview(update, user_id)
        return

    # Генерируем следующий вопрос
    await update.message.reply_text(
        "🧠 Генерирую следующий вопрос...",
        parse_mode="HTML"
    )
    await generate_next_question(update, user_id)  # Передаем update напрямую


# ------------------------------------------------------
#  Завершение интервью с рекомендациями
# ------------------------------------------------------

async def finish_interview(update: Update, user_id: int):
    """Завершает интервью и генерирует полный фидбек с рекомендациями"""
    session = user_sessions[user_id]

    analysis_msg = await update.message.reply_text(
        "📝 <b>HR готовит полный анализ с рекомендациями...</b>",
        parse_mode="HTML"
    )

    # Генерируем полный фидбек с рекомендациями
    feedback_messages = [
        {"role": "system",
         "content": f"""Ты опытный HR-специалист. Проанализируй ответы кандидата на позицию {session['role_name']} и дай РАЗВЕРНУТУЮ обратную связь.

Структура:
1. ОБЩАЯ ОЦЕНКА - общее впечатление
2. СИЛЬНЫЕ СТОРОНЫ - 2-3 конкретных пункта  
3. ОБЛАСТИ РАЗВИТИЯ - 2-3 конструктивных пункта
4. КОНКРЕТНЫЕ РЕКОМЕНДАЦИИ ПО ОБУЧЕНИЮ - ссылки на курсы, книги, практические проекты
5. ВЕРДИКТ - подходит/не подходит и почему

Для рекомендаций используй актуальные ресурсы: Stepik, Coursera, книги, YouTube каналы, практические проекты."""},
    ]

    # Добавляем вопросы и ответы
    for i, qa in enumerate(session["answers"]):
        feedback_messages.append({
            "role": "user",
            "content": f"Вопрос {i + 1} ({qa['type']}): {qa['question']}\nОтвет: {qa['answer']}"
        })

    final_feedback = await client.chat_completion(feedback_messages, max_tokens=1000)
    await analysis_msg.delete()

    if final_feedback.startswith("❌"):
        final_feedback = "✅ <b>Интервью завершено!</b>\n\nСпасибо за участие!"

    # Формируем отчет
    report = f"🎯 <b>ИНТЕРВЬЮ ЗАВЕРШЕНО! ({session['role_name']})</b>\n\n"
    report += "📋 <b>ПОЛНЫЙ АНАЛИЗ С РЕКОМЕНДАЦИЯМИ:</b>\n\n"
    report += f"{final_feedback}\n\n"
    report += "💡 <i>Используйте /start для нового собеседования</i>"

    keyboard = [
        [InlineKeyboardButton("🔄 Новое интервью", callback_data="show_interview_menu")],
        [InlineKeyboardButton("👁️‍🗨️ История", callback_data="show_history")]
    ]

    await update.message.reply_text(
        report,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )

    session["state"] = "completed"


# ------------------------------------------------------
#  Остальные функции (история, навигация) остаются без изменений
# ------------------------------------------------------

async def show_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает краткую историю собеседований"""
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    if user_id not in user_sessions or user_sessions[user_id]["state"] != "completed":
        await query.edit_message_text(
            "📜 <b>История пуста.</b>\n\n"
            "Завершите хотя бы одно интервью чтобы увидеть историю.",
            parse_mode="HTML"
        )
        return

    session = user_sessions[user_id]

    history_text = f"📜 <b>Краткая история ({session['role_name']}):</b>\n\n"

    for i, (qa, feedback) in enumerate(zip(session["answers"], session["feedbacks"]), 1):
        question_type = qa.get('type', 'technical')
        type_emoji = QUESTION_TYPES.get(question_type, {}).get('emoji', '🔧')
        history_text += f"{type_emoji} <b>Вопрос {i}:</b> {qa['question']}\n"
        history_text += f"<b>Ответ:</b> {qa['answer'][:100]}...\n"
        history_text += f"<b>Фидбек:</b> {feedback}\n\n"
        history_text += "─" * 30 + "\n\n"

    keyboard = [
        [InlineKeyboardButton("🔄 Новое интервью", callback_data="show_interview_menu")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_start")]
    ]

    await query.edit_message_text(
        history_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )


async def back_to_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возвращает в главное меню"""
    query = update.callback_query
    await query.answer()

    text = (
        "👋 <b>Добро пожаловать в AI HR Interview Bot!</b>\n\n"
        "<b>Новые возможности:</b>\n"
        "• 🎯 Выбор длины собеседования\n"
        "• 🔧 Разные типы вопросов\n"
        "• 💻 Практические задачи\n"
        "• 🎭 Ситуационные кейсы\n"
        "• 📚 Персональные рекомендации\n\n"
        "Выберите действие:"
    )

    keyboard = [
        [InlineKeyboardButton("📎 Начать интервью", callback_data="show_interview_menu")],
        [InlineKeyboardButton("👁️‍🗨️ История", callback_data="show_history")]
    ]

    await query.message.reply_text(
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
#  Настройка бота
# ------------------------------------------------------

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    print(f"❌ Ошибка: {context.error}")


def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("❌ ОШИБКА: TELEGRAM_BOT_TOKEN не найден!")
        return

    print("🚀 Создаем Application...")

    application = Application.builder().token(token).build()

    application.add_handler(CallbackQueryHandler(callback_router))
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("interview", interview_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    application.add_error_handler(error_handler)

    print("✅ Бот запущен с новыми функциями!")

    application.run_polling()


if __name__ == "__main__":
    main()