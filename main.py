import os
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Ініціалізація бота
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# 📊 Дані
stats = defaultdict(lambda: {"work": 0, "away": 0})
away_time = None
work_start_time = None
last_date = None

# 🎛 Кнопки
def get_main_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("🟢 На робочому місці", callback_data="back_to_work"),
        InlineKeyboardButton("🔴 Пішов", callback_data="left_work")
    )
    return keyboard

# ▶️ /start
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    global work_start_time, last_date
    now = datetime.datetime.now()
    today = now.date()

    if last_date != today:
        last_date = today
    if work_start_time is None:
        work_start_time = now

    await message.answer("Обери статус:", reply_markup=get_main_keyboard())

# 🔴 Пішов
@dp.callback_query_handler(Text(equals="left_work"))
async def handle_left(callback: types.CallbackQuery):
    global away_time, work_start_time, stats

    now = datetime.datetime.now()
    today = now.date()
    work_text = "❓ Робочий час не визначено"

    if work_start_time:
        session = (now - work_start_time).total_seconds()
        stats[today]["work"] += session

        minutes = int(session // 60)
        hours = minutes // 60
        mins = minutes % 60

        work_text = f"✅ Робота перед цим: {hours} год {mins} хв"

    away_time = now
    work_start_time = None

    await callback.message.answer(
        f"🔴 Хтось вийшов з робочого місця.\n{work_text}",
        reply_markup=get_main_keyboard()
    )
    await callback.answer()

# 🟢 Повернувся
@dp.callback_query_handler(Text(equals="back_to_work"))
async def handle_back(callback: types.CallbackQuery):
    global away_time, work_start_time, stats, last_date

    now = datetime.datetime.now()
    today = now.date()

    if last_date != today:
        last_date = today

    if away_time:
        session = (now - away_time).total_seconds()
        stats[today]["away"] += session
        away_time = None

    work_start_time = now

    away_sec = stats[today]["away"]
    work_sec = stats[today]["work"]
    if work_start_time:
        work_sec += (now - work_start_time).total_seconds()

    text = (
        f"🟢 Хтось повернувся на робоче місце.\n"
        f"⏱ Відсутність за день: {int(away_sec // 3600)} год {int(away_sec % 3600 // 60)} хв\n"
        f"✅ Робота за день: {int(work_sec // 3600)} год {int(work_sec % 3600 // 60)} хв"
    )

    await callback.message.answer(text, reply_markup=get_main_keyboard())
    await callback.answer()

# 📊 /stats — статистика за тиждень
@dp.message_handler(commands=['stats'])
async def handle_stats(message: types.Message):
    now = datetime.datetime.now()
    today = now.date()
    week_dates = [(today - datetime.timedelta(days=i)) for i in range(6, -1, -1)]

    text = "📊 Статистика за останні 7 днів:\n\n"
    total_work = 0
    total_away = 0

    for day in week_dates:
        work = stats[day]["work"]
        away = stats[day]["away"]
        total_work += work
        total_away += away
        text += f"📅 {day.strftime('%a %d.%m')} — 🟢 {int(work // 3600)}г {int(work % 3600 // 60)}х, 🔴 {int(away // 3600)}г {int(away % 3600 // 60)}х\n"

    text += (
        f"\n🟢 Загалом працювали: {int(total_work // 3600)} год {int(total_work % 3600 // 60)} хв\n"
        f"🔴 Загалом були відсутні: {int(total_away // 3600)} год {int(total_away % 3600 // 60)} хв"
    )

    await message.answer(text)

# 🟢 Старт / стоп
async def on_startup(dp):
    print("✅ Бот запущено")

async def on_shutdown(dp):
    print("🛑 Бот зупинено")

if __name__ == '__main__':
    print("🟡 main.py запущено")
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup, on_shutdown=on_shutdown)
