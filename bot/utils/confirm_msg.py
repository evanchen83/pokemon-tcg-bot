async def request_confirm_message(interaction, bot, user, embed):
    message = await interaction.followup.send(embed=embed)
    await message.add_reaction("👍")
    await message.add_reaction("👎")

    def check(reaction, _user):
        return (
            _user == user
            and str(reaction.emoji) in ["👍", "👎"]
            and reaction.message.id == message.id
        )

    try:
        reaction, _ = await bot.wait_for("reaction_add", timeout=60.0, check=check)

        if str(reaction.emoji) == "👍":
            await interaction.followup.send(
                f"{user.name.capitalize()} accepted the request!"
            )
            return True
        elif str(reaction.emoji) == "👎":
            await interaction.followup.send(
                f"{user.name.capitalize()} declined the request."
            )
            return False

    except TimeoutError:
        await interaction.followup.send(
            f"{user.name.capitalize()} did not respond in time."
        )
        return False
