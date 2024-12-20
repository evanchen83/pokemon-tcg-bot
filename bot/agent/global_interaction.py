import discord

_INTERACTION = None


def get_interaction() -> discord.Interaction:
    return _INTERACTION


def set_interaction(interaction: discord.Interaction):
    global _INTERACTION
    _INTERACTION = interaction
