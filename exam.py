import logging
import sqlite3
from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from keyboards import start_keyboards
from config import API_TOKEN

# Setup logging
logging.basicConfig(level=logging.INFO)

# Database utility function
def db_connection():
    return sqlite3.connect('todo_db.sqlite')

# Create database and table
def create_db():
    with db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_name TEXT,
            user_id INTEGER
        )''')
        conn.commit()

create_db()

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot=bot, storage=MemoryStorage())

class Register(StatesGroup):
    new_task_name = State()
    task_id = State()
    task_name = State()
    delete_id = State()

@dp.message_handler(commands="help")
async def help_command(message: types.Message):
    await message.answer("Assalomu aleykum, admin:\n@Saidbuk201")

@dp.message_handler(commands="start")
async def start_command(message: types.Message):
    await message.answer("Assalomu aleykum, MENU!", reply_markup=start_keyboards)

@dp.message_handler(lambda message: "Barchasini ko'rish 📋" in message.text)
async def view_tasks(message: types.Message):
    with db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE user_id = ?", (message.chat.id,))
        rows = cursor.fetchall()

    if not rows:
        await message.answer("Hali vazifalar yo'q")
    else:
        task_list = "\n".join([f"{row[0]}: {row[1]}" for row in rows])
        await message.answer("Sizning vazifalaringiz:\n" + task_list)

@dp.message_handler(lambda message: "Yangi qo'shish ➕" in message.text)
async def start_adding_task(message: types.Message):
    await message.answer("Vazifa nomini kiriting:")
    await Register.new_task_name.set()

@dp.message_handler(state=Register.new_task_name)
async def add_task(message: types.Message, state: FSMContext):
    new_task_name = message.text.strip()
    chat_id = message.chat.id

    if not new_task_name:
        await message.answer("Iltimos, vazifa nomini kiriting.")
        return

    with db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO tasks (task_name, user_id) VALUES (?, ?)", (new_task_name, chat_id))
        conn.commit()

    await message.answer("Vazifa qo'shildi!")
    await state.finish()

@dp.message_handler(lambda message: "O'zgartirish ✏️" in message.text)
async def editing_task(message: types.Message):
    await message.answer("O'zgartirish uchun ID ni kiriting:")
    await Register.task_id.set()

@dp.message_handler(state=Register.task_id)
async def get_task_id(message: types.Message, state: FSMContext):
    task_id = message.text.strip()
    await state.update_data(task_id=task_id)
    await message.answer("Yangi vazifa nomini kiriting:")
    await Register.task_name.set()

@dp.message_handler(state=Register.task_name)
async def update_task(message: types.Message, state: FSMContext):
    new_task_name = message.text.strip()
    data = await state.get_data()
    task_id = data.get('task_id')
    chat_id = message.chat.id

    with db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE tasks SET task_name = ? WHERE id = ? AND user_id = ?", (new_task_name, task_id, chat_id))
        if cursor.rowcount == 0:
            await message.answer("Vazifa topilmadi yoki sizga tegishli emas.")
        else:
            await message.answer("Vazifa o'zgartirildi!") 
        conn.commit()

    await state.finish()

@dp.message_handler(lambda message: "Hammasini O'chirish ❌" in message.text)
async def delete_all_tasks(message: types.Message):
    with db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tasks WHERE user_id = ?", (message.chat.id,))
        conn.commit()

    await message.answer("Barcha vazifalar o'chirildi!")

@dp.message_handler(lambda message: "O'chirish ❌" in message.text)
async def deleting_task(message: types.Message):
    await message.answer("O'chirish uchun ID ni kiriting:")
    await Register.delete_id.set() 

@dp.message_handler(state=Register.delete_id)
async def delete_task(message: types.Message, state: FSMContext):
    task_id = message.text.strip()
    chat_id = message.chat.id

    with db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tasks WHERE id = ? AND user_id = ?", (task_id, chat_id))
        if cursor.rowcount == 0:
            await message.answer("Vazifa topilmadi yoki sizga tegishli emas.")
        else:
            await message.answer("Vazifa o'chirildi!")
        conn.commit()

    await state.finish()

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
