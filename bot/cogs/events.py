from discord.ext import commands
from data.data import server_data


class EventsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Logged in as {self.bot.user.name}")

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if not member.bot and before.channel and not after.channel:
            if before.channel.guild.voice_client and len(before.channel.members) == 1:
                await before.channel.guild.voice_client.disconnect()
                del server_data[before.channel.guild.id]
