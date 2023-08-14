# cogs/commands.py
import discord
from discord.ext import commands
import yt_dlp
import random
from data.data import server_data


class CommandsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        description="Play a video or a playlist on YouTube\n"
        "\u1CBC\u1CBC\u1CBC\u1CBC *`!play {youtube url}`*\n"
        "\u1CBC\u1CBC\u1CBC\u1CBC *`!play {youtube playlist url}` (random ordering)*\n"
        ""
    )
    async def play(self, ctx):
        try:
            if not ctx.author.voice:
                raise AttributeError("You must first join a voice channel")

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
            send_message = "\n".join(
                [
                    "- *!play `{youtube url}`*",
                    "- *!play `{youtube playlist url}`*",
                ]
            )
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

        except AttributeError as e:
            embed = discord.Embed(
                title=str(e),
                color=discord.Color.red(),
            )
            await ctx.send(embed=embed)
        except Exception as e:
            print(e)
            embed = discord.Embed(
                title="An error occurred while playing music! Please try again later.",
                color=discord.Color.red(),
            )
            await ctx.send(embed=embed)

    async def play_song(self, ctx, voice_client):
        async def play_next(ctx, voice_client):
            if ctx.guild.id in server_data:
                server_data[ctx.guild.id].pop(0)
                if server_data[ctx.guild.id]:
                    await self.play_song(ctx, voice_client)
                else:
                    embed = discord.Embed(
                        title="Playlist has ended",
                        color=discord.Color.green(),
                    )
                    await ctx.send(embed=embed)

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
                        if entry["title"] != "Private video":
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

    @commands.command(description="Skip a song\n" " ")
    async def skip(self, ctx):
        if ctx.guild.id in server_data:
            if len(server_data[ctx.guild.id]):
                embed = discord.Embed(
                    title="Skip",
                    color=discord.Color.green(),
                )
                await ctx.send(embed=embed)
                voice_client = ctx.voice_client
                voice_client.stop()

    @commands.command(description="Pause the song\n" " ")
    async def pause(self, ctx):
        if ctx.guild.id in server_data:
            if ctx.voice_client.is_playing():
                embed = discord.Embed(
                    title="Paused",
                    color=discord.Color.green(),
                )
                await ctx.send(embed=embed)
                ctx.voice_client.pause()

    @commands.command(description="Resume the song\n" " ")
    async def resume(self, ctx):
        if ctx.guild.id in server_data:
            if ctx.voice_client.is_paused():
                embed = discord.Embed(
                    title="Resume",
                    color=discord.Color.green(),
                )
                await ctx.send(embed=embed)
                ctx.voice_client.resume()

    @commands.command(description="Show the next ten songs\n" " ")
    async def show(self, ctx):
        if ctx.guild.id in server_data:
            if len(server_data[ctx.guild.id]):
                embed = discord.Embed(
                    title=f"Playlist ({len(server_data[ctx.guild.id])} songs remaining)",
                    color=discord.Color.purple(),
                )
                for index, song_info in enumerate(server_data[ctx.guild.id], start=1):
                    if index == 11:
                        break
                    video_url = song_info["video_url"]
                    title = song_info["title"]
                    embed.add_field(
                        name=f"♪ \u00A0 Track {index}",
                        value=f"[{title}]({video_url})",
                        inline=False,
                    )
                await ctx.send(embed=embed)

            else:
                embed = discord.Embed(
                    title="Playlist is empty",
                    color=discord.Color.red(),
                )
                await ctx.send(embed=embed)

    @commands.command(description="Exit voice channel\n" " ")
    async def exit(self, ctx):
        if ctx.guild.id in server_data:
            await ctx.voice_client.disconnect()
            del server_data[ctx.guild.id]

    @commands.command(description="Show the help message\n" " ")
    async def help(self, ctx):
        embed = discord.Embed(
            title="Commands List",
            color=discord.Color.green(),
        )

        for cmd in self.get_commands():
            embed.add_field(
                name=f"***!{cmd.name}***",
                value=f"\u1CBC\u1CBC{cmd.description}"
                if cmd.description
                else "No description available.",
                inline=False,
            )

        await ctx.send(embed=embed)
