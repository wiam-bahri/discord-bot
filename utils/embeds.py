"""
utils/embeds.py
-----------------
Embed رسالة الترحيب.
"""

import os

import discord

import config

ASSETS_GIFS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "gifs")


def _attach_local_gif(embed: discord.Embed, gif_filename: str | None) -> discord.File | None:
    """يربط ملف GIF محلي بالـ Embed، ويُعيد None إن لم يوجد الملف."""
    if not gif_filename:
        return None

    gif_path = os.path.join(ASSETS_GIFS_DIR, gif_filename)
    if not os.path.isfile(gif_path):
        return None

    embed.set_image(url=f"attachment://{gif_filename}")
    return discord.File(gif_path, filename=gif_filename)


def build_welcome_embed(member: discord.Member) -> tuple[discord.Embed, discord.File | None]:
    """يبني Embed الترحيب الذي يظهر عند دخول عضو جديد إلى قناة welcome."""
    description = config.WELCOME_DESCRIPTION.format(bot_name=config.BOT_NAME)

    embed = discord.Embed(
        title=config.WELCOME_TITLE,
        description=description,
        color=config.COLOR_PRIMARY,
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.set_footer(text=f"{config.BOT_NAME} • {config.SERVER_NAME}")

    gif_file = _attach_local_gif(embed, getattr(config, "WELCOME_GIF_FILENAME", None))
    return embed, gif_file
