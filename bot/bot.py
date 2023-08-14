import discord
import asyncio
from discord.ext import commands
from bot.config import getToken
from cogs.commands import CommandsCog
from cogs.events import EventsCog

intents = discord.Intents.default()
intents.voice_states = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


async def addCogs():
    await bot.add_cog(CommandsCog(bot))
    await bot.add_cog(EventsCog(bot))


if __name__ == "__main__":
    asyncio.run(addCogs())
    asyncio.run(bot.run(getToken()))
