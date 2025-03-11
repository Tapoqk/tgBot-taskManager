import asyncio
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram import Dispatcher, Bot
import re
import sqlite3
from database import cursor, connect, logged_in, is_logged_in
from snake import Game
from env import TOKEN

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(Command('help'))
async def help_command(message: Message):
    """Функция, которая создаёт клавиатуру для выбора категории помощи"""
    kb = InlineKeyboardBuilder()

    categories = [
        ("Авторизация", "help_auth"),
        ("Задачи", "help_todo"),
        ("Напоминания", "help_reminders"),
        ("Таймеры", "help_timers"),
        ("Змейка", "help_snake")
    ]

    for help_type, help_data in categories:
        kb.button(text=help_type, callback_data=help_data)

    kb.adjust(2, repeat=True)

    await message.answer(
        "Главное меню\nВыберите категорию:",
        reply_markup=kb.as_markup()
    )


@dp.callback_query(lambda c: c.data.startswith("help_"))
async def process_help_menu(callback: CallbackQuery):
    """Функция, которая используется, чтобы показать информацию о выбранной категории"""

    help_texts = {
        "help_auth": (
            "Авторизация:\n"
            "/register [логин] [пароль] - Регистрация\n"
            "/login [логин] [пароль] - Вход в систему\n"
            "/logout - Выход из аккаунта"
        ),
        "help_todo": (
            "Управление задачами:\n"
            "/add [задача] - Добавить задачу\n"
            "/delete [задача] - Удалить задачу\n"
            "/list - Список всех задач"
        ),
        "help_reminders": (
            "Напоминания:\n"
            "/set [HH:MM] - Установить напоминание"
        ),
        "help_timers": (
            "Таймеры:\n"
            "/timer - Запустить таймер"
        ),
        "help_snake": (
            "Змейка:\n"
            "/snake - Запустить змейку"
        )
    }

    await callback.message.edit_text(help_texts[callback.data])
    await callback.answer()


@dp.message(Command('register'))
async def register(message: Message):
    """Функция для регистрации нового пользователя"""
    separate = message.text.split(maxsplit=2)
    if len(separate) < 3:
        await message.answer('Формат: /register [логин] [пароль]')
        return

    try:
        cursor.execute(
            "INSERT INTO users (login, password) VALUES (?, ?)",
            (separate[1], separate[2])
        )
        connect.commit()
        await message.answer('Регистрация успешна!')
    except sqlite3.IntegrityError:
        await message.answer("Логин занят!")


@dp.message(Command('login'))
async def login(message: Message):
    """Функция для авторизации пользователя"""
    separate = message.text.split(maxsplit=2)
    if len(separate) < 3:
        await message.answer('Формат: /login [логин] [пароль]')
        return

    cursor.execute("SELECT user_id FROM users WHERE login = ? AND password = ?",
                  (separate[1], separate[2]))

    user = cursor.fetchone()
    if user:
        logged_in[message.from_user.id] = user[0]
        cursor.execute("INSERT OR REPLACE INTO sessions VALUES (?, ?)",
                      (message.from_user.id, user[0]))
        connect.commit()
        await message.answer(f"Добро пожаловать, {separate[1]}!")
    else:
        await message.answer("Ошибка авторизации!")

@dp.message(Command('logout'))
async def logout(message: Message):
    """Функция для завершения сессии пользователя"""
    if is_logged_in(message.from_user.id):
        del logged_in[message.from_user.id]
        cursor.execute("DELETE FROM sessions WHERE user_id_telegram = ?",
                      (message.from_user.id,))
        connect.commit()
        await message.answer("Вы вышли из системы!")
    else:
        await message.answer("Вы не авторизованы!")

@dp.message(Command('add'))
async def add_todo(message: Message):
    """Функция для добавления новой задачи"""
    if not is_logged_in(message.from_user.id):
        await message.answer('Требуется авторизация!')
        return

    habit = message.text[len('/add '):].strip()
    if not habit:
        await message.answer('Формат: /add [задача]')
        return

    cursor.execute("INSERT INTO todos (user_id, todo) VALUES (?, ?)",
                  (logged_in[message.from_user.id], habit))
    connect.commit()
    await message.answer(f"Задача добавлена: {habit}")

@dp.message(Command('delete'))
async def delete_todo(message: Message):
    """Функция для удаления задачи из списка"""
    if not is_logged_in(message.from_user.id):
        await message.answer('Требуется авторизация!')
        return

    todo = message.text[len('/delete '):].strip()
    if not todo:
        await message.answer('Формат: /delete [задача]')
        return

    cursor.execute("DELETE FROM todos WHERE user_id = ? AND todo = ?",
                  (logged_in[message.from_user.id], todo))
    connect.commit()
    await message.answer(f"Задача удалена: {todo}")

@dp.message(Command('list'))
async def list_todo(message: Message):
    """Функция для отображения списка всех задач"""
    if not is_logged_in(message.from_user.id):
        await message.answer('Требуется авторизация!')
        return

    cursor.execute("SELECT todo FROM todos WHERE user_id = ?",
                  (logged_in[message.from_user.id],))
    todos = [td[0] for td in cursor.fetchall()]
    text = "Список ваших задач:\n" + "\n".join(todos) if todos else "Задачи ещё не добавлены!"
    await message.answer(text)

@dp.message(Command('set'))
async def set_reminder(message: Message):
    """Функция для установления напоминания"""
    if not is_logged_in(message.from_user.id):
        await message.answer('Требуется авторизация!')
        return

    match = re.search(r"(\d{2}:\d{2})", message.text)
    if not match:
        await message.answer("Формат: /set [HH:MM]")
        return

    cursor.execute("SELECT todo FROM todos WHERE user_id = ?",
                   (logged_in[message.from_user.id],))
    todos = [td[0] for td in cursor.fetchall()]

    if not todos:
        await message.answer("Сначала добавьте задачи!")
        return

    kb = InlineKeyboardBuilder()
    for todo in todos:
        kb.button(text=todo, callback_data=f"remind|{match.group(1)}|{todo}")
    kb.adjust(4)

    await message.answer(
        "Выберите задачу для напоминания:",
        reply_markup=kb.as_markup()
    )

@dp.callback_query(lambda c: c.data.startswith("remind"))
async def process_reminder(callback: CallbackQuery):
    """Функция для сохранения напоминаний в базу данных"""
    empty, time, todo = callback.data.split("|")
    cursor.execute("""
        INSERT OR REPLACE INTO reminders 
        (user_id, reminder_time, todo) 
        VALUES (?, ?, ?)
    """, (logged_in[callback.from_user.id], time, todo))
    connect.commit()
    await callback.message.delete()
    await callback.message.answer(f"Напоминание для '{todo}' установлено на {time}")

@dp.message(Command('timer'))
async def set_timer(message: Message):
    """Функция для отображения меню выбора длительности таймера"""
    if not is_logged_in(message.from_user.id):
        await message.answer('Требуется авторизация!')
        return

    kb = InlineKeyboardBuilder()
    durations = [1, 2, 3, 5, 10, 15, 30, 60]

    for minutes in durations:
        kb.button(text=f"{minutes} минут", callback_data=f"timer_duration|{minutes}")
    kb.adjust(4, repeat=True)

    await message.answer(
        "Выберите длительность таймера:",
        reply_markup=kb.as_markup()
    )

@dp.callback_query(lambda c: c.data.startswith("timer_duration"))
async def start_timer_handler(callback: CallbackQuery):
    """Функция запускает таймер с выбранной длительностью"""
    empty, minutes = callback.data.split("|")

    await callback.message.delete()
    await start_timer_logic(
        user_id=callback.from_user.id,
        minutes=int(minutes)
    )

async def start_timer_logic(user_id: int, minutes: int):
    """Функция запускает и отслеживает таймер"""
    start_message = f"Таймер на {minutes} минут запущен!"
    await bot.send_message(user_id, start_message)

    await asyncio.sleep(minutes * 60)

    end_message = f"Таймер на {minutes} минут завершен!"
    await bot.send_message(user_id, end_message)

active_games = {}

@dp.message(Command('snake'))
async def start_snake_game(message: Message):
    """Функция для запуска змейки"""
    if not is_logged_in(message.from_user.id):
        await message.answer('Требуется авторизация!')
        return

    game = Game()
    active_games[message.from_user.id] = game

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬆️", callback_data="up")],
        [InlineKeyboardButton(text="⬅️", callback_data="left"),
         InlineKeyboardButton(text="⬇️", callback_data="down"),
         InlineKeyboardButton(text="➡️", callback_data="right")]
    ])

    await message.answer(
        f"Игра Змейка!\n{game.get_field()}\nСчёт: {game.score}",
        reply_markup=kb
    )

@dp.callback_query(lambda c: c.data in ["up", "down", "left", "right"])
async def handle_snake_controls(callback: CallbackQuery):
    """Функция для обработки нажатий клавиатуры"""
    user_id = callback.from_user.id
    game = active_games.get(user_id)
    if not game:
        await callback.answer("Игра не запущена. Введите /snake, чтобы начать.")
        return

    direction_map = {
        "up": (0, -1),
        "down": (0, 1),
        "left": (-1, 0),
        "right": (1, 0)
    }
    game.snake.change_direction(direction_map[callback.data])

    game.update()

    if game.game_over:
        await callback.message.edit_text(f"Игра окончена! Ваш счёт: {game.score}")
        del active_games[user_id]
    else:
        await callback.message.edit_text(
            f"Игра Змейка!\n{game.get_field()}\nСчёт: {game.score}",
            reply_markup=callback.message.reply_markup
        )
    await callback.answer()