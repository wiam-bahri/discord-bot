"""
cogs/admin_panel.py
-----------------------
مسؤول عن إرسال اللوحة الإدارية في قناة admin_panel، مرة واحدة فقط،
ثم تحديثها تلقائيًا عند كل إقلاع إذا تغيّرت الأزرار مستقبلًا.

هذه القناة يجب أن تكون مخفية عن الأعضاء العاديين من إعدادات صلاحيات
القناة نفسها في ديسكورد (Server Settings > Roles أو صلاحيات القناة
مباشرة) - البوت لا يُنشئ أو يُخفي القناة تلقائيًا، فقط يرسل اللوحة
فيها بافتراض أنها مضبوطة مسبقًا لتكون خاصة بالإدارة.
"""

import logging

import discord
from discord.ext import commands

import config
from views.admin_views import AdminPanelView

logger = logging.getLogger("owl-bot")

PANEL_MARKER = "admin_panel_v1"


class AdminPanel(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        await self.ensure_panel_posted()

    async def ensure_panel_posted(self):
        channel_id = config.CHANNELS.get("admin_panel")

        if not channel_id:
            logger.warning(
                "لم يتم ضبط CHANNELS['admin_panel'] في config.py - "
                "لن تُرسل اللوحة الإدارية."
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
                    title="🔒 اللوحة الإدارية",
                    description="أزرار سريعة لأهم المهام الإدارية 👇",
                    color=config.COLOR_PRIMARY,
                )
                embed.set_footer(text=PANEL_MARKER)

                if existing_message is not None:
                    await existing_message.edit(embed=embed, view=AdminPanelView())
                    logger.info("تم تحديث اللوحة الإدارية بالأزرار الحالية.")
                else:
                    await channel.send(embed=embed, view=AdminPanelView())
                    logger.info("تم إرسال اللوحة الإدارية.")

            except discord.Forbidden:
                logger.error(
                    f"لا يملك البوت صلاحية الوصول لقناة {channel.name}. "
                    "تحقق من الصلاحيات (View Channel, Read Message History, Send Messages)."
                )


async def setup(bot: commands.Bot):
    await bot.add_cog(AdminPanel(bot))
