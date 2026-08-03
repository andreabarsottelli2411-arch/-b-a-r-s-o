import discord
from discord.ext import commands
from datetime import timedelta, datetime, timezone
import re
import os
import time


# =========================
# CONFIGURATION
# =========================

TOKEN = os.getenv("TOKEN")

PREFIX = ","

SERVER_ID = 1469436868239298624

# Channels
MONITORED_CHANNELS = {
    1469657626785615943,
    1528513613562642512,
    1469436868998332480
}

LOG_CHANNEL_ID = 1533593701312495756
SELF_PROMO_CHANNEL_ID = 1469661038055002112


# Warning roles

WARNING_ROLES = {
    1: 1533657085538209822,
    2: 1533657126629539993,
    3: 1533657139975819274
}


# Allowed links

WHITELIST = {
    "medal.tv",
    "tenor.com"
}


# =========================
# BOT SETUP
# =========================

intents = discord.Intents.default()

intents.message_content = True
intents.members = True


bot = commands.Bot(
    command_prefix=PREFIX,
    intents=intents,
    help_command=None
)


start_time = time.time()


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
    \b[a-zA-Z0-9-]+\.(com|net|org|gg|tv|io|co|me|xyz)\S*
    )
    """,
    re.VERBOSE | re.IGNORECASE
)


def contains_bad_link(content):

    links = LINK_REGEX.findall(content)

    if not links:
        return False

    content = content.lower()


    for allowed in WHITELIST:
        if allowed in content:
            return False


    return True



# =========================
# READY
# =========================

@bot.event
async def on_ready():

    print("-------------------------")
    print(f"Logged in as {bot.user}")
    print("Version 2.0 Online")
    print("-------------------------")


    channel = bot.get_channel(LOG_CHANNEL_ID)

    if channel:

        embed = discord.Embed(
            title="🟢 Bot Online",
            description="Self Promo Protection is running.",
            color=discord.Color.green(),
            timestamp=datetime.now(timezone.utc)
        )


        embed.add_field(
            name="Latency",
            value=f"{round(bot.latency * 1000)}ms"
        )


        embed.add_field(
            name="Servers",
            value=str(len(bot.guilds))
        )


        await channel.send(embed=embed)



# =========================
# ADMIN CHECK
# =========================

def is_admin():

    async def predicate(ctx):

        if ctx.author.guild_permissions.administrator:
            return True

        await ctx.send(
            "❌ You need Administrator permission to use this command."
        )

        return False


    return commands.check(predicate)



# =========================
# LOGGING FUNCTION
# =========================

async def send_log(
    title,
    description,
    color=discord.Color.red()
):

    channel = bot.get_channel(LOG_CHANNEL_ID)

    if channel:

        embed = discord.Embed(
            title=title,
            description=description,
            color=color,
            timestamp=datetime.now(timezone.utc)
        )

        await channel.send(embed=embed)



# =========================
# MESSAGE PROTECTION
# =========================

@bot.event
async def on_message(message):

    if message.author.bot:
        return


    if message.channel.id in MONITORED_CHANNELS:


        if not message.author.guild_permissions.administrator:


            if contains_bad_link(message.content):

                try:

                    content = message.content


                    await message.delete()


                    await message.author.timeout(
                        timedelta(days=7),
                        reason="Self promotion link"
                    )


                    await send_log(
                        "🔨 Automatic Timeout",
                        f"""
User:
{message.author.mention}

Channel:
{message.channel.mention}

Reason:
Self promotion/link outside self-promo

Punishment:
7 day timeout

Deleted message:
{content[:1000]}
"""
                    )


                except Exception as e:

                    print(e)


    await bot.process_commands(message)

# =========================
# WARNING SYSTEM HELPERS
# =========================

async def get_warning_level(member):

    for level, role_id in WARNING_ROLES.items():

        role = member.guild.get_role(role_id)

        if role in member.roles:
            return level

    return 0



async def remove_warning_roles(member):

    roles_to_remove = []

    for role_id in WARNING_ROLES.values():

        role = member.guild.get_role(role_id)

        if role and role in member.roles:
            roles_to_remove.append(role)


    if roles_to_remove:
        await member.remove_roles(*roles_to_remove)



async def apply_warning(member, level):

    await remove_warning_roles(member)

    role = member.guild.get_role(
        WARNING_ROLES[level]
    )

    if role:
        await member.add_roles(role)



# =========================
# HELP COMMAND
# =========================

@bot.command(name="help")
@is_admin()
async def help_command(ctx):

    embed = discord.Embed(
        title="🤖 Self Promo Bot Commands",
        color=discord.Color.blue()
    )

    embed.description = """

`,warn @user <reason>`
→ Give a warning and punishment.

`,warnings @user`
→ Check warning level.

`,clearwarnings @user`
→ Remove warning roles.

`,unmute @user`
→ Remove timeout.

`,whitelist add <domain>`
→ Allow a website.

`,whitelist remove <domain>`
→ Remove a website.

`,whitelist list`
→ Show allowed websites.

`,botstatus`
→ Show bot information.

"""

    await ctx.send(embed=embed)



# =========================
# WARN COMMAND
# =========================

@bot.command()
@is_admin()
async def warn(ctx, member: discord.Member, *, reason):

    try:

        current = await get_warning_level(member)

        new_warning = current + 1


        if new_warning >= 3:


            await apply_warning(
                member,
                3
            )


            await ctx.send(
                f"""
🔨 {member.mention}

You have received your third warning.

Reason:
{reason}

Punishment:
**7 day ban**
"""
            )


            await send_log(
                "🔨 Third Warning - Ban",
                f"""
User:
{member.mention}

Moderator:
{ctx.author.mention}

Reason:
{reason}

Punishment:
7 day ban
"""
            )


            await member.ban(
                reason="Third warning reached",
                delete_message_days=0
            )



        elif new_warning == 2:


            await apply_warning(
                member,
                2
            )


            await member.timeout(
                timedelta(days=3),
                reason=reason
            )


            await ctx.send(
                f"""
⚠️ {member.mention}

You have received your second warning.

Reason:
{reason}

Punishment:
**3 day timeout**

⚠️ Your next warning will result in a **7 day ban**.
"""
            )



        else:


            await apply_warning(
                member,
                1
            )


            await member.timeout(
                timedelta(hours=1),
                reason=reason
            )


            await ctx.send(
                f"""
⚠️ {member.mention}

You have received your first warning.

Reason:
{reason}

Punishment:
**1 hour timeout**
"""
            )


        await send_log(
            "⚠️ Warning Issued",
            f"""
User:
{member.mention}

Moderator:
{ctx.author.mention}

Warning:
{new_warning}/3

Reason:
{reason}
"""
        )



    except Exception as e:

        await ctx.send(
            f"❌ Failed to warn user.\nReason:\n`{e}`"
        )



# =========================
# WARNINGS COMMAND
# =========================

@bot.command()
@is_admin()
async def warnings(ctx, member: discord.Member):

    level = await get_warning_level(member)


    await ctx.send(
        f"⚠️ {member.mention} currently has warning level **{level}/3**."
    )



# =========================
# CLEAR WARNINGS
# =========================

@bot.command()
@is_admin()
async def clearwarnings(ctx, member: discord.Member):

    await remove_warning_roles(member)


    await ctx.send(
        f"✅ Cleared all warnings for {member.mention}."
    )



# =========================
# UNMUTE
# =========================

@bot.command()
@is_admin()
async def unmute(ctx, member: discord.Member):

    await member.timeout(
        None,
        reason=f"Removed by {ctx.author}"
    )


    await ctx.send(
        f"✅ Removed timeout from {member.mention}."
    )



# =========================
# WHITELIST COMMAND
# =========================

@bot.group(
    invoke_without_command=True
)
@is_admin()
async def whitelist(ctx):

    await ctx.send(
        "Use:\n`,whitelist add/remove/list`"
    )



@whitelist.command()
async def add(ctx, domain):

    WHITELIST.add(
        domain.lower()
    )


    await ctx.send(
        f"✅ Added `{domain}` to whitelist."
    )



@whitelist.command()
async def remove(ctx, domain):

    WHITELIST.discard(
        domain.lower()
    )


    await ctx.send(
        f"✅ Removed `{domain}` from whitelist."
    )



@whitelist.command()
async def list(ctx):

    await ctx.send(
        "✅ Allowed websites:\n" +
        "\n".join(WHITELIST)
    )



# =========================
# BOT STATUS
# =========================

@bot.command()
@is_admin()
async def botstatus(ctx):

    uptime = int(
        time.time() - start_time
    )

    hours = uptime // 3600
    minutes = (uptime % 3600) // 60


    embed = discord.Embed(
        title="🤖 Bot Status",
        color=discord.Color.green()
    )


    embed.add_field(
        name="Latency",
        value=f"{round(bot.latency * 1000)}ms"
    )


    embed.add_field(
        name="Uptime",
        value=f"{hours}h {minutes}m"
    )


    embed.add_field(
        name="Servers",
        value=len(bot.guilds)
    )


    await ctx.send(embed=embed)



# =========================
# COMMAND ERROR HANDLER
# =========================

@bot.event
async def on_command_error(ctx, error):

    if isinstance(error, commands.MissingPermissions):

        await ctx.send(
            "❌ You do not have permission to use this command."
        )


    elif isinstance(error, commands.MissingRequiredArgument):

        await ctx.send(
            "❌ Missing argument. Check `,help`."
        )


    else:

        await ctx.send(
            f"❌ Command failed:\n`{error}`"
        )