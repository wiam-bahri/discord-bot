"""
utils/permissions.py
-----------------------
التحقق من أن المستخدم أدمن قبل تنفيذ أزرار اللوحة الإدارية.
"""

import discord


def is_admin(interaction: discord.Interaction) -> bool:
    """أدمن = مالك السيرفر، أو Administrator، أو Manage Server."""
    if interaction.guild is None:
        return False

    member = interaction.user
    if not isinstance(member, discord.Member):
        return False

    if interaction.guild.owner_id == member.id:
        return True

    perms = member.guild_permissions
    return perms.administrator or perms.manage_guild
