# cogs/commands.py
import discord
from discord.ext import commands
import yt_dlp
import random
from data.data import server_data, server_loop
import json


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
            params = ctx.message.content.split()
            video_list = await self.ydl_extractor(
                extract_music_url=False, given_url=params[1]
            )

            if ctx.guild.id not in server_data:
                server_data[ctx.guild.id] = []
                server_loop[ctx.guild.id] = False

            server_data[ctx.guild.id].extend(video_list)

            if not ctx.voice_client:
                voice_client = await voice_channel.connect()
                await self.play_song(ctx, voice_client)
            elif not ctx.voice_client.is_playing():
                await self.play_song(ctx, ctx.voice_client)

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
                if not server_loop[ctx.guild.id]:
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
            if not server_loop[ctx.guild.id]:
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
                if "ie_key" in info:
                    # if the url is a video in a playlist
                    return await self.ydl_extractor(
                        extract_music_url=False, given_url=info["url"]
                    )
                elif "entries" in info:
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

    @commands.command(
        description="Skip one or multiple songs\n"
        "\u1CBC\u1CBC\u1CBC\u1CBC *`!skip {song number}(optional)`*\n"
        ""
    )
    async def skip(self, ctx):
        if ctx.guild.id in server_data:
            if len(server_data[ctx.guild.id]):
                params = ctx.message.content.split()
                num = params[1] if len(params) >= 2 else "#"
                server_loop[ctx.guild.id] = False
                if num.isdigit() and int(num) > 1:
                    num = int(num)
                    if num >= len(server_data[ctx.guild.id]):
                        title = f"Skip {len(server_data[ctx.guild.id])} songs"
                        server_data[ctx.guild.id] = server_data[ctx.guild.id][-1:]
                    else:
                        title = f"Skip {num} songs"
                        server_data[ctx.guild.id] = (
                            server_data[ctx.guild.id][num:]
                            if server_loop[ctx.guild.id]
                            else server_data[ctx.guild.id][num - 1 :]
                        )
                else:
                    title = "Skip"

                embed = discord.Embed(
                    title=title,
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

    @commands.command(description="Enable or disable loop playback\n" " ")
    async def loop(self, ctx):
        if ctx.guild.id in server_data:
            if ctx.voice_client.is_playing():
                title = "Looping " + ("off" if server_loop[ctx.guild.id] else "on")
                embed = discord.Embed(
                    title=title,
                    color=discord.Color.green(),
                )
                await ctx.send(embed=embed)
                server_loop[ctx.guild.id] = not server_loop[ctx.guild.id]

    @commands.command(description="Show the next ten songs\n" " ")
    async def show(self, ctx):
        if ctx.guild.id in server_data:
            if len(server_data[ctx.guild.id]):
                remain = (
                    f"*({len(server_data[ctx.guild.id])} songs remaining)*"
                    if len(server_data[ctx.guild.id]) > 10
                    else ""
                )
                embed = discord.Embed(
                    title=f"Playlist ",
                    color=discord.Color.purple(),
                )
                for index, song_info in enumerate(server_data[ctx.guild.id], start=1):
                    if index == 11:
                        break
                    video_url = song_info["video_url"]
                    title = song_info["title"]
                    embed.add_field(
                        name=f"♪ \u00A0 Track {index} "
                        + (" *(playing)*" if index == 1 else "")
                        + (
                            " *(looping)*"
                            if index == 1 and server_loop[ctx.guild.id]
                            else ""
                        ),
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

    @commands.command(description="Shuffle the playlist\n" " ")
    async def shuffle(self, ctx):
        if ctx.guild.id in server_data:
            shuffled_playlist = server_data[ctx.guild.id].copy()
            random.shuffle(shuffled_playlist)
            server_data[ctx.guild.id] = [
                server_data[ctx.guild.id][0]
            ] + shuffled_playlist
            ctx.voice_client.stop()

    @commands.command(description="Exit voice channel\n" " ")
    async def exit(self, ctx):
        if ctx.guild.id in server_data:
            await ctx.voice_client.disconnect()
            del server_data[ctx.guild.id]
            del server_loop[ctx.guild.id]

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

            embed.set_footer(
                text="✉️ kevins30102@yahoo.com.tw",
                icon_url="https://media3.giphy.com/media/v1.Y2lkPTc5MGI3NjExaml6bnByNTZ4aXQxYmFxNWo3M2ZjaXM2emN4dTV1dmEwaWl1bXJraCZlcD12MV9naWZzX3NlYXJjaCZjdD1n/oBQZIgNobc7ewVWvCd/200w.gif",
            )
        await ctx.send(embed=embed)
