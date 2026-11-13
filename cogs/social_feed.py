"""
cogs/social_feed.py
-----------------------
مراقبة قناة يوتيوب الخاصة بـ Wiam.dev، وإرسال إعلان تلقائي (بلسان
wiam نفسها، بنفس روح باقي رسائل البوت) في قناة "أخبار وئام"
(config.CHANNELS["social_updates"]) عند نزول فيديو جديد.

الطريقة: نعتمد على رابط RSS الرسمي المجاني من يوتيوب (بدون أي مفتاح
API ولا تسجيل ولا حدود استخدام)، ونفحصه دوريًا للمقارنة مع آخر فيديو
معروف. نحوّل @handle (المضبوط في config.YOUTUBE_HANDLE) إلى الـ
channel_id الحقيقي تلقائيًا عند أول فحص.

"""

import json
import logging
import os
import re
import xml.etree.ElementTree as ET

import aiohttp
import discord
from discord.ext import commands, tasks

import config

logger = logging.getLogger("owl-bot")

STATE_FILE = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "data", "social_feed_state.json"
)

_XML_NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "yt": "http://www.youtube.com/xml/schemas/2015",
}


def _load_state() -> dict:
    if not os.path.isfile(STATE_FILE):
        return {}
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def _save_state(state: dict) -> None:
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f)


_MEDIA_NS = {"media": "http://search.yahoo.com/mrss/"}


def _parse_latest_video(xml_text: str):
    """يستخرج أحدث فيديو (video_id, title, link, description) من نص RSS."""
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return None, None, None, None

    entry = root.find("atom:entry", _XML_NS)
    if entry is None:
        return None, None, None, None

    video_id = entry.findtext("yt:videoId", namespaces=_XML_NS)
    title = entry.findtext("atom:title", namespaces=_XML_NS)
    link_el = entry.find("atom:link", _XML_NS)
    link = link_el.get("href") if link_el is not None else None

    # الوصف موجود داخل media:group/media:description في RSS يوتيوب
    description = None
    media_group = entry.find("media:group", _MEDIA_NS)
    if media_group is not None:
        description = media_group.findtext("media:description", namespaces=_MEDIA_NS)

    return video_id, title, link, description


class SocialFeed(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.youtube_channel_id: str | None = None
        self._last_warning: str | None = None
        self.state = _load_state()
        self.check_youtube.start()

    def cog_unload(self):
        self.check_youtube.cancel()

    async def _resolve_youtube_channel_id(self, session: aiohttp.ClientSession) -> str | None:
        """يحصل على channel_id (مطلوب لرابط الـRSS): من config مباشرة، وإلا من صفحة القناة."""
        manual_id = getattr(config, "YOUTUBE_CHANNEL_ID", None)
        if manual_id:
            return manual_id

        handle = config.YOUTUBE_HANDLE
        if not handle:
            return None

        url = f"https://www.youtube.com/@{handle}"
        # نتجاوز صفحة الموافقة (Consent) التي يعرضها يوتيوب لبعض السيرفرات
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
            "Cookie": "CONSENT=YES+1; SOCS=CAI",
        }
        try:
            async with session.get(url, headers=headers) as resp:
                if resp.status != 200:
                    self._warn_once(f"تعذّر الوصول لصفحة يوتيوب @{handle} (status {resp.status}).")
                    return None
                html = await resp.text()
        except Exception as e:
            self._warn_once(f"خطأ أثناء جلب صفحة يوتيوب: {e}")
            return None

        patterns = (
            r'"channelId":"(UC[\w-]{22})"',
            r'"externalId":"(UC[\w-]{22})"',
            r'channel_id=(UC[\w-]{22})',
            r'youtube\.com/channel/(UC[\w-]{22})',
        )
        for pattern in patterns:
            match = re.search(pattern, html)
            if match:
                return match.group(1)

        self._warn_once(
            f"لم يتم العثور على channelId لـ @{handle} (يوتيوب لا يعرض الصفحة لهذا السيرفر "
            "أو الاسم خاطئ). الحل: ضع YOUTUBE_CHANNEL_ID مباشرة في config.py."
        )
        return None

    def _warn_once(self, message: str) -> None:
        """يسجّل التحذير مرة واحدة فقط بدل تكراره كل 10 دقائق."""
        if message != self._last_warning:
            logger.warning(message)
            self._last_warning = message

    @tasks.loop(minutes=10)
    async def check_youtube(self):
        channel_id_cfg = config.CHANNELS.get("social_updates")
        if not channel_id_cfg:
            return  # القناة غير مضبوطة بعد في config.py

        target_channel = None
        for guild in self.bot.guilds:
            found = guild.get_channel(channel_id_cfg)
            if found is not None:
                target_channel = found
                break

        if target_channel is None:
            return

        async with aiohttp.ClientSession() as session:
            if self.youtube_channel_id is None:
                self.youtube_channel_id = await self._resolve_youtube_channel_id(session)
                if self.youtube_channel_id is None:
                    return

            feed_url = (
                "https://www.youtube.com/feeds/videos.xml"
                f"?channel_id={self.youtube_channel_id}"
            )
            try:
                async with session.get(feed_url) as resp:
                    if resp.status != 200:
                        return
                    xml_text = await resp.text()
            except Exception as e:
                logger.warning(f"خطأ أثناء جلب RSS يوتيوب: {e}")
                return

        video_id, title, link, description = _parse_latest_video(xml_text)
        if video_id is None:
            return

        last_seen = self.state.get("youtube_last_id")

        if last_seen is None:
            # أول تشغيل: نسجل الفيديو الحالي كمرجع فقط، بدون إعلان،
            # حتى لا يُعلن فجأة عن فيديو قديم عند تفعيل الميزة أول مرة.
            self.state["youtube_last_id"] = video_id
            _save_state(self.state)
            return

        if video_id == last_seen:
            return

        self.state["youtube_last_id"] = video_id
        _save_state(self.state)

        # وصف الفيديو غالبًا طويل - نقتصر على أول سطرين حتى لا يطغى على البطاقة
        short_description = None
        if description:
            short_description = description.strip().split("\n\n")[0][:300]

        embed = discord.Embed(
            title=title,
            url=link,
            description=short_description,
            color=config.COLOR_PRIMARY,
        )
        # صورة مصغّرة (Thumbnail) حقيقية من يوتيوب حتى يبان الفيديو مباشرة
        # في الرسالة، بدل الاعتماد فقط على معاينة ديسكورد التلقائية للرابط.
        embed.set_image(url=f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg")
        embed.set_footer(text=config.BOT_NAME)

        try:
            await target_channel.send(content="🎥 نزّلت فيديو جديد على يوتيوب!", embed=embed)
        except discord.Forbidden:
            logger.warning("لا يملك البوت صلاحية الإرسال في قناة أخبار وئام.")

    @check_youtube.before_loop
    async def before_check_youtube(self):
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot):
    await bot.add_cog(SocialFeed(bot))
