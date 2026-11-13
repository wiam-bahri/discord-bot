"""
main.py
--------
نقطة انطلاق البوت. الميزات الحالية فقط:
- الترحيب + الرسالة الخاصة التلقائية للأعضاء الجدد
- القائمة الرئيسية (من هي وئام / تابعوني)
- أخبار وئام (يوتيوب تلقائيًا)
- اللوحة الإدارية (إرسال رسالة)
"""

import asyncio
import logging

import discord
from discord.ext import commands

import config
from views.onboarding_views import OnboardingStartView
from views.menu_views import BotChatMenuView
from views.admin_views import AdminPanelView

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("bot.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("owl-bot")

# Members Intent فقط: ضروري لمعرفة دخول الأعضاء الجدد
intents = discord.Intents.default()
intents.members = True


class OwlBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents, help_command=None)

    async def setup_hook(self):
        # أزرار ثابتة تبقى تعمل بعد إعادة التشغيل
        self.add_view(OnboardingStartView())
        self.add_view(BotChatMenuView())
        self.add_view(AdminPanelView())

        for cog in (
            "cogs.welcome",
            "cogs.bot_chat",
            "cogs.social_feed",
            "cogs.admin_panel",
        ):
            await self.load_extension(cog)
            logger.info(f"تم تحميل cog: {cog}")

        # لم تعد هناك أوامر Slash. نزامن شجرة فارغة حتى تختفي الأوامر
        # القديمة (/stats, /profile ...) من ديسكورد.
        try:
            if config.GUILD_ID:
                guild = discord.Object(id=int(config.GUILD_ID))
                self.tree.clear_commands(guild=guild)
                await self.tree.sync(guild=guild)
            else:
                await self.tree.sync()
            logger.info("تم تنظيف أوامر Slash القديمة.")
        except Exception as e:
            logger.error(f"فشل تنظيف أوامر Slash: {e}")

    async def on_ready(self):
        logger.info(f"✅ البوت متصل الآن باسم: {self.user} (ID: {self.user.id})")


async def main():
    if not config.DISCORD_BOT_TOKEN:
        logger.error("لم يتم العثور على DISCORD_BOT_TOKEN في ملف .env")
        return

    bot = OwlBot()
    async with bot:
        await bot.start(config.DISCORD_BOT_TOKEN)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("تم إيقاف البوت يدويًا.")
