"""
views/onboarding_views.py
----------------------------
زر "Let's get started" في رسالة الترحيب.

لا يوجد أي إجبار على الإجابة، ولا أسئلة، ولا موافقة على قواعد،
ولا رتبة "غير موثّق" تُخفي القنوات. مجرد رسالة ودّية بسيطة توجّه
العضو إلى قناة bot-chat حيث يمكنه استكشاف السيرفر بنفسه.
"""

import discord

import config


class OnboardingStartView(discord.ui.View):
    """
    timeout=None لأن هذا الزر يجب أن يبقى قابلاً للاستخدام إلى الأبد
    (حتى بعد إعادة تشغيل البوت).
    """

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Let's get started",
        style=discord.ButtonStyle.primary,
        emoji="🚀",
        custom_id="onboarding:start",  # ثابت حتى يعمل الزر بعد إعادة تشغيل البوت
    )
    async def start_onboarding(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        bot_chat_id = config.CHANNELS.get("bot_chat")
        bot_chat_mention = f"<#{bot_chat_id}>" if bot_chat_id else "#bot-chat"

        await interaction.response.send_message(
            f"أهلًا بك {interaction.user.mention}! 🎉\n\n"
            f"استكشف السيرفر بحرية، وإذا احتجت أي شيء توجّه إلى {bot_chat_mention} "
            f"للتحدث معي أو معرفة المزيد عن المجتمع 👋",
            ephemeral=True,
        )
