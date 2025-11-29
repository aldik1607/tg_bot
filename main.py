import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import Message
from dotenv import load_dotenv
from settings import API_URL
import requests
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from bot_states import RegisterStates, LoginStates
from settings import API_URL

LOGIN_URL = f"{API_URL}/auth/login"

REGISTER_URL = f"{API_URL}/auth/register"

storage = MemoryStorage()
dp = Dispatcher(storage=storage)

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is not set")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("Файл main.py запущен")

STARTUPS_URL = f"{API_URL}/startups"

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()


@dp.message(F.text == "/startups")
async def get_startups(message: Message):
    try:
        response = requests.get(STARTUPS_URL, timeout=10)
        response.raise_for_status()
        startups = response.json()

        if not startups:
            await message.answer("Стартапов пока нет.")
            return

        lines = []
        for s in startups:
            name = s.get("title", "Без названия")
            desc = s.get("description", "")
            lines.append(f"• {name} — {desc}")

        text = "\n".join(lines)

        await send_long_text(message, text)  
    except Exception as e:
        await message.answer(f"Ошибка при запросе стартапов: {e}")


async def send_long_text(message: Message, text: str, max_length: int = 4096):
    """Send long text by splitting it into multiple messages if needed."""
    for i in range(0, len(text), max_length):
        await message.answer(text[i:i + max_length])


@dp.message(F.text == "/start")
async def cmd_start(message: Message):
    await message.answer("Привет")

@dp.message(F.text == "/register")
async def register_start(message: Message, state: FSMContext):
    await message.answer("Введите ваше имя:")
    await state.set_state(RegisterStates.waiting_for_name)


@dp.message(RegisterStates.waiting_for_name)
async def register_get_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Введите ваш email:")
    await state.set_state(RegisterStates.waiting_for_email)


@dp.message(RegisterStates.waiting_for_email)
async def register_get_email(message: Message, state: FSMContext):
    await state.update_data(email=message.text)
    await message.answer("Придумайте пароль:")
    await state.set_state(RegisterStates.waiting_for_password)


@dp.message(RegisterStates.waiting_for_password)
async def register_get_password(message: Message, state: FSMContext):
    data = await state.get_data()
    name = data["name"]
    email = data["email"]
    password = message.text

    try:
        resp = requests.post(
            REGISTER_URL,
            json={"name": name, "email": email, "password": password},
            timeout=10,
        )
        if resp.status_code in (200, 201):
            await message.answer("Регистрация прошла успешно!")
        else:
            await message.answer(f"Регистрация не удалась: {resp.status_code} {resp.text}")
    except Exception as e:
        await message.answer(f"Ошибка при запросе регистрации: {e}")

    await state.clear()

async def main():
    logger.info("Бот запускается...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

@dp.message(F.text == "/login")
async def login_start(message: Message, state: FSMContext):
    await message.answer("Введите ваш email:")
    await state.set_state(LoginStates.waiting_for_email)


@dp.message(LoginStates.waiting_for_email)
async def login_get_email(message: Message, state: FSMContext):
    await state.update_data(email=message.text)
    await message.answer("Введите пароль:")
    await state.set_state(LoginStates.waiting_for_password)


@dp.message(LoginStates.waiting_for_password)
async def login_get_password(message: Message, state: FSMContext):
    data = await state.get_data()
    email = data["email"]
    password = message.text

    try:
        resp = requests.post(
            LOGIN_URL,
            json={"email": email, "password": password},
            timeout=10,
        )
        if resp.status_code == 200:
            body = resp.json()
            token = body.get("token")
            await message.answer("Вы успешно вошли!")
        else:
            await message.answer(f"Логин не удался: {resp.status_code} {resp.text}")
    except Exception as e:
        await message.answer(f"Ошибка при запросе логина: {e}")

    await state.clear()