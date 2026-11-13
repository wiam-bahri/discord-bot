"""
views/admin_views.py
------------------------
اللوحة الإدارية: زر واحد فقط "إرسال رسالة".
الزر يتحقق من is_admin بنفسه كحماية إضافية.
"""

import logging

import discord

import config
from utils.permissions import is_admin

logger = logging.getLogger("owl-bot")


class SendMessageModal(discord.ui.Modal, title="إرسال رسالة"):
    """
    إذا كُتب عنوان تُرسل الرسالة كـ Embed منسّق،
    وإذا تُرك العنوان فارغًا تُرسل كنص عادي بلسان البوت.
    """

    content = discord.ui.TextInput(
        label="نص الرسالة",
        style=discord.TextStyle.paragraph,
        max_length=2000,
        required=True,
    )
    embed_title = discord.ui.TextInput(
        label="عنوان (اختياري - يحوّلها لـ Embed)",
        max_length=256,
        required=False,
    )
    image_url = discord.ui.TextInput(
        label="رابط صورة (اختياري، يعمل مع العنوان فقط)",
        required=False,
    )

    async def on_submit(self, interaction: discord.Interaction):
        embed = None
        if self.embed_title.value.strip():
            embed = discord.Embed(
                title=self.embed_title.value.strip(),
                description=self.content.value,
                color=config.COLOR_PRIMARY,
            )
            if self.image_url.value.strip():
                embed.set_image(url=self.image_url.value.strip())

        await interaction.response.send_message(
            "📍 اختر القناة اللي تحب ترسل فيها الرسالة:",
            view=ChannelPickerView(content=self.content.value, embed=embed),
            ephemeral=True,
        )


class ChannelPickerView(discord.ui.View):
    """قائمة اختيار قناة، تظهر بعد كتابة الرسالة، وتُرسل فيها بمجرد الاختيار."""

    def __init__(self, content: str, embed: discord.Embed | None):
        super().__init__(timeout=300)
        self.content = content
        self.embed = embed

    @discord.ui.select(
        cls=discord.ui.ChannelSelect,
        placeholder="اختر قناة نصية...",
        channel_types=[discord.ChannelType.text, discord.ChannelType.news],
    )
    async def channel_select(
        self, interaction: discord.Interaction, select: discord.ui.ChannelSelect
    ):
        if not is_admin(interaction):
            await interaction.response.send_message(
                "🔒 هذه الميزة مخصصة للإدارة فقط.", ephemeral=True
            )
            return

        target = select.values[0].resolve() or await select.values[0].fetch()

        try:
            if self.embed is not None:
                await target.send(embed=self.embed)
            else:
                await target.send(self.content)
        except discord.Forbidden:
            await interaction.response.send_message(
                f"❌ ما عنديش صلاحية الإرسال في {target.mention}.", ephemeral=True
            )
            return

        await interaction.response.edit_message(
            content=f"✅ تم إرسال الرسالة في {target.mention}.", view=None
        )


class AdminPanelView(discord.ui.View):
    """اللوحة الإدارية الثابتة (زر واحد: إرسال رسالة)."""

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="إرسال رسالة",
        emoji="📨",
        style=discord.ButtonStyle.primary,
        custom_id="admin:sendmsg",
    )
    async def send_message_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_admin(interaction):
            await interaction.response.send_message(
                "🔒 هذه اللوحة مخصصة للإدارة فقط.", ephemeral=True
            )
            return
        await interaction.response.send_modal(SendMessageModal())
