# main.py
import asyncio
import os
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message
from openai import OpenAI
from aiohttp import web
from database import init_db, register_or_update_user, get_user_by_identifier, modify_tokens, modify_status

# Вставьте ваши данные прямо сюда, чтобы обойти проблему с переменными в Render
TOKEN = "8039854075:AAEgAoo2SCDUiBwz9hzbJ0MNCinj1-56x10"
GROQ_API_KEY = "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"
ADMIN_ID = 8431713859

PORT = int(os.getenv("PORT", 8080))
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")

bot = Bot(token=TOKEN)
dp = Dispatcher()

client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1"
)

def is_user_admin(user_id: int) -> bool:
    if user_id == ADMIN_ID:
        return True
    user = get_user_by_identifier(user_id)
    return user and user['is_admin'] == 1

@dp.message(Command("start"))
async def cmd_start(message: Message):
    init_db()
    if not message.from_user:
        return
        
    user_id = message.from_user.id
    username = message.from_user.username
    
    register_or_update_user(user_id, username)
    user = get_user_by_identifier(user_id)
    
    if user['is_blocked']:
        await message.answer("⛔ **Доступ ограничен**\n\nВаш аккаунт был заблокирован в системе безопасности администратором. Обратитесь в службу поддержки для уточнения деталей.")
        return

    uname_display = f"@{user['username']}" if user['username'] else "Не указан"
    
    await message.answer(
        f"✨ **Добро пожаловать в элитный ИИ-ассистент нового поколения!** 💎\n\n"
        f"🔮 Я универсальный искусственный интеллект (на базе Groq Llama 3.1), интегрированный для работы в любых личных чатах, группах и каналах.\n\n"
        f"📊 **Ваш персональный профиль:**\n"
        f"┣ 🆔 Telegram ID: `{user['user_id']}`\n"
        f"┣ 👤 Username: `{uname_display}`\n"
        f"┗ ⚡ Доступные токены: **{user['tokens']}** (1 запрос = 1 токен)\n\n"
        f"🚀 *Просто отправьте мне текстовый запрос или добавьте меня в ваш рабочий чат с правами администратора, чтобы начать плодотворное взаимодействие.*",
        parse_mode="Markdown"
    )

@dp.message(Command("admin"))
async def cmd_admin(message: Message):
    if not is_user_admin(message.from_user.id):
        await message.answer("🛡️ **Ошибка доступа**\n\nУ вас отсутствуют необходимые привилегии для вызова панели управления системой.")
        return
        
    await message.answer(
        "👑 **Центр управления системой (Admin Panel)** 🌟\n\n"
        "Интерфейс высшего уровня для контроля пользователей, распределения токенов и управления правами доступа.\n"
        "💡 *Для выполнения команд вы можете использовать как числовой `ID`, так и `@username`.*\n\n"
        "⚡ **Доступные протоколы команд:**\n"
        "• `/add_tokens <ID или @username> <кол-во>` — зачисление токенов 💎\n"
        "• `/remove_tokens <ID или @username> <кол-во>` — списание токенов 📉\n"
        "• `/block <ID или @username>` — заморозка аккаунта пользователя ⛔\n"
        "• `/unblock <ID или @username>` — разморозка аккаунта пользователя ✅\n"
        "• `/make_admin <ID или @username>` — назначение администратором 👑\n"
        "• `/remove_admin <ID или @username>` — отзыв административных прав 🛡️",
        parse_mode="Markdown"
    )

@dp.message(Command("add_tokens"))
async def cmd_add_tokens(message: Message):
    if not is_user_admin(message.from_user.id):
        return
    parts = message.text.split()
    if len(parts) != 3:
        await message.answer("⚠️ **Неверный синтаксис команды**\n\nИспользуйте правильный формат:\n`/add_tokens <ID или @username> <количество>`", parse_mode="Markdown")
        return
    try:
        target = parts[1]
        amount = int(parts[2])
        new_total, real_id = modify_tokens(target, amount)
        if new_total is None:
            await message.answer("❌ **Пользователь не найден**\n\nУбедитесь, что указанный ID или @username корректен и пользователь хотя бы раз запускал бота.", parse_mode="Markdown")
            return
        await message.answer(f"💎 **Операция выполнена успешно**\n\nПользователю (`{target} | ID: {real_id}`) начислено токенов. Актуальный баланс: **{new_total} ⚡**", parse_mode="Markdown")
    except ValueError:
        await message.answer("⚠️ **Ошибка валидации данных**\n\nКоличество токенов должно строго являться целым числом.")

@dp.message(Command("remove_tokens"))
async def cmd_remove_tokens(message: Message):
    if not is_user_admin(message.from_user.id):
        return
    parts = message.text.split()
    if len(parts) != 3:
        await message.answer("⚠️ **Неверный синтаксис команды**\n\nИспользуйте правильный формат:\n`/remove_tokens <ID или @username> <количество>`", parse_mode="Markdown")
        return
    try:
        target = parts[1]
        amount = int(parts[2])
        new_total, real_id = modify_tokens(target, -amount)
        if new_total is None:
            await message.answer("❌ **Пользователь не найден**\n\nУбедитесь, что указанный ID или @username корректен.", parse_mode="Markdown")
            return
        await message.answer(f"📉 **Операция выполнена успешно**\n\nУ пользователя (`{target} | ID: {real_id}`) списано токенов. Остаток на балансе: **{new_total} ⚡**", parse_mode="Markdown")
    except ValueError:
        await message.answer("⚠️ **Ошибка валидации данных**\n\nКоличество токенов должно строго являться целым числом.")

@dp.message(Command("block"))
async def cmd_block(message: Message):
    if not is_user_admin(message.from_user.id):
        return
    parts = message.text.split()
    if len(parts) != 2:
        await message.answer("⚠️ **Неверный синтаксис команды**\n\nИспользуйте правильный формат:\n`/block <ID или @username>`", parse_mode="Markdown")
        return
    target = parts[1]
    real_id = modify_status(target, 'is_blocked', 1)
    if not real_id:
        await message.answer("❌ **Пользователь не найден** в базе данных системы.", parse_mode="Markdown")
        return
    await message.answer(f"⛔ **Безопасность активирована**\n\nПользователь (`{target} | ID: {real_id}`) успешно заблокирован.", parse_mode="Markdown")

@dp.message(Command("unblock"))
async def cmd_unblock(message: Message):
    if not is_user_admin(message.from_user.id):
        return
    parts = message.text.split()
    if len(parts) != 2:
        await message.answer("⚠️ **Неверный синтаксис команды**\n\nИспользуйте правильный формат:\n`/unblock <ID или @username>`", parse_mode="Markdown")
        return
    target = parts[1]
    real_id = modify_status(target, 'is_blocked', 0)
    if not real_id:
        await message.answer("❌ **Пользователь не найден** в базе данных системы.", parse_mode="Markdown")
        return
    await message.answer(f"🟢 **Доступ восстановлен**\n\nПользователь (`{target} | ID: {real_id}`) успешно разблокирован.", parse_mode="Markdown")

@dp.message(Command("make_admin"))
async def cmd_make_admin(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ **Привилегии владельца**\n\nНазначать новых администраторов имеет право исключительно Главный владелец бота.", parse_mode="Markdown")
        return
    parts = message.text.split()
    if len(parts) != 2:
        await message.answer("⚠️ **Неверный синтаксис команды**\n\nИспользуйте правильный формат:\n`/make_admin <ID или @username>`", parse_mode="Markdown")
        return
    target = parts[1]
    real_id = modify_status(target, 'is_admin', 1)
    if not real_id:
        await message.answer("❌ **Пользователь не найден** в базе данных.", parse_mode="Markdown")
        return
    await message.answer(f"👑 **Повышение прав**\n\nПользователь (`{target} | ID: {real_id}`) официально наделен статусом администратора системы.", parse_mode="Markdown")

@dp.message(Command("remove_admin"))
async def cmd_remove_admin(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ **Привилегии владельца**\n\nЗабирать административные права может только Главный владелец бота.", parse_mode="Markdown")
        return
    parts = message.text.split()
    if len(parts) != 2:
        await message.answer("⚠️ **Неверный синтаксис команды**\n\nИспользуйте правильный формат:\n`/remove_admin <ID или @username>`", parse_mode="Markdown")
        return
    target = parts[1]
    real_id = modify_status(target, 'is_admin', 0)
    if not real_id:
        await message.answer("❌ **Пользователь не найден** в базе данных.", parse_mode="Markdown")
        return
    await message.answer(f"🛡️ **Понижение прав**\n\nС пользователя (`{target} | ID: {real_id}`) успешно сняты административные полномочия.", parse_mode="Markdown")

@dp.message(F.text)
async def handle_ai_query(message: Message):
    if message.text.startswith("/"):
        return
    
    if not message.from_user:
        return
        
    user_id = message.from_user.id
    username = message.from_user.username

    register_or_update_user(user_id, username)
    user = get_user_by_identifier(user_id)
    
    if user['is_blocked']:
        return

    if user['tokens'] <= 0:
        if message.chat.type == "private":
            await message.answer("⚠️ **Лимит исчерпан**\n\nК сожалению, у вас закончились доступные токены. Обратитесь к администратору для пополнения баланса.", parse_mode="Markdown")
        return

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": message.text}]
        )
        answer = response.choices[0].message.content
        
        new_tokens, _ = modify_tokens(user_id, -1)
        
        await message.answer(f"{answer}\n\n*(✨ Списан 1 токен. Остаток на балансе: **{new_tokens} ⚡**)*", parse_mode="Markdown")
    except Exception as e:
        if message.chat.type == "private":
            await message.answer(f"⚠️ **Ошибка ИИ-сервиса**\n\nПроизошла непредвиденная ошибка при обработке запроса: `{e}`", parse_mode="Markdown")

async def handle_ping(request):
    return web.Response(text="Bot is alive and working!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    print(f"Веб-сервер запущен на порту {PORT}")

async def self_ping_task():
    await asyncio.sleep(15)
    import aiohttp
    while True:
        try:
            if RENDER_EXTERNAL_URL:
                async with aiohttp.ClientSession() as session:
                    async with session.get(RENDER_EXTERNAL_URL) as resp:
                        print(f"🔄 Авто-пинг выполнен успешно: статус {resp.status}")
            else:
                print("⚠️ RENDER_EXTERNAL_URL не задана, авто-пинг пропущен.")
        except Exception as e:
            print(f"⚠️ Ошибка авто-пинга: {e}")
        
        await asyncio.sleep(480)

async def main():
    init_db()
    await asyncio.gather(
        start_web_server(),
        self_ping_task(),
        dp.start_polling(bot)
    )

if __name__ == "__main__":
    asyncio.run(main())
