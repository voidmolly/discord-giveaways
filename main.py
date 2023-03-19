import discord
from discord.ext import commands
import json
import random
import asyncio
import logging

# загружаем конфигурационный файл
with open('config.json') as f:
    config = json.load(f)

if bool(config['debug']):
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(module)s - %(levelname)s - %(funcName)s: %(lineno)d - %(message)s",
        datefmt='%H:%M:%S',
    )
    logging.info("Debug mode is ON")
else:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s: %(message)s",
        datefmt='%H:%M:%S',
    )
    logging.basicConfig(level=logging.INFO)

intents = discord.Intents.all()

# создаем экземпляр клиента discord и задаем префикс
bot = commands.Bot(command_prefix=config['prefix'], intents=intents)


@bot.event
async def on_ready():
    logging.info(f'Бот {bot.user} запущен и успешно подключен к Discord')


# функция, которая будет вызываться, когда сообщение будет отправлено в канал
@bot.event
async def on_message(message):
    # проверяем, что сообщение не от бота
    if message.author.bot:
        return

    # проверяем, что сообщение было отправлено в нужный канал
    if message.channel.id != config['channel_id']:
        return

    logging.debug("Зарегестрировано новое сообщение от админа в канале для розыгрышей")

    # отправляем сообщение в личные сообщения автору сообщения
    author = message.author
    await author.send('Сколько реакций нужно для розыгрыша?')

    # функция, которая будет вызываться, когда пользователь ответит на сообщение в личных сообщениях
    def check(m):
        return m.author == author and isinstance(m.channel, discord.DMChannel)

    # ждем ответа пользователя
    try:
        reaction_count_message = await bot.wait_for('message', check=check, timeout=60.0)
    except asyncio.TimeoutError:
        await author.send('Время ответа истекло. Розыгрыш удален.')
        logging.info("Время ответа истекло. Розыгрыш удален.")
        await message.delete()
        return

    # преобразуем ответ пользователя в число
    try:
        reaction_count = int(reaction_count_message.content)
    except ValueError:
        await author.send('Неверный формат ответа. Розыгрыш удален.')
        await message.delete('Неверный формат ответа. Розыгрыш удален.')
        logging.info()
        logging.debug(reaction_count_message.content)
        return

    logging.info(f"Розыгрыш завершится, когда наберется {reaction_count} участников")

    # добавляем реакцию на сообщение
    await message.add_reaction('🎉')

    # функция, которая будет вызываться, когда реакция будет добавлена к сообщению
    async def on_reaction_add(reaction, user):
        # проверяем, что реакция добавлена к нужному сообщению
        if reaction.message.id != message.id:
            return

        logging.debug(f"Добавлена реакция: {reaction.emoji}")

        if reaction.emoji == '❌':
            # получаем объект нужной реакции
            target_reaction = None
            for r in reaction.message.reactions:
                if str(r.emoji) == '🎉':
                    target_reaction = r
                    break
            if target_reaction is not None:
                # получаем список пользователей, которые оставили нужную реакцию
                users = []
                async for user in target_reaction.users():
                    if not user.bot and user != author:
                        users.append(user)
                # выбираем случайного пользователя из списка пользователей
                winner = random.choice(users)
                # отправляем сообщение в канал с упоминанием победителя
                await reaction.message.reply(f'Победитель: {winner.mention}')
            else:
                await reaction.message.reply('Не найдено реакции на 🎉')
            # удаляем обработчик реакций
            bot.remove_listener(on_reaction_add)
            logging.info("Розыгрыш завершен досрочно")

        # проверяем, что количество реакций достаточно для розыгрыша
        elif reaction.count >= reaction_count and reaction.emoji == '🎉':
            # получаем список пользователей, которые оставили реакцию
            users = []
            async for user in reaction.users():
                if not user.bot:
                    users.append(user)
            # выбираем случайного пользователя из списка пользователей
            winner = random.choice(users)
            # отправляем сообщение в канал с упоминанием победителя
            await reaction.message.reply(f'Победитель: {winner.mention}')
            # удаляем обработчик реакций
            bot.remove_listener(on_reaction_add)
            logging.info("Розыгрыш завершен")


    # добавляем обработчик реакций
    listener = bot.add_listener(on_reaction_add)


# запускаем бота
bot.run(config['token'])
