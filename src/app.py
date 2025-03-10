import io
import re

import discord
import pytesseract
import requests
from discord.ext import commands
from PIL import Image
from pydantic import ValidationError

from config import Config  # noqa F401
from helper import determine_rank, generate_leaderboard, validate_input, RankUpGpRequirement, RANK_ROLE_IDS
from process_data import evaluate_monthly_gain

# bot.py


# Define your bot with required intents
config = Config()
intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # Required for managing roles
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    # Sync the application commands with Discord.
    await bot.tree.sync()
    print(f"Logged in as {bot.user}")

def is_mod(interaction: discord.Interaction) -> bool:
    """
    Check that the command is invoked by a member with the "mod" role.
    """
    if not interaction.guild:
        return False  # Command must be used in a server
    member = interaction.user
    # Check if the member has any role with the name "mod" (case-insensitive)
    return any(role.name.lower() == "mod" for role in member.roles)

@discord.app_commands.check(is_mod)
@bot.tree.command(name="evaluate_gain", description="Evaluate monthly gain using year, month, and number of top members")
@discord.app_commands.describe(
    year="Year to evaluate",
    month="Month to evaluate",
    n="Number of top members to evaluate",
)
async def evaluate_gain(interaction: discord.Interaction, year: int, month: int, n: int):
    """
    Slash command to call the external function evaluate_monthly_gain.
    Usage in Discord: /evaluate_gain year:<int> month:<int> n:<int>
    """
    try:
        validated_data = validate_input(year, month, n)
    except ValidationError as e:
        print("Validation of user input failed!")
        error_str = "\n".join([f"{error['msg']}" for error in e.errors()])
        await interaction.response.send_message(error_str)
        await interaction(error_str)
        return

    try:
        result = evaluate_monthly_gain(**validated_data.model_dump())
    except ValueError as e:
        await interaction.response.send_message(f"Error: {e}")
        return


    leaderboard = generate_leaderboard(result)

    embed = discord.Embed(
        title="Leaderboard GP Gain",
        description="Here are the top Guild Point gainers, applaud them:",
        color=discord.Color.blurple()
    )
    
    leaderboard_text = ""
    for rank, name, score in leaderboard:
        leaderboard_text += f"**{rank}.** {name} - {score}\n"
    
    embed.add_field(name="Rankings", value=leaderboard_text, inline=False)
    
    # Optionally, set a footer or timestamp.
    embed.set_footer(text="Leaderboard generated by the bot")
    
    await interaction.response.send_message(embed=embed)

@evaluate_gain.error
async def evaluate_gain_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
    if isinstance(error, discord.app_commands.CheckFailure):
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
    else:
        await interaction.response.send_message(f"An error occurred while processing the command. {error}", ephemeral=True)





# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
@bot.event
async def on_message(message: discord.Message):
    # Avoid processing our own messages
    if message.author == bot.user:
        return
    
    if message.channel.id != config.rank_up_channel_id:
        return

    if message.attachments:
        for attachment in message.attachments:
            # Filter out non-image files by extension or content type.
            if any(attachment.filename.lower().endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".webp"]):
                # Fetch the image data from Discord (in memory, no need to save to disk).
                response = requests.get(attachment.url)
                image_data = io.BytesIO(response.content)
                
                # Open the image with Pillow.
                img = Image.open(image_data)
                
                # Perform OCR using pytesseract.
                # This returns all recognized text from the image.
                recognized_text = pytesseract.image_to_string(img)
                print("Recognized text:", recognized_text)
                # Regex Explanation:
                # (?i)
                    # This inline flag makes the regex case-insensitive, so it will match "GP", "gp", "Gb", "gB", etc.
                # (?:gp|gb)
                    # This non-capturing group matches either "gp" or "gb".
                    # (The non-capturing group is used here since we only care about the number that follows.)
                # \D*
                    # Matches zero or more non-digit characters. This handles cases where there may be punctuation or no whitespace at all between the letters and the number.
                # (\d+)
                    # Captures one or more digits following the pattern.
                pattern = r"(?i)(?:gp|gb|6b|6p|g@p|@p|g2)\D*(\d+)"

                match = re.search(pattern, recognized_text)
                if match:
                    gp_value = match.group(1)
                    print("GP value found:", gp_value)
                    await message.channel.send(f"GP Value found: **{gp_value}**, Rank: **{determine_rank(int(gp_value))}**")
                    await update_member_rank(message, int(gp_value))
                else:
                    await message.channel.send("Could not find a GP value in the image.")

    # Continue processing other commands or events.
    await bot.process_commands(message)



async def update_member_rank(message: discord.Message, gp_value: int):

    member = message.author
    guild = message.guild

    # Determine which rank the GP value qualifies for.
    new_rank:RankUpGpRequirement = determine_rank(gp_value)

    if new_rank is None:
        await  message.channel.send("GP value is too low for any rank.")
        return

    new_role_id = RANK_ROLE_IDS.get(new_rank)
    if new_role_id is None:
        await  message.channel.send("Role for the determined rank was not found. Should never happen ask mod for help")
        return

    new_role = guild.get_role(new_role_id)
    if new_role is None:
        await  message.channel.send("The role was not found in the guild.")
        return

    # Gather any current rank roles that the member has.
    current_rank_roles = [role for role in member.roles if role.id in RANK_ROLE_IDS.values()]

    # Determine if the member already has a higher rank.
    for role in current_rank_roles:
        current_rank = RankUpGpRequirement[role.name.upper()]
        # If the member already has a higher rank, abort.
        if current_rank > gp_value:
            await  message.channel.send(
                "You already have a higher rank role."
            )
            return

    # Remove any lower rank roles.
    for role in current_rank_roles:

        current_rank = RankUpGpRequirement[role.name.upper()]

        if current_rank < RankUpGpRequirement[new_rank]:
            print(f"current_rank: {current_rank}, gp_value: {gp_value}")
            print(f"Removing role {role.name} from {member.display_name}")
            await member.remove_roles(role, reason="Upgrading rank role")

    # Finally, add the new role if not already present.
    if new_role not in member.roles:
        await member.add_roles(new_role, reason="Updating rank role")
        await  message.channel.send(
            f"Your rank role has been updated to **{new_role.name}**."
        )
    else:
        await  message.channel.send(
            "Your rank role is already up-to-date."
        )


if __name__ == "__main__":
    bot.run(config.bot_token)
