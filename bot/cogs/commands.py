# cogs/commands.py
import discord
from discord.ext import commands
import yt_dlp
import random
from data.data import server_data


class CommandsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def play(self, ctx):
        try:
            voice_channel = ctx.author.voice.channel
            params = ctx.message.content.split(" ")
            video_list = await self.ydl_extractor(
                extract_music_url=False, given_url=params[1]
            )

            if ctx.guild.id not in server_data:
                server_data[ctx.guild.id] = []

            server_data[ctx.guild.id].extend(video_list)

            if not ctx.voice_client:
                voice_client = await voice_channel.connect()
                await self.play_song(ctx, voice_client)

        except IndexError:
            commands = [
                "- *!play `{youtube url}`*",
                "- *!play `{youtube playlist url}`*",
            ]
            send_message = "\n".join(commands)
            embed = discord.Embed(
                title="Command Format is Incorrect",
                description=send_message,
                color=discord.Color.red(),
            )
            embed.set_footer(
                text="you sucks",
                icon_url="https://media.tenor.com/hu4sl_5rDXcAAAAC/cat-catcry.gif",
            )
            await ctx.send(embed=embed)
            return

        except AttributeError:
            await ctx.send("You must first join a voice channel!")
            return

        except Exception as e:
            print(e)
            await ctx.send(
                "An error occurred while playing music! Please try again later."
            )

    @commands.command()
    async def skip(self, ctx):
        if ctx.guild.id in server_data:
            embed = discord.Embed(
                title="You skipped a song",
                color=discord.Color.blue(),
            )
            await ctx.send(embed=embed)
            voice_client = ctx.voice_client
            voice_client.stop()

    async def play_song(self, ctx, voice_client):
        async def play_next(ctx, voice_client):
            if ctx.guild.id in server_data:
                server_data[ctx.guild.id].pop(0)
                if server_data[ctx.guild.id]:
                    await self.play_song(ctx, voice_client)
                else:
                    del server_data[ctx.guild.id]

        if ctx.guild.id in server_data:
            video_url = server_data[ctx.guild.id][0]["video_url"]
            title = server_data[ctx.guild.id][0]["title"]

            embed = discord.Embed(
                title=f"Now playing\n",
                description=f"♪ \u00A0 **[{title}]({video_url})**",
                color=discord.Color.blue(),
            )
            await ctx.send(embed=embed)

            music_url = await self.ydl_extractor(
                extract_music_url=True, given_url=video_url
            )
            ffmpeg_opts = {
                "options": "-vn",
                "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
            }
            voice_client.play(
                discord.FFmpegPCMAudio(music_url, **ffmpeg_opts),
                after=lambda error: self.bot.loop.create_task(
                    play_next(ctx, voice_client)
                ),
            )

    async def ydl_extractor(self, extract_music_url, given_url):
        ydl_opts = {
            "format": "bestaudio/best",
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ],
            "extract_flat": True,
            "verbose": False,
        }

        video_list = []

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(given_url, download=False)

            # For Debugging
            # with open("info.json", "w") as json_file:
            #     json.dump(info, json_file, indent=4)

            if extract_music_url:
                return info["url"]
            else:
                if "entries" in info:
                    # playlist url
                    for entry in info["entries"]:
                        video_info = {
                            "title": entry["title"],
                            "video_url": entry["url"],
                        }
                        video_list.append(video_info)
                    random.shuffle(video_list)
                else:
                    # video url
                    video_info = {
                        "title": info["title"],
                        "video_url": given_url,
                    }
                    video_list.append(video_info)
        return video_list
