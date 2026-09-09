import logging
import time
import requests
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    ContextTypes,
)

# ========== НАСТРОЙКИ (ЗАМЕНИ НА СВОИ) ==========
BOT_TOKEN = ""
GIGACHAT_AUTH_KEY = ""

# URL для GigaChat
GIGACHAT_AUTH_URL = "h"
GIGACHAT_API_URL = "https://"

# ========== ЛОГГИРОВАНИЕ ==========
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ========== СОСТОЯНИЯ ДИАЛОГОВ ==========
AGE, INCOME, SAVINGS, APARTMENT_COST = range(4)
CITY, CATEGORY, ROOMS, PRICE_MIN, PRICE_MAX = range(100, 105)

# ==================== СИМУЛЯЦИЯ ЖИЗНИ ====================
def calculate_scenario(age, income, savings, apartment_cost):
    """Рассчитывает два пути: ипотека vs аренда + инвестиции."""
    mortgage_rate = 0.10
    mortgage_years = 10
    down_payment_pct = 0.20
    rent = 35000
    invest_return = 0.08
    income_growth = 0.07

    down_payment = apartment_cost * down_payment_pct
    loan_amount = apartment_cost - down_payment

    r_monthly = mortgage_rate / 12
    n_months = mortgage_years * 12
    if r_monthly > 0:
        monthly_payment = loan_amount * (r_monthly * (1 + r_monthly) ** n_months) / (
            (1 + r_monthly) ** n_months - 1
        )
    else:
        monthly_payment = loan_amount / n_months

    yearly_mortgage = monthly_payment * 12
    remaining_savings = max(savings - down_payment, 0)

    years = [5, 10, 15]
    result = {
        "mortgage_path": [],
        "rent_path": [],
        "monthly_payment": monthly_payment
    }

    mortgage_savings = remaining_savings
    rent_savings = savings
    current_income = income

    for year in range(1, 16):
        if year > 1:
            current_income *= (1 + income_growth)

        # Путь ипотеки
        free_cash_m = current_income * 12 - yearly_mortgage
        if free_cash_m > 0:
            mortgage_savings += free_cash_m * 0.5
        mortgage_savings *= (1 + invest_return)

        # Путь аренды
        free_cash_r = current_income * 12 - rent * 12
        if free_cash_r > 0:
            rent_savings += free_cash_r * 0.7
        rent_savings *= (1 + invest_return)

        if year in years:
            result["mortgage_path"].append({
                "year": year,
                "age": age + year,
                "savings": round(mortgage_savings),
                "apartment_value": round(apartment_cost * (1 + 0.03) ** year)
            })

            result["rent_path"].append({
                "year": year,
                "age": age + year,
                "savings": round(rent_savings),
                "apartment_value": 0
            })

    return result


def format_scenario(data, scenario):
    """Форматирует результат симуляции в читаемый текст."""
    text = "📊 *Прогноз на основе твоих данных*\n\n"
    text += f"💰 Ежемесячный платёж по ипотеке: {scenario['monthly_payment']:,.0f} ₽\n"
    text += f"🏠 Аренда такой же квартиры: 45 000 ₽/мес\n\n"

    text += "*Если купишь в ипотеку:*\n"
    for p in scenario["mortgage_path"]:
        text += (
            f"• {p['year']} лет (тебе {p['age']}): "
            f"накопления ~{p['savings']:,} ₽, "
            f"квартира ~{p['apartment_value']:,} ₽\n"
        )

    text += "\n*Если снимаешь и инвестируешь:*\n"
    for p in scenario["rent_path"]:
        text += (
            f"• {p['year']} лет (тебе {p['age']}): "
            f"накопления ~{p['savings']:,} ₽, жилья нет\n"
        )

    total_m = scenario["mortgage_path"][-1]["savings"] + scenario["mortgage_path"][-1]["apartment_value"]
    total_r = scenario["rent_path"][-1]["savings"]
    text += f"\n*Итог через 15 лет:*\n"
    text += f"• Ипотека: капитал ≈ {total_m:,} ₽\n"
    text += f"• Аренда: капитал ≈ {total_r:,} ₽\n"
    text += "\n✨ Для персональной истории — /story"
    return text


# ==================== GIGACHAT ====================
def get_gigachat_token():
    """Получает токен GigaChat по готовому Authorization Key."""
    payload = {"scope": "GIGACHAT_API_PERS"}
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
        "RqUID": str(int(time.time() * 1000)),
        "Authorization": GIGACHAT_AUTH_KEY
    }
    try:
        resp = requests.post(GIGACHAT_AUTH_URL, data=payload, headers=headers, verify=False)
        resp.raise_for_status()
        return resp.json()["access_token"]
    except Exception as e:
        logger.error(f"Ошибка получения токена GigaChat: {e}")
        raise


def generate_life_story(data, scenario):
    """Генерирует рассказ о трёх вариантах жизни через GigaChat."""
    prompt = f"""
Ты — AI Life Simulator. Напиши живую историю с тремя сценариями жизни на 15 лет.

Данные пользователя:
- Возраст: {data['age']} лет
- Доход: {data['income']:,.0f} ₽/мес
- Накопления: {data['savings']:,.0f} ₽
- Цена квартиры: {data['apartment_cost']:,.0f} ₽
- Ипотечный платёж: {scenario['monthly_payment']:,.0f} ₽/мес
- Аренда: 35 000 ₽/мес

Финансовые прогнозы:
- Ипотека: {scenario['mortgage_path']}
- Аренда: {scenario['rent_path']}

Опиши три пути с эмодзи и деталями:
1. 🏠 Стабильная ипотека — покупка сейчас, семья, ребёнок к 33-35, карьера в найме.
2. 🕊 Свобода и инвестиции — аренда, накопления, покупка жилья позже за наличные.
3. 🚀 Рисковый рывок — студия, переезд в Москву, стартап, высокий доход после 40.

Формат: живой блог, 600-800 слов. Начни с заголовка "📖 Твоя книга судьбы".
"""
    try:
        token = get_gigachat_token()
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
        payload = {
            "model": "GigaChat",
            "messages": [
                {
                    "role": "system",
                    "content": "Ты — талантливый писатель и финансовый аналитик. Создаёшь реалистичные, вдохновляющие истории."
                },
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.8,
            "max_tokens": 1500,
            "stream": False
        }
        resp = requests.post(GIGACHAT_API_URL, json=payload, headers=headers, verify=False)
        if resp.status_code == 401:
            token = get_gigachat_token()
            headers["Authorization"] = f"Bearer {token}"
            resp = requests.post(GIGACHAT_API_URL, json=payload, headers=headers, verify=False)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
    except Exception as e:
        logger.error(f"Ошибка генерации истории: {e}")
        return (
            "😔 Не удалось создать историю. Возможные причины:\n"
            "• Закончились токены GigaChat\n"
            "• Проблемы с сетью\n"
            "Попробуйте позже или проверьте /start"
        )


# ==================== ОБРАБОТЧИКИ СИМУЛЯЦИИ ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "👋 Привет! Я AI Life Simulator.\n\n"
        "Помогу заглянуть в будущее и понять, что будет, если купить квартиру.\n"
        "А ещё могу найти жильё на Avito и Циан.\n\n"
        "Для начала — сколько тебе лет? (введи число)"
    )
    return AGE


async def get_age(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message.text.isdigit():
        await update.message.reply_text("🔢 Введи возраст числом (например, 30).")
        return AGE
    context.user_data["age"] = int(update.message.text)
    await update.message.reply_text("💼 Какой у тебя среднемесячный доход (чистыми, ₽)?")
    return INCOME


async def get_income(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        income = float(update.message.text.replace(",", ".").replace(" ", ""))
    except ValueError:
        await update.message.reply_text("🔢 Введи число, например: 150000")
        return INCOME
    context.user_data["income"] = income
    await update.message.reply_text("🏦 Сколько сейчас накоплений (₽)?")
    return SAVINGS


async def get_savings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        savings = float(update.message.text.replace(",", ".").replace(" ", ""))
    except ValueError:
        await update.message.reply_text("🔢 Введи число, например: 2000000")
        return SAVINGS
    context.user_data["savings"] = savings
    await update.message.reply_text("🏠 Сколько стоит квартира, которую хочешь купить (₽)?")
    return APARTMENT_COST


async def get_apartment_cost(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        cost = float(update.message.text.replace(",", ".").replace(" ", ""))
    except ValueError:
        await update.message.reply_text("🔢 Введи число, например: 8000000")
        return APARTMENT_COST

    context.user_data["apartment_cost"] = cost
    await update.message.reply_text("⏳ Считаю варианты...")

    scenario = calculate_scenario(
        context.user_data["age"],
        context.user_data["income"],
        context.user_data["savings"],
        cost
    )
    reply = format_scenario(context.user_data, scenario)
    await update.message.reply_text(reply, parse_mode="Markdown")
    await update.message.reply_text(
        "✨ Хочешь персональную историю о трёх судьбах? Жми /story\n"
        "🏠 Нужно найти реальное жильё? Жми /search\n"
        "🔄 Новый расчёт — /start"
    )
    return ConversationHandler.END


async def story_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Генерирует и отправляет историю жизни."""
    required = ["age", "income", "savings", "apartment_cost"]
    if not all(k in context.user_data for k in required):
        await update.message.reply_text("⚠️ Сначала пройди симуляцию — /start")
        return

    await update.message.reply_text("✍️ Размышляю... Это займёт ~20 секунд.")

    data = {k: context.user_data[k] for k in required}
    scenario = calculate_scenario(data["age"], data["income"], data["savBings"], data["apartment_cost"])
    story = generate_life_story(data, scenario)

    # Telegram ограничивает сообщения 4096 символами
    if len(story) > 4000:
        await update.message.reply_text(story[:4000])
        await update.message.reply_text(story[4000:8000])
    else:
        await update.message.reply_text(story)

    await update.message.reply_text(
        "📘 Вот такая судьба!\n"
        "/start — новые данные\n"
        "/search — найти жильё"
    )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("❌ Диалог прерван.\n/start — симуляция\n/search — поиск жилья")
    return ConversationHandler.END


# ==================== ПОИСК ЖИЛЬЯ ====================
def build_avito_url(city, category, rooms=None, price_min=None, price_max=None):
    """Формирует ссылку на Avito с фильтрами."""
    base = f"https://www.avito.ru/{city}/{category}"
    params = []
    if rooms:
        params.append(f"komnat={rooms}")
    if price_min:
        params.append(f"pmin={price_min}")
    if price_max:
        params.append(f"pmax={price_max}")
    return base + "?" + "&".join(params) if params else base


def build_cian_url(city, category, rooms=None, price_min=None,price_max=None):
    """Формирует ссылку на Циан с фильтрами."""
    city_map = {
        "moskva": "moskva",
        "spb": "sankt-peterburg",
        "ekaterinburg": "ekaterinburg",
        "novosibirsk": "novosibirsk",
        "kazan": "kazan",
        "nizhniy_novgorod": "nizhniy-novgorod"
    }
    cat_map = {
        "kvartiry/prodam": "flat/sale",
        "komnaty/prodam": "room/sale",
        "doma/prodam": "house/sale"
    }
    cian_city = city_map.get(city, city)
    cian_cat = cat_map.get(category, "flat/sale")
    base = f"https://{cian_city}.cian.ru/{cian_cat}/"
    params = []
    if rooms:
        params.append(f"room{rooms}=1")
    if price_min:
        params.append(f"minprice={price_min}")
    if price_max:
        params.append(f"maxprice={price_max}")
    return base + "?" + "&".join(params) if params else base


async def search_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "🏠 *Режим риэлтора*\n\n"
        "Подберу ссылки на Avito и Циан под ваш запрос.\n"
        "В каком городе ищем?\n"
        "Примеры: _moskva, spb, ekaterinburg, novosibirsk, kazan_",
        parse_mode="Markdown"
    )
    return CITY


async def get_city(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    trans = {
        "москва": "moskva",
        "санкт-петербург": "spb",
        "питер": "spb",
        "екатеринбург": "ekaterinburg",
        "новосибирск": "novosibirsk",
        "казань": "kazan",
        "нижний новгород": "nizhniy_novgorod"
    }
    city = update.message.text.strip().lower()
    context.user_data["s_city"] = trans.get(city, city)
    await update.message.reply_text(
        "Что ищем?\n"
        "1 — Квартиру\n"
        "2 — Комнату\n"
        "3 — Дом"
    )
    return CATEGORY


async def get_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    mapping = {
        "1": "kvartiry/prodam",
        "2": "komnaty/prodam",
        "3": "doma/prodam"
    }
    cat = mapping.get(update.message.text.strip())
    if not cat:
        await update.message.reply_text("Пожалуйста, введи 1, 2 или 3.")
        return CATEGORY
    context.user_data["s_cat"] = cat
    await update.message.reply_text("Сколько комнат? (1-5, или 0 — не важно)")
    return ROOMS


async def get_rooms(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    context.user_data["s_rooms"] = None if text == "0" else text
    await update.message.reply_text("Минимальная цена (₽)?\n0 — не важно")
    return PRICE_MIN


async def get_price_min(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        val = float(update.message.text.replace(",", ".").replace(" ", ""))
    except ValueError:
        await update.message.reply_text("Введи число (например, 3000000).")
        return PRICE_MIN
    context.user_data["s_pmin"] = int(val) if val > 0 else None
    await update.message.reply_text("Максимальная цена (₽)?\n0 — не важно")
    return PRICE_MAX


async def get_price_max(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        val = float(update.message.text.replace(",", ".").replace(" ", ""))
    except ValueError:
        await update.message.reply_text("Введи число.")
        return PRICE_MAX
    context.user_data["s_pmax"] = int(val) if val > 0 else None

    # Собираем ссылки
    city = context.user_data["s_city"]
    cat = context.user_data["s_cat"]
    rooms = context.user_data["s_rooms"]
    pmin = context.user_data["s_pmin"]
    pmax = context.user_data["s_pmax"]

    avito_url = build_avito_url(city, cat, rooms, pmin, pmax)
    cian_url = build_cian_url(city, cat, rooms, pmin, pmax)

    msg = (
        "🔍 *Готово! Вот ссылки на объявления:*\n\n"
        f"🏡 [Смотреть на Avito]({avito_url})\n"
        f"🏡 [Смотреть на Циан]({cian_url})\n\n"
        "Нажми на ссылку, чтобы открыть в браузере.\n"
        "—\n"
        "/search — новый поиск\n"
        "/start — симуляция жизни"
    )
    await update.message.reply_text(msg, parse_mode="Markdown", disable_web_page_preview=False)
    return ConversationHandler.END


# ==================== ЗАПУСК ====================
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # Симуляция
    sim_conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_age)],
            INCOME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_income)],
            SAVINGS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_savings)],
            APARTMENT_COST: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_apartment_cost)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    app.add_handler(sim_conv)
    app.add_handler(CommandHandler("story", story_command))

    # Поиск жилья
    search_conv = ConversationHandler(
        entry_points=[CommandHandler("search", search_start)],
        states={
            CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_city)],
            CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_category)],
            ROOMS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_rooms)],
            PRICE_MIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_price_min)],
            PRICE_MAX: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_price_max)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    app.add_handler(search_conv)

    logger.info("🚀 AI Life Simulator запущен!")
    print("✅ Бот работает. Нажми Ctrl+C для остановки.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()