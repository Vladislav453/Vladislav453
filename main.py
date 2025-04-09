import sys
import logging
import asyncio
from os import getenv
import datetime
import requests
import math

from aiogram.types import Message
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from my_token import BOT_TOKEN, WETHER_TOKEN

# Инициализация бота и диспетчера
TOKEN = getenv(BOT_TOKEN)

dp = Dispatcher()


@dp.message(CommandStart())
async def start(msg: Message):
    await msg.reply("Привет! Напиши мне название города, и я пришлю сводку погоды. \n"
                    "Чтобы получить прогноз на несколько дней, напиши 'город через N дней', "
                    "где N — количество дней (максимум 5).")


@dp.message()
async def get_weather(msg: Message):
    text = msg.text.strip()
    parts = text.split(' через ')

    city_name = parts[0]  # Название города
    days_ahead = 0  # Количество дней для прогноза

    if len(parts) > 1:
        try:
            days_ahead = int(parts[1].split()[0])  # Извлекаем количество дней
        except ValueError:
            await msg.reply("Пожалуйста, укажите корректное число дней.")
            return

    if not city_name:
        await msg.reply("Пожалуйста, укажите название города.")
        return

    try:
        if days_ahead > 0:
            response = requests.get(
                f"http://api.openweathermap.org/data/2.5/forecast?q={city_name}&lang=ru&units=metric&appid={WETHER_TOKEN}")

            if response.status_code != 200:
                await msg.reply("Не удалось получить данные о погоде. Проверьте название города.")
                return

            data = response.json()
            forecast_list = data['list']
            daily_forecast = {}

            for forecast in forecast_list:
                # Извлекаем дату из временной метки
                forecast_date = datetime.datetime.fromtimestamp(forecast['dt']).date()
                if forecast_date not in daily_forecast:
                    daily_forecast[forecast_date] = []

                temp = forecast['main']['temp']
                weather_description = forecast['weather'][0]['description']
                daily_forecast[forecast_date].append(f"{forecast['dt_txt']}: {temp}°C, {weather_description}")

            forecast_message = f"Прогноз погоды в городе {city_name} на следующий(ие) {days_ahead} дня(ей):\n"
            n = 0

            for day, forecasts in sorted(daily_forecast.items()):
                if (day - datetime.date.today()).days > days_ahead:
                    continue  # Прекращаем, если прошли нужное количество дней

                for forecast in forecasts:
                    if n == 12 or n == 4 or n == 0 or n == 20 or n == 28 or n == 36:
                        forecast_message += f"\n<b>{day}</b>:\n"
                        print(n)

                    n += 1
                    forecast_message += f"{forecast}\n"

            await msg.reply(forecast_message)

        else:
            # Запрос текущей погоды
            response = requests.get(
                f"http://api.openweathermap.org/data/2.5/weather?q={city_name}&lang=ru&units=metric&appid={WETHER_TOKEN}")

            if response.status_code != 200:
                await msg.reply("Не удалось получить данные о погоде. Проверьте название города.")
                return

            data = response.json()
            city = data["name"]
            cur_temp = data["main"]["temp"]
            humidity = data["main"]["humidity"]
            pressure = data["main"]["pressure"]
            wind = data["wind"]["speed"]

            sunrise_timestamp = datetime.datetime.fromtimestamp(data["sys"]["sunrise"])
            sunset_timestamp = datetime.datetime.fromtimestamp(data["sys"]["sunset"])

            length_of_the_day = sunset_timestamp - sunrise_timestamp

            code_to_smile = {
                "Clear": "Ясно \U00002600",
                "Clouds": "Облачно \U00002601",
                "Rain": "Дождь \U00002614",
                "Drizzle": "Дождь \U00002614",
                "Thunderstorm": "Гроза \U000026A1",
                "Snow": "Снег \U0001F328",
                "Mist": "Туман \U0001F32B"
            }
            weather_description = data["weather"][0]["main"]
            wd = code_to_smile.get(weather_description, "Посмотри в окно, я не понимаю, что там за погода...")

            await msg.reply(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
                            f"Погода в городе: {city}\n<b>Температура: {cur_temp}°C {wd}</b>\n"
                            f"Влажность: {humidity}%\nДавление: {math.ceil(pressure / 1.333)} мм.рт.ст\nВетер: {wind} м/с \n"
                            f"Восход солнца: {sunrise_timestamp}\nЗакат солнца: {sunset_timestamp}\nПродолжительность дня: {length_of_the_day}\n"
                            f"Хорошего дня!")

    except Exception as e:
        await msg.reply("Произошла ошибка при получении данных о погоде. Проверьте название города!")


async def main() -> None:
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
