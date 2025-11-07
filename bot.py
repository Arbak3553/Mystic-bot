#!/usr/bin/env python3
"""
Мистический Telegram бот - Хиромантия, Таро, Астрология
"""
import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    filters,
    ContextTypes
)
from dotenv import load_dotenv
from openai import OpenAI
import tarot
import base64
from datetime import datetime
from PIL import Image
import io

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Инициализация DeepSeek API
deepseek_client = OpenAI(
    api_key=os.getenv('DEEPSEEK_API_KEY'),
    base_url="https://api.deepseek.com"
)

# Состояния для ConversationHandler
WAITING_QUESTION, WAITING_ZODIAC, WAITING_BIRTHDATE, WAITING_PALM_PHOTO = range(4)


def get_main_menu():
    """Создает главное меню бота"""
    keyboard = [
        [InlineKeyboardButton("🔮 Таро", callback_data="tarot")],
        [InlineKeyboardButton("✋ Хиромантия", callback_data="palmistry")],
        [InlineKeyboardButton("⭐ Астрология", callback_data="astrology")],
        [InlineKeyboardButton("🎱 Предсказание", callback_data="prediction")],
        [InlineKeyboardButton("ℹ️ Помощь", callback_data="help")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_tarot_menu():
    """Меню раскладов Таро"""
    keyboard = [
        [InlineKeyboardButton("Карта дня", callback_data="tarot_day")],
        [InlineKeyboardButton("Три карты (прошлое-настоящее-будущее)", callback_data="tarot_three")],
        [InlineKeyboardButton("Расклад на любовь", callback_data="tarot_love")],
        [InlineKeyboardButton("Ответ Да/Нет", callback_data="tarot_yesno")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="back_main")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_astrology_menu():
    """Меню астрологии"""
    keyboard = [
        [InlineKeyboardButton("Гороскоп на сегодня", callback_data="horoscope_today")],
        [InlineKeyboardButton("Гороскоп на неделю", callback_data="horoscope_week")],
        [InlineKeyboardButton("Натальная карта", callback_data="natal_chart")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="back_main")]
    ]
    return InlineKeyboardMarkup(keyboard)


async def ask_deepseek(prompt: str, system_prompt: str = None) -> str:
    """
    Отправляет запрос к DeepSeek API
    """
    try:
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": prompt})

        response = deepseek_client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            temperature=0.9,
            max_tokens=1500
        )

        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Ошибка при обращении к DeepSeek API: {e}")
        return "Извините, произошла ошибка при обращении к магическим силам. Попробуйте позже."


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    welcome_text = (
        f"🔮 Приветствую тебя, {user.first_name}!\n\n"
        "Я - Мистический помощник, твой проводник в мир эзотерики и предсказаний.\n\n"
        "Я могу:\n"
        "🃏 Погадать на картах Таро\n"
        "✋ Прочитать линии на твоей ладони\n"
        "⭐ Составить астрологический прогноз\n"
        "🎱 Предсказать будущее\n\n"
        "Выбери, что тебя интересует:"
    )

    await update.message.reply_text(welcome_text, reply_markup=get_main_menu())


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатий на кнопки"""
    query = update.callback_query
    await query.answer()

    if query.data == "back_main":
        await query.edit_message_text(
            "🔮 Главное меню. Выбери интересующую тебя область:",
            reply_markup=get_main_menu()
        )
        return ConversationHandler.END

    elif query.data == "tarot":
        await query.edit_message_text(
            "🃏 Выбери расклад Таро:",
            reply_markup=get_tarot_menu()
        )

    elif query.data == "astrology":
        await query.edit_message_text(
            "⭐ Выбери тип астрологического прогноза:",
            reply_markup=get_astrology_menu()
        )

    elif query.data == "palmistry":
        await query.edit_message_text(
            "✋ Хиромантия\n\n"
            "Отправь мне фото своей ладони (желательно правой руки) "
            "с хорошим освещением. Или опиши основные линии:\n\n"
            "• Линия жизни (дуга от большого пальца)\n"
            "• Линия сердца (горизонтальная линия вверху)\n"
            "• Линия ума (горизонтальная линия в центре)\n"
            "• Линия судьбы (вертикальная линия)\n\n"
            "Какие из них длинные, короткие, прерывистые?"
        )
        return WAITING_PALM_PHOTO

    elif query.data == "prediction":
        await query.edit_message_text(
            "🎱 Задай мне свой вопрос, и я загляну в будущее...\n\n"
            "Напиши свой вопрос одним сообщением."
        )
        return WAITING_QUESTION

    elif query.data == "help":
        help_text = (
            "ℹ️ Помощь\n\n"
            "Команды бота:\n"
            "/start - Главное меню\n"
            "/help - Эта справка\n\n"
            "Возможности:\n"
            "• Таро - различные расклады карт\n"
            "• Хиромантия - анализ линий на ладони\n"
            "• Астрология - гороскопы и натальные карты\n"
            "• Предсказания - ответы на твои вопросы\n\n"
            "Все предсказания генерируются с помощью AI."
        )
        keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data="back_main")]]
        await query.edit_message_text(help_text, reply_markup=InlineKeyboardMarkup(keyboard))

    # Обработчики Таро
    elif query.data == "tarot_day":
        await handle_tarot_day(query)
    elif query.data == "tarot_three":
        await handle_tarot_three(query)
    elif query.data == "tarot_love":
        await handle_tarot_love(query)
    elif query.data == "tarot_yesno":
        await handle_tarot_yesno(query)

    # Обработчики астрологии
    elif query.data == "horoscope_today":
        await query.edit_message_text("⭐ Введите ваш знак зодиака:")
        return WAITING_ZODIAC
    elif query.data == "horoscope_week":
        await handle_horoscope_week(query, context)
    elif query.data == "natal_chart":
        await query.edit_message_text(
            "🌟 Для натальной карты введите дату рождения в формате ДД.ММ.ГГГГ\n"
            "Например: 15.03.1990"
        )
        return WAITING_BIRTHDATE


# ============= ОБРАБОТЧИКИ ТАРО =============

async def handle_tarot_day(query):
    """Карта дня"""
    await query.edit_message_text("🔮 Вытягиваю карту дня...")

    card = tarot.draw_cards(1)[0]

    system_prompt = (
        "Ты опытный таролог с глубокими знаниями карт Таро. "
        "Дай подробное толкование карты дня. Объясни, что эта карта означает "
        "для человека на сегодняшний день. Пиши мистически и загадочно, но содержательно. "
        "ВАЖНО: Отвечай ТОЛЬКО на русском языке с АБСОЛЮТНО ГРАМОТНОЙ орфографией и пунктуацией. "
        "Проверяй каждое слово на правильность написания. Используй литературный русский язык."
    )

    interpretation = await ask_deepseek(
        f"Выпала карта: {card}. Дай толкование этой карты как карты дня.",
        system_prompt
    )

    response = f"🃏 Карта дня: *{card}*\n\n{interpretation}"

    keyboard = [[InlineKeyboardButton("🔮 Ещё расклад", callback_data="tarot")],
                [InlineKeyboardButton("⬅️ Главное меню", callback_data="back_main")]]

    await query.edit_message_text(response, reply_markup=InlineKeyboardMarkup(keyboard),
                                   parse_mode='Markdown')


async def handle_tarot_three(query):
    """Расклад на три карты"""
    await query.edit_message_text("🔮 Делаю расклад на три карты...")

    cards = tarot.draw_cards(3)

    system_prompt = (
        "Ты опытный таролог. Сделай расклад на три карты: "
        "прошлое, настоящее и будущее. Дай глубокое толкование каждой карты "
        "и общую картину. Пиши мистически, но содержательно. "
        "ВАЖНО: Отвечай ТОЛЬКО на русском языке с АБСОЛЮТНО ГРАМОТНОЙ орфографией и пунктуацией. "
        "Проверяй каждое слово на правильность написания. Используй литературный русский язык."
    )

    interpretation = await ask_deepseek(
        f"Выпали карты:\nПрошлое: {cards[0]}\nНастоящее: {cards[1]}\nБудущее: {cards[2]}\n\n"
        f"Дай подробное толкование этого расклада.",
        system_prompt
    )

    response = (
        f"🃏 Расклад «Прошлое-Настоящее-Будущее»\n\n"
        f"📜 Прошлое: *{cards[0]}*\n"
        f"⏳ Настоящее: *{cards[1]}*\n"
        f"🔮 Будущее: *{cards[2]}*\n\n"
        f"{interpretation}"
    )

    keyboard = [[InlineKeyboardButton("🔮 Ещё расклад", callback_data="tarot")],
                [InlineKeyboardButton("⬅️ Главное меню", callback_data="back_main")]]

    await query.edit_message_text(response, reply_markup=InlineKeyboardMarkup(keyboard),
                                   parse_mode='Markdown')


async def handle_tarot_love(query):
    """Расклад на любовь"""
    await query.edit_message_text("💕 Делаю расклад на любовь...")

    cards = tarot.draw_cards(3)

    system_prompt = (
        "Ты опытный таролог, специализирующийся на любовных раскладах. "
        "Сделай расклад на любовь из трех карт: 1) Ты, 2) Партнер, 3) Отношения. "
        "Дай глубокое толкование. Пиши романтично и мистически. "
        "ВАЖНО: Отвечай ТОЛЬКО на русском языке с АБСОЛЮТНО ГРАМОТНОЙ орфографией и пунктуацией. "
        "Проверяй каждое слово на правильность написания. Используй литературный русский язык."
    )

    interpretation = await ask_deepseek(
        f"Любовный расклад:\nТы: {cards[0]}\nПартнер: {cards[1]}\nОтношения: {cards[2]}\n\n"
        f"Дай подробное толкование.",
        system_prompt
    )

    response = (
        f"💕 Любовный расклад\n\n"
        f"👤 Ты: *{cards[0]}*\n"
        f"💑 Партнер: *{cards[1]}*\n"
        f"❤️ Отношения: *{cards[2]}*\n\n"
        f"{interpretation}"
    )

    keyboard = [[InlineKeyboardButton("🔮 Ещё расклад", callback_data="tarot")],
                [InlineKeyboardButton("⬅️ Главное меню", callback_data="back_main")]]

    await query.edit_message_text(response, reply_markup=InlineKeyboardMarkup(keyboard),
                                   parse_mode='Markdown')


async def handle_tarot_yesno(query):
    """Ответ Да/Нет"""
    await query.edit_message_text("🎱 Спрашиваю карты...")

    card = tarot.draw_cards(1)[0]

    system_prompt = (
        "Ты таролог. Дай ответ Да или Нет на основе выпавшей карты. "
        "Объясни почему карта говорит именно так. Будь загадочным. "
        "ВАЖНО: Отвечай ТОЛЬКО на русском языке с АБСОЛЮТНО ГРАМОТНОЙ орфографией и пунктуацией. "
        "Проверяй каждое слово на правильность написания. Используй литературный русский язык."
    )

    interpretation = await ask_deepseek(
        f"Выпала карта: {card}. Это Да или Нет? Объясни.",
        system_prompt
    )

    response = f"🎱 Карта: *{card}*\n\n{interpretation}"

    keyboard = [[InlineKeyboardButton("🔮 Ещё вопрос", callback_data="tarot")],
                [InlineKeyboardButton("⬅️ Главное меню", callback_data="back_main")]]

    await query.edit_message_text(response, reply_markup=InlineKeyboardMarkup(keyboard),
                                   parse_mode='Markdown')


# ============= ОБРАБОТЧИКИ АСТРОЛОГИИ =============

ZODIAC_SIGNS = [
    "Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева",
    "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы"
]


async def handle_horoscope_week(query, context):
    """Недельный гороскоп для всех знаков"""
    await query.edit_message_text("⭐ Составляю недельный гороскоп...")

    system_prompt = (
        "Ты профессиональный астролог. Составь краткий общий гороскоп на неделю. "
        "Упомяни ключевые астрологические события недели. "
        "Пиши загадочно и мистически. Ответ на русском языке."
    )

    horoscope = await ask_deepseek(
        f"Составь общий гороскоп на неделю. Сегодня {datetime.now().strftime('%d.%m.%Y')}",
        system_prompt
    )

    response = f"⭐ Гороскоп на неделю\n\n{horoscope}"

    keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data="astrology")],
                [InlineKeyboardButton("🏠 Главное меню", callback_data="back_main")]]

    await query.edit_message_text(response, reply_markup=InlineKeyboardMarkup(keyboard))


async def handle_zodiac_horoscope(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Гороскоп по знаку зодиака"""
    zodiac = update.message.text.strip().capitalize()

    if zodiac not in ZODIAC_SIGNS:
        await update.message.reply_text(
            f"Пожалуйста, введите корректный знак зодиака из списка:\n" +
            ", ".join(ZODIAC_SIGNS)
        )
        return WAITING_ZODIAC

    await update.message.reply_text(f"⭐ Составляю гороскоп для {zodiac}...")

    system_prompt = (
        "Ты профессиональный астролог. Составь подробный гороскоп на сегодня "
        "для указанного знака зодиака. Пиши загадочно и мистически. "
        "Ответ на русском языке."
    )

    horoscope = await ask_deepseek(
        f"Составь гороскоп на сегодня для знака {zodiac}. "
        f"Сегодня {datetime.now().strftime('%d.%m.%Y')}",
        system_prompt
    )

    response = f"⭐ Гороскоп для {zodiac}\n\n{horoscope}"

    await update.message.reply_text(response, reply_markup=get_main_menu())
    return ConversationHandler.END


async def handle_natal_chart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Натальная карта"""
    birthdate = update.message.text.strip()

    await update.message.reply_text("🌟 Составляю натальную карту...")

    system_prompt = (
        "Ты опытный астролог. Составь краткую натальную карту для человека, "
        "родившегося в указанную дату. Опиши основные черты характера, "
        "предназначение, сильные стороны. Пиши мистически и вдохновляюще. "
        "Ответ на русском языке."
    )

    natal = await ask_deepseek(
        f"Составь натальную карту для человека, родившегося {birthdate}",
        system_prompt
    )

    response = f"🌟 Натальная карта\nДата рождения: {birthdate}\n\n{natal}"

    await update.message.reply_text(response, reply_markup=get_main_menu())
    return ConversationHandler.END


# ============= ОБРАБОТЧИКИ ХИРОМАНТИИ =============

async def handle_palm_reading(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Чтение по ладони"""
    await update.message.reply_text("✋ Изучаю линии на твоей ладони...")

    system_prompt = (
        "Ты опытный хиромант с глубокими знаниями чтения по руке. "
        "Проанализируй описание ладони или скажи что видишь фото и дай подробное толкование. "
        "Опиши что означают линии жизни, сердца, ума, судьбы для этого человека. "
        "Расскажи о характере человека, его судьбе и будущем. "
        "Пиши загадочно и мистически. Ответ на русском языке."
    )

    # Проверяем что прислал пользователь - текст или фото
    if update.message.photo:
        prompt = (
            "Пользователь прислал фото своей ладони. "
            "Дай подробное хиромантическое толкование, основываясь на общих принципах хиромантии. "
            "Опиши значение основных линий и что они говорят о характере и судьбе человека."
        )
    elif update.message.text:
        description = update.message.text
        prompt = f"Пользователь описал свою ладонь: {description}\n\nДай хиромантическое толкование на основе этого описания."
    else:
        await update.message.reply_text(
            "Пожалуйста, отправьте фото ладони или опишите основные линии текстом."
        )
        return WAITING_PALM_PHOTO

    try:
        reading = await ask_deepseek(prompt, system_prompt)
        result = f"✋ Чтение по ладони\n\n{reading}"

    except Exception as e:
        logger.error(f"Ошибка при анализе: {e}")
        result = "Извините, произошла ошибка. Попробуйте позже."

    await update.message.reply_text(result, reply_markup=get_main_menu())
    return ConversationHandler.END


# ============= ОБЩИЕ ПРЕДСКАЗАНИЯ =============

async def handle_prediction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ответ на вопрос пользователя"""
    question = update.message.text.strip()

    await update.message.reply_text("🔮 Заглядываю в будущее...")

    system_prompt = (
        "Ты мистический предсказатель и ясновидящий. "
        "Дай загадочное и глубокое предсказание на вопрос пользователя. "
        "Будь мистичным, используй образы и метафоры. "
        "Ответ на русском языке."
    )

    prediction = await ask_deepseek(
        f"Вопрос: {question}\n\nДай предсказание.",
        system_prompt
    )

    response = f"🔮 Предсказание\n\nТвой вопрос: _{question}_\n\n{prediction}"

    await update.message.reply_text(response, reply_markup=get_main_menu(),
                                     parse_mode='Markdown')
    return ConversationHandler.END


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    help_text = (
        "ℹ️ Помощь\n\n"
        "Команды бота:\n"
        "/start - Главное меню\n"
        "/help - Эта справка\n\n"
        "Используй меню для навигации по функциям бота."
    )
    await update.message.reply_text(help_text, reply_markup=get_main_menu())


def main():
    """Главная функция запуска бота"""
    token = os.getenv('TELEGRAM_BOT_TOKEN')

    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN не найден в переменных окружения!")

    # Создание приложения
    application = Application.builder().token(token).build()

    # Обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))

    # ConversationHandler для астрологии (знак зодиака)
    zodiac_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler, pattern="^horoscope_today$")],
        states={
            WAITING_ZODIAC: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_zodiac_horoscope)]
        },
        fallbacks=[CommandHandler("start", start)]
    )

    # ConversationHandler для натальной карты
    natal_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler, pattern="^natal_chart$")],
        states={
            WAITING_BIRTHDATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_natal_chart)]
        },
        fallbacks=[CommandHandler("start", start)]
    )

    # ConversationHandler для хиромантии
    palm_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler, pattern="^palmistry$")],
        states={
            WAITING_PALM_PHOTO: [
                MessageHandler(filters.PHOTO, handle_palm_reading),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_palm_reading)
            ]
        },
        fallbacks=[CommandHandler("start", start)]
    )

    # ConversationHandler для предсказаний
    prediction_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler, pattern="^prediction$")],
        states={
            WAITING_QUESTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_prediction)]
        },
        fallbacks=[CommandHandler("start", start)]
    )

    # Добавление ConversationHandlers
    application.add_handler(zodiac_conv_handler)
    application.add_handler(natal_conv_handler)
    application.add_handler(palm_conv_handler)
    application.add_handler(prediction_conv_handler)

    # Обработчик кнопок (должен быть после ConversationHandlers)
    application.add_handler(CallbackQueryHandler(button_handler))

    # Запуск бота
    logger.info("Бот запущен!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
