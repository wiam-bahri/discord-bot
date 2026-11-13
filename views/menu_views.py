"""
views/menu_views.py
----------------------
القائمة الرئيسية في قناة bot-chat: زران فقط
(من هي وئام / تابعوني).
"""

import discord

import config


class BotChatMenuView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="من هي وئام",
        emoji="👤",
        style=discord.ButtonStyle.secondary,
        custom_id="botchat:about",
    )
    async def about_me(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="👩‍💻 عن صاحبة المجتمع",
            description=config.CREATOR_ABOUT_TEXT,
            color=config.COLOR_PRIMARY,
        )
        embed.set_footer(text=config.BOT_NAME)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(
        label="تابعوني",
        emoji="🔗",
        style=discord.ButtonStyle.secondary,
        custom_id="botchat:socials",
    )
    async def socials(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(title="🔗 تابعوني هنا", color=config.COLOR_PRIMARY)

        link_view = discord.ui.View()
        has_links = False
        for name, url in config.SOCIAL_LINKS.items():
            if url:
                link_view.add_item(
                    discord.ui.Button(label=name, url=url, style=discord.ButtonStyle.link)
                )
                has_links = True

        if not has_links:
            embed.description = "لم تتم إضافة الروابط بعد."
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(embed=embed, view=link_view, ephemeral=True)
