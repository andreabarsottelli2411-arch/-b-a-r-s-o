import discord
from discord.ext import commands
from datetime import timedelta
import re
from datetime import datetime, timezone


# =========================
# CONFIGURATION
# =========================

import os

TOKEN = os.getenv("TOKEN")

# Channels where self-promo links are forbidden
MONITORED_CHANNELS = {
    1469657626785615943,
    1528513613562642512,
    1469436868998332480
}

# Mod log channel
LOG_CHANNEL_ID = 1533593701312495756

# Self promo channel
SELF_PROMO_CHANNEL_ID = 1469661038055002112

# Timeout duration
TIMEOUT_DURATION = timedelta(days=7)


# =========================
# BOT SETUP
# =========================

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


# =========================
# LINK DETECTION
# =========================

LINK_REGEX = re.compile(
    r"""
    (
        https?://\S+
        |
        www\.\S+
        |
        \b[a-zA-Z0-9-]+\.(com|net|org|gg|tv|io|co|me|xyz)\b\S*
    )
    """,
    re.VERBOSE | re.IGNORECASE
)


# Allowed websites
ALLOWED_DOMAINS = [
    "medal.tv",
    "tenor.com"
]


def contains_forbidden_link(message):
    """
    Returns True if message contains a link
    except allowed websites.
    """

    links = LINK_REGEX.findall(message.content)

    if not links:
        return False

    content = message.content.lower()

    for allowed in ALLOWED_DOMAINS:
        if allowed in content:
            return False

    return True


# =========================
# READY EVENT
# =========================

@bot.event
async def on_ready():
    print("--------------------------------")
    print(f"Logged in as {bot.user}")
    print(f"Bot ID: {bot.user.id}")
    print("--------------------------------")


# =========================
# MESSAGE CHECK
# =========================

@bot.event
async def on_message(message):

    # Ignore bots
    if message.author.bot:
        return


    # Only check selected channels
    if message.channel.id in MONITORED_CHANNELS:


        # Ignore administrators
        if message.author.guild_permissions.administrator:
            return


        # Check links
        if contains_forbidden_link(message):

            try:

                # Save message content before deleting
                deleted_content = message.content


                # Delete message
                await message.delete()


                # Timeout user
                await message.author.timeout(
                    TIMEOUT_DURATION,
                    reason="Self-promotion/link posted outside self-promo channel"
                )


                # Send log
                log_channel = bot.get_channel(LOG_CHANNEL_ID)

                if log_channel:

                    embed = discord.Embed(
                        title="🔨 User Timed Out",
                        color=discord.Color.red(),
                        timestamp=datetime.now(timezone.utc)
                    )

                    embed.add_field(
                        name="User",
                        value=f"{message.author.mention}\n`{message.author.id}`",
                        inline=False
                    )

                    embed.add_field(
                        name="Channel",
                        value=message.channel.mention,
                        inline=False
                    )

                    embed.add_field(
                        name="Reason",
                        value=(
                            "Posted self-promotion outside the self-promo channel.\n"
                            f"Timeout: **7 days**\n"
                            f"Please use <#{SELF_PROMO_CHANNEL_ID}> instead."
                        ),
                        inline=False
                    )

                    embed.add_field(
                        name="Deleted Message",
                        value=(
                            deleted_content[:1024]
                            if deleted_content
                            else "No text content"
                        ),
                        inline=False
                    )


                    embed.set_footer(
                        text="Self Promo Protection"
                    )

                    await log_channel.send(
                        embed=embed
                    )


            except discord.Forbidden:

                print(
                    f"Could not moderate {message.author}. "
                    "Check bot permissions/role position."
                )


            except Exception as e:

                print(
                    f"Error: {e}"
                )


    await bot.process_commands(message)



# =========================
# START BOT
# =========================

bot.run(TOKEN)