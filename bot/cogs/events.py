from discord.ext import commands
from data.data import server_data, server_loop


class EventsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Logged in as {self.bot.user.name}")

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.bot and before.channel and not after.channel:
            if before.channel.guild.id in server_data:
                await before.channel.guild.voice_client.disconnect()
                del server_data[before.channel.guild.id]
                del server_loop[before.channel.guild.id]

        elif not member.bot and before.channel and not after.channel:
            if before.channel.guild.voice_client and len(before.channel.members) == 1:
                await before.channel.guild.voice_client.disconnect()
                del server_data[before.channel.guild.id]
                del server_loop[before.channel.guild.id]
