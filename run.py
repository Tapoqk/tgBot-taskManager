import asyncio
import logging
from datetime import datetime
from database import cursor, connect, logged_in
from handlers import dp, bot


async def send_reminders():
    """Функция запускающая фоновую задачу для проверки и отправки напоминаний"""
    while True:
        now = datetime.now().strftime("%H:%M")

        cursor.execute("""
            SELECT user_id, todo 
            FROM reminders 
            WHERE reminder_time = ? AND reminded_once = 0
        """, (now,))

        for user_id_temp, todo_temp in cursor.fetchall():
            user_id_telegram = next((tg for tg, id_from_db in logged_in.items() if id_from_db == user_id_temp), None)

            if user_id_telegram:
                await bot.send_message(user_id_telegram, f"Время для: {todo_temp}!")
                cursor.execute("""
                    UPDATE reminders 
                    SET reminded_once = 1 
                    WHERE user_id = ? AND todo = ?
                """, (user_id_temp, todo_temp))
                connect.commit()

        await asyncio.sleep(60)

async def main():
    """Функция для запуска бота"""
    logging.basicConfig(level=logging.INFO)
    asyncio.create_task(send_reminders())
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())