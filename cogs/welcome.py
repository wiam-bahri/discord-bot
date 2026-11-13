"""
cogs/welcome.py
-----------------
مسؤول عن استقبال الأعضاء الجدد وإرسال رسالة الترحيب في قناة welcome.
"""

import logging

import discord
from discord.ext import commands

import config
from utils.embeds import build_welcome_embed
from views.onboarding_views import OnboardingStartView

logger = logging.getLogger("owl-bot")


class Welcome(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """يُستدعى تلقائيًا عند دخول عضو جديد إلى السيرفر."""

        # رسالة ترحيب شخصية في الخاص - إن كانت الرسائل الخاصة مغلقة عند
        # العضو، نتجاهل الخطأ بهدوء ونكمل بإرسال الرسالة العامة كالمعتاد.
        try:
            await member.send(config.DM_WELCOME_MESSAGE.format(mention=member.mention))
        except discord.Forbidden:
            logger.warning(f"لا يمكن إرسال رسالة خاصة إلى {member} - الرسائل الخاصة مغلقة.")

        channel_id = config.CHANNELS.get("welcome")

        if not channel_id:
            logger.warning(
                "لم يتم ضبط CHANNELS['welcome'] في config.py - "
                "لن تُرسل رسالة الترحيب."
            )
            return

        channel = member.guild.get_channel(channel_id)

        if channel is None:
            logger.warning(
                f"لم يتم العثور على قناة بالـ ID: {channel_id}. "
                "تأكد من صحة CHANNELS['welcome'] في config.py."
            )
            return

        embed, gif_file = build_welcome_embed(member)
        view = OnboardingStartView()

        if gif_file is None:
            logger.warning(
                f"لم يتم العثور على ملف الـ GIF '{config.WELCOME_GIF_FILENAME}' "
                "داخل assets/gifs/. سيتم إرسال الترحيب بدون صورة."
            )

        try:
            send_kwargs = {"content": member.mention, "embed": embed, "view": view}
            if gif_file is not None:
                send_kwargs["file"] = gif_file

            await channel.send(**send_kwargs)
            logger.info(f"تم إرسال رسالة الترحيب للعضو الجديد: {member}")
        except discord.Forbidden:
            logger.error(
                f"لا يملك البوت صلاحية الإرسال في قناة {channel.name}. "
                "تحقق من صلاحيات البوت في القناة."
            )
        except Exception as e:
            logger.error(f"خطأ غير متوقع أثناء إرسال رسالة الترحيب: {e}")


async def setup(bot: commands.Bot):
    await bot.add_cog(Welcome(bot))
