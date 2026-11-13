"""
cogs/bot_chat.py
-------------------
مسؤول عن إرسال القائمة الرئيسية في قناة bot-chat، مرة واحدة فقط.

نتحقق من سجل الرسائل أولًا حتى لا تتكرر القائمة كل مرة يُعاد فيها
تشغيل البوت (نفس مبدأ منع التكرار المطلوب في المشروع).
"""

import logging

import discord
from discord.ext import commands

import config
from views.menu_views import BotChatMenuView

logger = logging.getLogger("owl-bot")

# نص مميز نضعه في الـ footer للتعرف على رسالة القائمة عند البحث عنها لاحقًا
PANEL_MARKER = "botchat_panel_v1"


class BotChat(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        await self.ensure_panel_posted()

    async def ensure_panel_posted(self):
        channel_id = config.CHANNELS.get("bot_chat")

        if not channel_id:
            logger.warning(
                "لم يتم ضبط CHANNELS['bot_chat'] في config.py - "
                "لن تُرسل قائمة bot-chat."
            )
            return

        for guild in self.bot.guilds:
            channel = guild.get_channel(channel_id)
            if channel is None:
                continue

            try:
                existing_message = None
                async for message in channel.history(limit=20):
                    if (
                        message.author.id == self.bot.user.id
                        and message.embeds
                        and message.embeds[0].footer
                        and message.embeds[0].footer.text == PANEL_MARKER
                    ):
                        existing_message = message
                        break

                embed = discord.Embed(
                    title=f"👋 أهلًا! أنا {config.BOT_NAME}",
                    description="ماذا تريد أن تفعل؟ اختر من الأزرار بالأسفل 👇",
                    color=config.COLOR_PRIMARY,
                )
                embed.set_footer(text=PANEL_MARKER)

                if existing_message is not None:
                    # الرسالة موجودة من قبل - نحدّثها بنفس الـ Embed والأزرار
                    # الحالية بدل تركها بأزرار قديمة أو إرسال نسخة مكرّرة.
                    # هذا يعني أن أي تعديل لاحق على الأزرار في الكود سينعكس
                    # تلقائيًا هنا بمجرد إعادة تشغيل البوت، دون حذف يدوي.
                    await existing_message.edit(embed=embed, view=BotChatMenuView())
                    logger.info("تم تحديث قائمة bot-chat الرئيسية بالأزرار الحالية.")
                else:
                    await channel.send(embed=embed, view=BotChatMenuView())
                    logger.info("تم إرسال قائمة bot-chat الرئيسية.")

            except discord.Forbidden:
                logger.error(
                    f"لا يملك البوت صلاحية الوصول لقناة {channel.name}. "
                    "تحقق من الصلاحيات (View Channel, Read Message History, Send Messages)."
                )
            except Exception as e:
                logger.error(f"خطأ غير متوقع أثناء إعداد قائمة bot-chat: {e}")


async def setup(bot: commands.Bot):
    await bot.add_cog(BotChat(bot))
