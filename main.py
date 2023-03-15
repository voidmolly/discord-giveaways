import discord
from discord.ext import commands
import json
import random
import asyncio

# загружаем конфигурационный файл
with open('config.json') as f:
    config = json.load(f)

intents = discord.Intents.all()

# создаем экземпляр клиента discord и задаем префикс
bot = commands.Bot(command_prefix=config['prefix'], intents=intents)


@bot.event
async def on_ready():
    print(f'{bot.user} connected to Discord!')


# функция, которая будет вызываться, когда сообщение будет отправлено в канал
@bot.event
async def on_message(message):
    # проверяем, что сообщение не от бота
    if message.author.bot:
        return

    # проверяем, что сообщение было отправлено в нужный канал
    if message.channel.id != config['channel_id']:
        return

    # добавляем реакцию на сообщение
    await message.add_reaction('🎉')

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
        await author.send('Время ответа истекло')
        return

    # преобразуем ответ пользователя в число
    try:
        reaction_count = int(reaction_count_message.content)
    except ValueError:
        await author.send('Неверный формат ответа')
        return

    # функция, которая будет вызываться, когда реакция будет добавлена к сообщению
    async def on_reaction_add(reaction, user):
        # проверяем, что реакция добавлена к нужному сообщению
        if reaction.message.id != message.id:
            return

        # проверяем, что количество реакций достаточно для розыгрыша
        if reaction.count >= reaction_count:
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

    # добавляем обработчик реакций
    bot.add_listener(on_reaction_add)

# запускаем бота
bot.run(config['token'])

