# Weather Bot v2.1 - 2025-12-07
# Добавлено: поддержка python-telegram-bot[webhooks], корректный запуск вебхуков

import os
import logging
import asyncio
import sys
from datetime import datetime
import pytz
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from config import Config
from database import Database
import requests
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import platform

# Настройка логирования с учетом Windows кодировки
log_date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
log_filename = f"bot_log_{log_date}.log"

# Создаем обработчики с правильной кодировкой для Windows
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

file_handler = logging.FileHandler(log_filename, encoding='utf-8')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(console_handler)
logger.addHandler(file_handler)

# Дополнительно для Windows: устанавливаем кодировку UTF-8 для консоли
if platform.system() == "Windows":
    try:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
        logger.info("✅ Установлена кодировка UTF-8 для консоли Windows")
    except Exception as e:
        logger.warning(f"⚠️ Не удалось установить UTF-8 для консоли: {e}")

# Инициализация базы данных
db = Database()

# ===== ФУНКЦИИ РАБОТЫ С ПОГОДОЙ =====
def get_weather(city):
    """Получить текущую погоду для города"""
    try:
        params = {
            'q': city,
            'appid': Config.OPENWEATHER_API,
            'units': 'metric',
            'lang': 'ru'
        }
        
        response = requests.get(Config.WEATHER_API_URL, params=params, timeout=10)
        data = response.json()
        
        if response.status_code != 200:
            logger.error(f"❌ Ошибка API погоды: {data.get('message', 'Unknown error')}")
            return f"❌ Не удалось получить погоду для {city}. Проверьте название города."
        
        # Извлекаем данные
        temp = data['main']['temp']
        feels_like = data['main']['feels_like']
        humidity = data['main']['humidity']
        pressure = data['main']['pressure']
        wind_speed = data['wind']['speed']
        weather_desc = data['weather'][0]['description'].capitalize()
        
        # Эмодзи для погоды
        weather_emoji = "🌤"
        if "дождь" in weather_desc.lower():
            weather_emoji = "🌧"
        elif "снег" in weather_desc.lower():
            weather_emoji = "❄️"
        elif "облак" in weather_desc.lower():
            weather_emoji = "☁️"
        elif "ясно" in weather_desc.lower():
            weather_emoji = "☀️"
        
        return (
            f"{weather_emoji} **Текущая погода в {city}**\n\n"
            f"🌡 **Температура:** {temp:.1f}°C (ощущается как {feels_like:.1f}°C)\n"
            f"💧 **Влажность:** {humidity}%\n"
            f"🌬 **Давление:** {pressure} гПа\n"
            f"💨 **Ветер:** {wind_speed} м/с\n"
            f"☁️ **{weather_desc}**"
        )
    except Exception as e:
        logger.error(f"❌ Ошибка получения погоды для {city}: {e}")
        return "❌ Произошла ошибка при получении погоды. Попробуйте позже."

def get_forecast(city, days=1):
    """Получить прогноз погоды на несколько дней"""
    try:
        params = {
            'q': city,
            'appid': Config.OPENWEATHER_API,
            'units': 'metric',
            'lang': 'ru',
            'cnt': days * 8  # 8 замеров в день (каждые 3 часа)
        }
        
        response = requests.get(Config.FORECAST_API_URL, params=params, timeout=10)
        data = response.json()
        
        if response.status_code != 200:
            return f"❌ Не удалось получить прогноз для {city}."
        
        forecast_text = f"📅 **Прогноз погоды в {city} на {days} дней**\n\n"
        
        current_date = None
        for item in data['list']:
            dt = datetime.fromtimestamp(item['dt'])
            date_str = dt.strftime("%d.%m")
            time_str = dt.strftime("%H:%M")
            
            if date_str != current_date:
                current_date = date_str
                forecast_text += f"\n**{current_date}**\n"
            
            temp = item['main']['temp']
            desc = item['weather'][0]['description'].capitalize()
            forecast_text += f"⏰ {time_str}: {temp:.1f}°C, {desc}\n"
        
        return forecast_text
    except Exception as e:
        logger.error(f"❌ Ошибка получения прогноза для {city}: {e}")
        return "❌ Произошла ошибка при получении прогноза."

def get_clothing_advice(temperature):
    """Рекомендации по одежде на основе температуры"""
    try:
        temp = float(temperature)
        
        if temp < -10:
            return "🧥 **Очень холодно!**\nНужно: шуба/пуховик, шапка, шарф, перчатки, теплые ботинки"
        elif -10 <= temp < 0:
            return "🧥 **Холодно!**\nНужно: теплая куртка, шапка, шарф, перчатки"
        elif 0 <= temp < 10:
            return "🧥 **Прохладно!**\nНужно: демисезонная куртка, водолазка, джинсы"
        elif 10 <= temp < 20:
            return "👕 **Комфортно!**\nНужно: свитер/толстовка, легкая куртка, джинсы"
        elif 20 <= temp < 25:
            return "👕 **Тепло!**\nНужно: футболка, шорты/юбка, легкая обувь"
        else:
            return "👕 **Очень тепло!**\nНужно: шорты, майка, солнцезащитные очки, головной убор"
    except:
        return "👕 **Рекомендации по одежде**\nНа основе текущей температуры"

# ===== ФУНКЦИИ РАБОТЫ С ПРАЗДНИКАМИ =====
def get_holiday_info():
    """Получить информацию о сегодняшних праздниках (упрощенная версия)"""
    today = datetime.now().strftime("%d.%m")
    
    # Список основных российских праздников (можно расширить)
    holidays = {
        "01.01": "🎉 Новый год",
        "07.01": "🕯 Рождество Христово",
        "23.02": "🎖 День защитника Отечества",
        "08.03": "💐 Международный женский день",
        "01.05": "노동 День труда",
        "09.05": "🕊 День Победы",
        "12.06": "🇷🇺 День России",
        "04.11": "🇷🇺 День народного единства"
    }
    
    return holidays.get(today, None)

# ===== ФУНКЦИИ ДЛЯ УВЕДОМЛЕНИЙ =====
def get_digest_type(current_time):
    """Определить тип дайджеста по времени суток"""
    hour = current_time.hour
    
    if 5 <= hour < 12:
        return "Утренний"
    elif 12 <= hour < 17:
        return "Дневной"
    elif 17 <= hour < 22:
        return "Вечерний"
    else:
        return "Ночной"

def format_digest_message(city, weather_info, clothing_advice, holiday_info=None):
    """Сформировать сообщение дайджеста с учетом времени суток"""
    moscow_tz = pytz.timezone('Europe/Moscow')
    current_time = datetime.now(moscow_tz)
    digest_type = get_digest_type(current_time)
    
    # Определение приветствия по времени суток
    if digest_type == "Утренний":
        greeting = "Доброе утро!"
        intro = "🌅 Начни день с правильного настроения!"
    elif digest_type == "Дневной":
        greeting = "Добрый день!"
        intro = "☀️ Середина дня — самое время проверить погоду!"
    elif digest_type == "Вечерний":
        greeting = "Добрый вечер!"
        intro = "🌆 Вечер — время планировать завтрашний день!"
    else:
        greeting = "Доброй ночи!"
        intro = "🌙 Поздравляю, ты сегодня победил! Отдыхай, а завтра будет новый день."
    
    # Формирование сообщения
    digest_message = (
        f"📨 **{digest_type} дайджест для {city}**\n\n"
        f"✨ **{greeting}**\n"
        f"{intro}\n\n"
        f"{weather_info}\n\n"
        f"{clothing_advice}"
    )
    
    # Добавляем информацию о празднике, если есть
    if holiday_info:
        digest_message += f"\n\n🎉 **Сегодня празднуем:** {holiday_info}"
    
    digest_message += "\n\n😊 Хорошего дня!"
    
    return digest_message

# ===== ОБРАБОТЧИКИ СООБЩЕНИЙ =====
MAIN_MENU_KEYBOARD = [
    [KeyboardButton("🌤 Текущая погода"), KeyboardButton("📅 Прогноз на 3 дня")],
    [KeyboardButton("👗 Рекомендации по одежде"), KeyboardButton("🎉 Праздники сегодня")],
    [KeyboardButton("📍 Изменить город"), KeyboardButton("⏰ Настроить уведомления")],
    [KeyboardButton("🔄 Сбросить настройки")]
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    user = update.effective_user
    user_id = user.id
    
    # Создаем или обновляем пользователя в БД
    db.create_or_update_user(
        user_id=user_id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name
    )
    
    # Получаем настройки пользователя
    user_settings = db.get_user(user_id)
    
    welcome_message = (
        f"👋 Привет, {user.first_name}!\n\n"
        f"🌤 Я — твой персональный погодный помощник!\n\n"
        f"🏙 **Твой город:** {user_settings['city']}\n"
        f"⏰ **Уведомления:** {', '.join(user_settings['notification_times'])} (МСК)\n\n"
        f"Выбери действие из меню ниже:"
    )
    
    reply_markup = ReplyKeyboardMarkup(MAIN_MENU_KEYBOARD, resize_keyboard=True)
    await update.message.reply_text(welcome_message, reply_markup=reply_markup, parse_mode='Markdown')

async def weather_current(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Текущая погода"""
    user_id = update.effective_user.id
    user_settings = db.get_user(user_id)
    city = user_settings['city']
    
    weather_info = get_weather(city)
    await update.message.reply_text(weather_info, parse_mode='Markdown')

async def weather_forecast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Прогноз на 3 дня"""
    user_id = update.effective_user.id
    user_settings = db.get_user(user_id)
    city = user_settings['city']
    
    forecast_info = get_forecast(city, days=3)
    await update.message.reply_text(forecast_info, parse_mode='Markdown')

async def clothing_advice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Рекомендации по одежде"""
    user_id = update.effective_user.id
    user_settings = db.get_user(user_id)
    city = user_settings['city']
    
    # Получаем текущую температуру
    try:
        params = {
            'q': city,
            'appid': Config.OPENWEATHER_API,
            'units': 'metric'
        }
        response = requests.get(Config.WEATHER_API_URL, params=params, timeout=10)
        data = response.json()
        
        if response.status_code == 200:
            temp = data['main']['temp']
            advice = get_clothing_advice(temp)
        else:
            advice = "👕 **Рекомендации по одежде**\nНе удалось определить температуру. Используйте общий совет выше."
    except Exception as e:
        logger.error(f"❌ Ошибка получения температуры для одежды: {e}")
        advice = "👕 **Рекомендации по одежде**\nПроизошла ошибка при получении данных."
    
    await update.message.reply_text(advice, parse_mode='Markdown')

async def holidays_today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Праздники сегодня"""
    holiday = get_holiday_info()
    
    if holiday:
        message = f"🎉 **Сегодня празднуем:**\n\n{holiday}"
    else:
        message = "📅 **Сегодня нет официальных праздников**\n\nНо это не повод не радоваться! 😊"
    
    await update.message.reply_text(message, parse_mode='Markdown')

async def change_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Изменить город"""
    message = (
        "📍 **Введите название города:**\n\n"
        "Например: Москва, Санкт-Петербург, Новосибирск\n\n"
        "Отправь название, и я обновлю твои настройки!"
    )
    await update.message.reply_text(message, parse_mode='Markdown')
    
    # Устанавливаем состояние ожидания города
    context.user_data['awaiting_city'] = True
    context.user_data['awaiting_notifications'] = False

async def handle_city_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ввода города"""
    if context.user_data.get('awaiting_city'):
        city = update.message.text.strip()
        user_id = update.effective_user.id
        
        # Обновляем город в БД
        success = db.update_user_city(user_id, city)
        
        if success:
            message = f"✅ **Город успешно изменен!**\n\n🏙 Теперь твой город: {city}"
        else:
            message = "❌ **Ошибка при обновлении города.** Попробуй еще раз."
        
        # Сбрасываем состояние
        context.user_data['awaiting_city'] = False
        
        reply_markup = ReplyKeyboardMarkup(MAIN_MENU_KEYBOARD, resize_keyboard=True)
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')

async def setup_notifications(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Настроить уведомления"""
    message = (
        "⏰ **Настройка уведомлений**\n\n"
        f"Максимум {Config.MAX_NOTIFICATION_TIMES} уведомлений в день.\n\n"
        "Отправь время в формате ЧЧ:ММ (например: 08:00, 18:30)\n"
        "**Время указывается по Московскому времени (МСК, UTC+3)**\n"
        "Для нескольких уведомлений отправь через запятую:\n"
        "`08:00, 13:00, 18:00`\n\n"
        "Текущие настройки: "
    )
    
    user_id = update.effective_user.id
    user_settings = db.get_user(user_id)
    current_times = ', '.join(user_settings['notification_times'])
    
    message += f"{current_times} (МСК)"
    
    await update.message.reply_text(message, parse_mode='Markdown')
    context.user_data['awaiting_notifications'] = True
    context.user_data['awaiting_city'] = False

async def handle_notifications_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ввода времени уведомлений"""
    if context.user_data.get('awaiting_notifications'):
        input_text = update.message.text.strip()
        user_id = update.effective_user.id
        
        # Разбираем введенные времена
        times = [t.strip() for t in input_text.split(',')]
        
        # Обновляем настройки в БД
        new_times = db.update_notification_times(user_id, times)
        
        # ИСПРАВЛЕНИЕ: правильное сообщение об уведомлениях
        message = f"✅ **Уведомления настроены!**\n\n⏰ Теперь ты будешь получать уведомления в:\n{', '.join(new_times)} (МСК)"
        
        # Сбрасываем состояние
        context.user_data['awaiting_notifications'] = False
        
        reply_markup = ReplyKeyboardMarkup(MAIN_MENU_KEYBOARD, resize_keyboard=True)
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')
        
        # ОБНОВЛЕНИЕ ПЛАНИРОВЩИКА ПОСЛЕ ИЗМЕНЕНИЯ НАСТРОЕК
        if hasattr(context.application, 'scheduler') and context.application.scheduler:
            logger.info(f"🔄 Обновление расписания уведомлений для пользователя {user_id} после изменения настроек")
            # Удаляем все текущие задачи пользователя
            user_jobs = [job for job in context.application.scheduler.get_jobs() if str(user_id) in job.id]
            for job in user_jobs:
                logger.info(f"🗑️ Удаляем задание: {job.id}")
                job.remove()
            
            # Добавляем новые задачи
            await schedule_user_digests(context.application, user_id, new_times)

async def reset_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сбросить настройки"""
    user_id = update.effective_user.id
    success = db.reset_user_settings(user_id)
    
    if success:
        message = (
            "🔄 **Настройки сброшены до базовых!**\n\n"
            "🏙 Город: Москва\n"
            "⏰ Уведомления: 08:00, 18:00 (МСК)\n\n"
            "Можешь изменить их в меню."
        )
    else:
        message = "❌ **Ошибка при сбросе настроек.** Попробуй позже."
    
    reply_markup = ReplyKeyboardMarkup(MAIN_MENU_KEYBOARD, resize_keyboard=True)
    await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')
    
    # ОБНОВЛЕНИЕ ПЛАНИРОВЩИКА ПОСЛЕ СБРОСА НАСТРОЕК
    if hasattr(context.application, 'scheduler') and context.application.scheduler:
        logger.info(f"🔄 Обновление расписания уведомлений для пользователя {user_id} после сброса настроек")
        # Удаляем все текущие задачи пользователя
        user_jobs = [job for job in context.application.scheduler.get_jobs() if str(user_id) in job.id]
        for job in user_jobs:
            logger.info(f"🗑️ Удаляем задание: {job.id}")
            job.remove()
        
        # Добавляем новые задачи с базовыми настройками
        default_times = ['08:00', '18:00']
        await schedule_user_digests(context.application, user_id, default_times)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help"""
    help_text = """
    🆘 **Доступные команды и функции:**

    🌤 **Погода:**
    • Текущая погода - показать погоду сейчас
    • Прогноз на 3 дня - подробный прогноз
    
    👗 **Одежда:**
    • Рекомендации по одежде - советы на основе температуры
    
    🗓 **Праздники:**
    • Праздники сегодня - узнать о праздниках
    
    ⚙️ **Настройки:**
    • Изменить город - выбрать другой город
    • Настроить уведомления - установить время для дайджестов (по Московскому времени)
    • Сбросить настройки - вернуть базовые настройки
    
    🤖 **Тестовые команды:**
    • /test_notify - отправить тестовое уведомление сейчас
    • /list_jobs - показать все запланированные уведомления
    
    🤖 **Команды:**
    /start - начать работу
    /help - показать эту справку
    
    Все функции доступны через кнопки в меню!
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def unknown_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка неизвестных сообщений"""
    if context.user_data.get('awaiting_city'):
        await handle_city_input(update, context)
    elif context.user_data.get('awaiting_notifications'):
        await handle_notifications_input(update, context)
    else:
        message = (
            "❓ **Неизвестная команда**\n\n"
            "Используй кнопки в меню или команду /help для справки.\n\n"
            "Что ты хочешь сделать?"
        )
        reply_markup = ReplyKeyboardMarkup(MAIN_MENU_KEYBOARD, resize_keyboard=True)
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')

# ===== ФОНОВЫЕ УВЕДОМЛЕНИЯ =====
async def send_daily_digest(application, user_id: int):
    """Отправить ежедневный дайджест"""
    try:
        user_settings = db.get_user(user_id)
        if not user_settings:
            logger.warning(f"👤 Пользователь {user_id} не найден при отправке уведомления")
            return
        
        city = user_settings['city']
        
        # Получаем погоду
        weather_info = get_weather(city)
        
        # Получаем рекомендации по одежде
        try:
            params = {
                'q': city,
                'appid': Config.OPENWEATHER_API,
                'units': 'metric'
            }
            response = requests.get(Config.WEATHER_API_URL, params=params, timeout=10)
            data = response.json()
            
            if response.status_code == 200:
                temp = data['main']['temp']
                clothing_advice = get_clothing_advice(temp)
            else:
                clothing_advice = "👕 Не удалось получить рекомендации по одежде."
        except Exception as e:
            logger.error(f"❌ Ошибка получения одежды для дайджеста: {e}")
            clothing_advice = "👕 Рекомендации по одежде недоступны."
        
        # Получаем праздники
        holiday_info = get_holiday_info()
        
        # Формируем дайджест с учетом времени суток
        digest_message = format_digest_message(city, weather_info, clothing_advice, holiday_info)
        
        await application.bot.send_message(
            chat_id=user_id,
            text=digest_message,
            parse_mode='Markdown'
        )
        
        logger.info(f"✅Отправлен {get_digest_type(datetime.now(pytz.timezone('Europe/Moscow')))} дайджест пользователю {user_id}")
    except Exception as e:
        logger.error(f"❌ Ошибка отправки дайджеста для {user_id}: {e}", exc_info=True)

async def schedule_user_digests(application, user_id, times):
    """Запланировать уведомления для конкретного пользователя"""
    moscow_tz = pytz.timezone('Europe/Moscow')
    
    for time_str in times:
        try:
            hour, minute = map(int, time_str.split(':'))
            
            # Настраиваем триггер в московском времени
            trigger = CronTrigger(
                hour=hour,
                minute=minute,
                timezone="Europe/Moscow"
            )
            
            # ID задания должно быть уникальным
            job_id = f"digest_{user_id}_{time_str.replace(':', '_')}"
            
            # Добавляем задание
            application.scheduler.add_job(
                send_daily_digest,
                trigger,
                args=[application, user_id],
                id=job_id,
                replace_existing=True,
                misfire_grace_time=300  # 5 минут на обработку пропущенного задания
            )
            
            # Логируем без эмодзи для Windows
            logger.info(f"⏰ Запланировано уведомление для пользователя {user_id} в {time_str} (МСК)")
        except Exception as e:
            logger.error(f"❌ Ошибка планирования для пользователя {user_id}, время {time_str}: {e}")

async def schedule_daily_digests(application):
    """Настроить расписание для дайджестов всех пользователей"""
    try:
        # Инициализируем планировщик, если он еще не создан
        if not hasattr(application, 'scheduler') or application.scheduler is None:
            moscow_tz = pytz.timezone('Europe/Moscow')
            scheduler = AsyncIOScheduler(timezone=moscow_tz)
            scheduler.start()
            application.scheduler = scheduler
            logger.info("✅ Планировщик уведомлений инициализирован")
        
        # Получаем всех пользователей с их настройками уведомлений
        users = db.get_all_users_with_notifications()
        
        for user in users:
            user_id = user['user_id']
            notification_times = user['notification_times']
            
            # Запланировать уведомления для этого пользователя
            await schedule_user_digests(application, user_id, notification_times)
        
        logger.info(f"✅ Запланированы уведомления для {len(users)} пользователей")
        return application.scheduler
    except Exception as e:
        logger.error(f"❌ Ошибка при настройке расписания уведомлений: {e}", exc_info=True)
        return None

# ===== ТЕСТОВЫЕ ФУНКЦИИ ДЛЯ ДИАГНОСТИКИ =====
async def test_notify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Тестовое уведомление (для проверки работы)"""
    user_id = update.effective_user.id
    await send_daily_digest(context.application, user_id)
    await update.message.reply_text("✅ Тестовое уведомление отправлено немедленно!")

async def list_jobs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать все запланированные задачи"""
    if not hasattr(context.application, 'scheduler') or context.application.scheduler is None:
        await update.message.reply_text("❌ Планировщик не запущен")
        return
    
    jobs = context.application.scheduler.get_jobs()
    if not jobs:
        await update.message.reply_text("📋 Нет запланированных заданий")
        return
    
    message = f"📋 **Запланировано заданий: {len(jobs)}**\n\n"
    current_time = datetime.now(pytz.timezone('Europe/Moscow'))
    message += f"🕒 **Текущее время (МСК):** {current_time.strftime('%H:%M:%S')}\n\n"
    
    for job in jobs:
        next_run = job.next_run_time.astimezone(pytz.timezone('Europe/Moscow')).strftime('%H:%M:%S') if job.next_run_time else "Неизвестно"
        message += f"• `{job.id}` - следующий запуск: {next_run} (МСК)\n"
    
    await update.message.reply_text(message, parse_mode='Markdown')

# ===== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =====
async def shutdown_application(application):
    """Корректное завершение работы приложения"""
    logger.info("🔄 Начинаю корректное завершение работы бота...")
    
    # Останавливаем планировщик
    if hasattr(application, 'scheduler') and application.scheduler:
        try:
            application.scheduler.shutdown(wait=False)
            logger.info("✅ Планировщик уведомлений остановлен")
        except Exception as e:
            logger.error(f"❌ Ошибка при остановке планировщика: {e}")
    
    # Останавливаем приложение
    try:
        await application.stop()
        await application.shutdown()
        logger.info("✅ Приложение корректно завершило работу")
    except Exception as e:
        logger.error(f"❌ Ошибка при завершении приложения: {e}")

# ===== ФУНКЦИИ ИНИЦИАЛИЗАЦИИ =====
async def post_init(application: Application) -> None:
    """Действия после инициализации приложения"""
    logger.info("🔄 Запуск инициализации бота...")
    
    # Проверяем конфигурацию
    Config.validate()
    
    # Запускаем планировщик уведомлений
    await schedule_daily_digests(application)
    
    logger.info("✅ Бот успешно инициализирован!")

# ===== ОСНОВНАЯ ФУНКЦИЯ ЗАПУСКА =====
def main():
    """Основная функция запуска бота для PythonAnywhere"""
    try:
        # Проверяем конфигурацию
        Config.validate()
        
        # Создаем приложение
        application = Application.builder().token(Config.BOT_TOKEN).post_init(post_init).build()
        
        # Регистрируем обработчики
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("test_notify", test_notify))
        application.add_handler(CommandHandler("list_jobs", list_jobs))
        
        # Обработчики кнопок
        application.add_handler(MessageHandler(filters.Regex("^🌤 Текущая погода$"), weather_current))
        application.add_handler(MessageHandler(filters.Regex("^📅 Прогноз на 3 дня$"), weather_forecast))
        application.add_handler(MessageHandler(filters.Regex("^👗 Рекомендации по одежде$"), clothing_advice))
        application.add_handler(MessageHandler(filters.Regex("^🎉 Праздники сегодня$"), holidays_today))
        application.add_handler(MessageHandler(filters.Regex("^📍 Изменить город$"), change_city))
        application.add_handler(MessageHandler(filters.Regex("^⏰ Настроить уведомления$"), setup_notifications))
        application.add_handler(MessageHandler(filters.Regex("^🔄 Сбросить настройки$"), reset_settings))
        
        # Обработчики текстового ввода
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown_message))
        
        # ===== ЗАПУСК БОТА НА PYTHONANYWHERE =====
        logger.info("🚀 Запуск бота на PythonAnywhere...")
        
        if Config.WEBHOOK_URL:
            # Режим вебхуков для PythonAnywhere
            logger.info(f"🌐 Запуск бота в режиме вебхуков на порту {Config.PORT}")
            logger.info(f"🔗 Вебхук URL: {Config.WEBHOOK_URL}")
            
            # Для Python 3.12 и вебхуков используем этот подход
            application.run_webhook(
                listen="0.0.0.0",
                port=Config.PORT,
                webhook_url=Config.WEBHOOK_URL,
                drop_pending_updates=True,
                secret_token=None  # Не используем секретный токен для простоты
            )
        else:
            # Локальный режим с поллингом (для тестирования)
            logger.info("💻 Запуск бота в локальном режиме (поллинг)")
            application.run_polling(drop_pending_updates=True)
            
    except Exception as e:
        logger.critical(f"🔥 КРИТИЧЕСКАЯ ОШИБКА при запуске: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()