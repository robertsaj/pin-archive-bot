import discord
import os

from discord.ext import commands
from dotenv import load_dotenv
from random import randrange


load_dotenv()
bot = commands.Bot(command_prefix='/', status='Ready to archive')
archive_channel = None

EMBED_COLORS = [
    discord.Colour.magenta(),
    discord.Colour.blurple(),
    discord.Colour.dark_teal(),
    discord.Colour.blue(),
    discord.Colour.dark_blue(),
    discord.Colour.dark_gold(),
    discord.Colour.dark_green(),
    discord.Colour.dark_grey(),
    discord.Colour.dark_magenta(),
    discord.Colour.dark_orange(),
    discord.Colour.dark_purple(),
    discord.Colour.dark_red(),
    discord.Colour.darker_grey(),
    discord.Colour.gold(),
    discord.Colour.green(),
    discord.Colour.greyple(),
    discord.Colour.orange(),
    discord.Colour.purple(),
    discord.Colour.magenta(),
]


def random_color():
    return randrange(len(EMBED_COLORS))


async def build_and_send_embed(message):
    global archive_channel
    if archive_channel is not None and message is not None:
        embed = discord.Embed(
            description=f'{message.content}',
            color=random_color(),
        )
        # checks to see if pinned message has attachments
        attachments = message.attachments
        if len(attachments) >= 1:
            embed.set_image(url=attachments[0].url)
        elif len(message.embeds) >= 1:
            embed.set_image(url=message.embeds[0].thumbnail.url)
        embed.add_field(
            name="\u200B",
            value=f'Sent in {message.channel.mention} at: {message.created_at.strftime("%m/%d/%Y, %I:%M %p")}',
        )
        embed.add_field(
            name='\u200B',
            value=f'[Jump]({message.jump_url})',
        )
        embed.set_author(
            name=message.author.name,
            url=message.author.avatar_url,
            icon_url=message.author.avatar_url,
        )
        await archive_channel.send(embed=embed)


async def send_help(channel):
    embed = discord.Embed(
        color=random_color()
    )
    embed.add_field(
        name='/pin.set-archive-channel',
        value='Run this in the channel where you want your shit saved',
        inline=False,
    )
    embed.add_field(
        name='/pin.unpin-all',
        value='Unpins all existing pins from the source channel. Kinda self-explanatory?',
        inline=False,
    )
    embed.add_field(
        name='/pin.archive-all',
        value='Copies all existing pins in the source channel to the archive channel (does not unpin them in the source channel)',
        inline=False,
    )
    embed.add_field(
        name='/pin.archive-and-unpin-all',
        value='Moves all existing pins in the source channel to the archive channel (unpins them in the source channel)',
        inline=False,
    )
    embed.add_field(
        name='/pin.help',
        value='You\'re lookin\' at it',
        inline=False,
    )
    await channel.send(embed=embed)


async def set_archive(message):
    f = open('archive-channel.txt', 'w')
    f.write(f'{message.channel.id}')
    f.close()
    await message.channel.send(f'Successfully set archive to #{message.channel.name}')
    await load_archive_channel_from_file()


async def set_bot_idle():
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.listening,
            name=f'/pin',
        ),
        status=discord.Status.idle,
    )


async def set_bot_online():
    global archive_channel
    if archive_channel is not None:
        await bot.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.playing,
                name=f'to #{archive_channel.name}',
            ),
            status=discord.Status.online,
        )


async def load_archive_channel_from_file():
    global archive_channel
    try:
        f = open('archive-channel.txt', 'r')
        channel_id = f.read()
        try:
            archive_channel = await bot.fetch_channel(channel_id=channel_id)
            await set_bot_online()
            return
        except discord.errors.NotFound:
            print(f'Could not find archive channel {channel_id}')
        except discord.errors.HTTPException:
            print(f'Malformed channel id {channel_id}')
    except FileNotFoundError:
        print(f'Could not find archive channel file')
    await set_bot_idle()


async def archive_all(channel, unpin=False):
    global archive_channel
    if archive_channel is None:
        await channel.send(f'No archive channel set: use /pin.set-archive-channel in the target archive channel')
        return
    for pin in await channel.pins():
        pinned_message = await channel.fetch_message(pin.id)
        await build_and_send_embed(pinned_message)
        if unpin:
            await pinned_message.unpin()
    await channel.send(f'Successfully {"moved" if unpin else "copied"} all pins to #{archive_channel.name}')


async def unpin_all(channel):
    for pin in await channel.pins():
        pinned_message = await channel.fetch_message(pin.id)
        await pinned_message.unpin()
    await channel.send('Successfully unpinned all pins')


@bot.event
async def on_ready():
    await load_archive_channel_from_file()
    print(f'Logged in as {bot.user}')


@bot.event
async def on_message(message):
    global archive_channel

    if message.type == discord.MessageType.pins_add:
        await message.delete()

    if message.author == bot.user:
        return

    if message.content == '/pin.set-archive-channel':
        await set_archive(message)
        return

    if message.content == '/pin.unpin-all':
        await unpin_all(message.channel)

    if message.content == '/pin.archive-all':
        await archive_all(message.channel, unpin=False)

    if message.content == '/pin.archive-and-unpin-all':
        await archive_all(message.channel, unpin=True)

    if message.content == '/pin.help' or message.content == '/pin':
        await send_help(message.channel)


@bot.event
async def on_raw_message_edit(payload):
    global archive_channel
    if archive_channel is not None:
        pinned = payload.data.get('pinned', False)
        if pinned:
            source_channel = await bot.fetch_channel(payload.channel_id)
            source_message = await source_channel.fetch_message(payload.message_id)
            if source_channel == archive_channel:
                await archive_channel.send('Why are you pinning in the archive channel? Freak.')
            else:
                await build_and_send_embed(source_message)
            await source_message.unpin()

bot.run(os.getenv('TOKEN'))
