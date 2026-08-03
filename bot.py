import discord
from discord.ext import commands
from datetime import timedelta, datetime, timezone
import os
import re
import time


# =====================================================
# CONFIGURATION
# =====================================================

TOKEN = os.getenv("TOKEN")

PREFIX = ","


# Server ID
SERVER_ID = 1469436868239298624


# Channels

MONITORED_CHANNELS = {
    1469657626785615943,
    1528513613562642512,
    1469436868998332480
}

LOG_CHANNEL_ID = 1533593701312495756

SELF_PROMO_CHANNEL_ID = 1469661038055002112



# =====================================================
# WARNING SYSTEM
# =====================================================


WARNING_ROLES = {

    1: 1533657085538209822,
    2: 1533657126629539993,
    3: 1533657139975819274

}



WARNING_PUNISHMENTS = {

    1: "1 hour timeout",
    2: "3 day timeout",
    3: "7 day ban"

}



# =====================================================
# LINK SETTINGS
# =====================================================


# Default allowed links

WHITELIST = {

    "medal.tv",
    "tenor.com"

}



# Words you add with ,blacklist add

BLACKLIST = set()



# =====================================================
# BOT SETUP
# =====================================================


intents = discord.Intents.default()

intents.message_content = True
intents.members = True



bot = commands.Bot(

    command_prefix=PREFIX,

    intents=intents,

    help_command=None

)



# Bot uptime

START_TIME = time.time()



# =====================================================
# REGEX
# =====================================================


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



# =====================================================
# BASIC HELPERS
# =====================================================


def get_log_channel():

    return bot.get_channel(LOG_CHANNEL_ID)



def is_admin(member):

    return member.guild_permissions.administrator



def get_time():

    return datetime.now(
        timezone.utc
    )



# =====================================================
# READY EVENT
# =====================================================


@bot.event

async def on_ready():

    print("==========================")
    print(f"Logged in as {bot.user}")
    print("Bot Version: 3.0")
    print("==========================")


    log = get_log_channel()


    if log:

        embed = discord.Embed(

            title="🟢 Bot Online",

            description="Self Promo Protection v3.0 is active.",

            color=discord.Color.green(),

            timestamp=get_time()

        )


        embed.add_field(

            name="Latency",

            value=f"{round(bot.latency * 1000)}ms"

        )


        embed.add_field(

            name="Servers",

            value=str(len(bot.guilds))

        )


        await log.send(
            embed=embed
        )

# =====================================================
# WARNING SYSTEM FUNCTIONS
# =====================================================


async def get_warning_level(member):

    """
    Checks which warning role the user currently has.
    Returns 0, 1, 2 or 3.
    """

    for level, role_id in WARNING_ROLES.items():

        role = member.guild.get_role(role_id)

        if role and role in member.roles:

            return level


    return 0





async def remove_warning_roles(member):

    """
    Removes old warning roles before applying the new one.
    """

    roles = []


    for role_id in WARNING_ROLES.values():

        role = member.guild.get_role(role_id)


        if role and role in member.roles:

            roles.append(role)



    if roles:

        await member.remove_roles(*roles)





async def give_warning_role(member, level):

    """
    Gives the correct warning role.
    """

    await remove_warning_roles(member)


    role = member.guild.get_role(
        WARNING_ROLES[level]
    )


    if role:

        await member.add_roles(role)





async def send_log(title, description, color=discord.Color.red()):

    """
    Sends moderation logs.
    """

    channel = get_log_channel()


    if channel:


        embed = discord.Embed(

            title=title,

            description=description,

            color=color,

            timestamp=get_time()

        )


        await channel.send(
            embed=embed
        )





# =====================================================
# MAIN WARNING ENGINE
# =====================================================


async def issue_warning(
    member,
    reason,
    moderator=None,
    automatic=False
):

    """
    Universal punishment system.

    Used by:
    - AutoMod
    - Commands
    """



    current_warning = await get_warning_level(member)


    next_warning = current_warning + 1



    # Prevent going above 3

    if next_warning > 3:

        next_warning = 3




    try:


        await give_warning_role(
            member,
            next_warning
        )



        # =========================
        # WARNING 1
        # =========================


        if next_warning == 1:


            await member.timeout(

                timedelta(hours=1),

                reason=reason

            )


            message = f"""

⚠️ {member.mention}

You have received your **first warning**.

**Reason:**
{reason}

**Punishment:**
1 hour timeout.

Please follow the server rules.

"""



        # =========================
        # WARNING 2
        # =========================


        elif next_warning == 2:


            await member.timeout(

                timedelta(days=3),

                reason=reason

            )


            message = f"""

⚠️ {member.mention}

You have received your **second warning**.

**Reason:**
{reason}

**Punishment:**
3 day timeout.

⚠️ Your next warning will result in a **7 day ban**.

"""



        # =========================
        # WARNING 3
        # =========================


        else:


            message = f"""

🔨 {member.mention}

You have reached your **third warning**.

**Reason:**
{reason}

**Punishment:**
7 day ban.

"""



            await member.ban(

                reason="Third warning reached"

            )




        return message



    except Exception as e:


        return f"""

❌ Failed to punish {member.mention}.

Error:

`{e}`

Check bot permissions and role hierarchy.

"""





# =====================================================
# TEXT CHECKING FUNCTIONS
# =====================================================


def contains_link(content):

    return bool(
        LINK_REGEX.search(content)
    )





def contains_blacklisted_word(content):


    content = content.lower()



    for word in BLACKLIST:


        pattern = r"\b" + re.escape(word) + r"\b"



        if re.search(pattern, content):

            return True



    return False

# =====================================================
# AUTOMOD MESSAGE SYSTEM
# =====================================================


@bot.event
async def on_message(message):


    # Ignore bots

    if message.author.bot:

        return



    # Ignore DMs

    if not message.guild:

        return




    # =================================================
    # BLACKLIST CHECK
    # =================================================


    if contains_blacklisted_word(
        message.content
    ):


        try:


            await message.delete()



            punishment_message = await issue_warning(

                message.author,

                "Using a blacklisted word.",

                automatic=True

            )



            await message.channel.send(

                punishment_message

            )



            await send_log(

                "🚫 Blacklisted Word Detected",

                f"""

User:

{message.author.mention}


Channel:

{message.channel.mention}


Reason:

Blacklisted word


Deleted Message:

{message.content[:1000]}

"""

            )



        except Exception as e:


            await message.channel.send(

                f"❌ Moderation error:\n`{e}`"

            )



        return





    # =================================================
    # LINK / SELF PROMO CHECK
    # =================================================


    if message.channel.id in MONITORED_CHANNELS:


        # Admins bypass

        if not is_admin(message.author):


            if contains_link(
                message.content
            ):


                # Check whitelist


                allowed = False



                for website in WHITELIST:


                    if website.lower() in message.content.lower():

                        allowed = True



                if not allowed:


                    try:


                        deleted_content = message.content



                        await message.delete()



                        punishment_message = await issue_warning(

                            message.author,

                            "Posting self promotion links outside the self-promo channel.",

                            automatic=True

                        )



                        await message.channel.send(

                            punishment_message

                        )



                        await send_log(

                            "🔗 Self Promotion Warning",

                            f"""

User:

{message.author.mention}


Channel:

{message.channel.mention}


Reason:

Self promotion link


Deleted Message:

{deleted_content[:1000]}

"""

                        )



                    except Exception as e:


                        await message.channel.send(

                            f"❌ Moderation error:\n`{e}`"

                        )



                    return





    # Allow commands to work

    await bot.process_commands(message)

# =====================================================
# ADMIN CHECK DECORATOR
# =====================================================


def admin_only():

    async def predicate(ctx):

        if ctx.author.guild_permissions.administrator:

            return True


        await ctx.send(
            "❌ You need Administrator permission to use this command."
        )


        return False


    return commands.check(predicate)




# =====================================================
# HELP COMMAND
# =====================================================


@bot.command(name="help")
@admin_only()
async def help_command(ctx):


    embed = discord.Embed(

        title="🤖 Self Promo Bot Commands",

        color=discord.Color.blue()

    )


    embed.description = """

`,help`
→ Shows this menu.


`,warn @user <reason>`
→ Manually warn a user.


`,warnings @user`
→ Shows warning level.


`,clearwarnings @user`
→ Removes warning roles.


`,unmute @user`
→ Removes timeout.


`,whitelist add <website>`
→ Allow a website.


`,whitelist remove <website>`
→ Remove a website.


`,whitelist list`
→ Show allowed websites.


`,blacklist add <word>`
→ Block a word.


`,blacklist remove <word>`
→ Remove blocked word.


`,blacklist list`
→ Show blocked words.


`,botstatus`
→ Show bot information.

"""


    await ctx.send(
        embed=embed
    )




# =====================================================
# WARN COMMAND
# =====================================================


@bot.command()
@admin_only()
async def warn(
    ctx,
    member: discord.Member,
    *,
    reason
):


    result = await issue_warning(

        member,

        reason,

        moderator=ctx.author

    )


    await ctx.send(
        result
    )





# =====================================================
# WARNINGS COMMAND
# =====================================================


@bot.command()
@admin_only()
async def warnings(
    ctx,
    member: discord.Member
):


    level = await get_warning_level(
        member
    )


    await ctx.send(

        f"⚠️ {member.mention} is currently at warning level **{level}/3**."

    )





# =====================================================
# CLEAR WARNINGS
# =====================================================


@bot.command()
@admin_only()
async def clearwarnings(
    ctx,
    member: discord.Member
):


    await remove_warning_roles(
        member
    )


    await ctx.send(

        f"✅ Cleared warnings for {member.mention}."

    )





# =====================================================
# UNMUTE
# =====================================================


@bot.command()
@admin_only()
async def unmute(
    ctx,
    member: discord.Member
):


    await member.timeout(

        None,

        reason=f"Removed by {ctx.author}"

    )


    await ctx.send(

        f"✅ Removed timeout from {member.mention}."

    )





# =====================================================
# WHITELIST COMMANDS
# =====================================================


@bot.group(
    invoke_without_command=True
)
@admin_only()
async def whitelist(ctx):


    await ctx.send(

        "Use:\n`,whitelist add/remove/list`"

    )





@whitelist.command()
async def add(
    ctx,
    website
):


    WHITELIST.add(

        website.lower()

    )


    await ctx.send(

        f"✅ Added `{website}` to whitelist."

    )





@whitelist.command()
async def remove(
    ctx,
    website
):


    WHITELIST.discard(

        website.lower()

    )


    await ctx.send(

        f"✅ Removed `{website}` from whitelist."

    )





@whitelist.command()
async def list(ctx):


    await ctx.send(

        "✅ Allowed websites:\n" +

        "\n".join(WHITELIST)

    )





# =====================================================
# BLACKLIST COMMANDS
# =====================================================


@bot.group(
    invoke_without_command=True
)
@admin_only()
async def blacklist(ctx):


    await ctx.send(

        "Use:\n`,blacklist add/remove/list`"

    )





@blacklist.command()
async def add(
    ctx,
    word
):


    BLACKLIST.add(

        word.lower()

    )


    await ctx.send(

        f"🚫 Added `{word}` to blacklist."

    )





@blacklist.command()
async def remove(
    ctx,
    word
):


    BLACKLIST.discard(

        word.lower()

    )


    await ctx.send(

        f"✅ Removed `{word}` from blacklist."

    )





@blacklist.command()
async def list(ctx):


    if not BLACKLIST:

        await ctx.send(

            "Blacklist is empty."

        )

        return



    await ctx.send(

        "🚫 Blacklisted words:\n" +

        "\n".join(BLACKLIST)

    )





# =====================================================
# BOT STATUS
# =====================================================


@bot.command()
@admin_only()
async def botstatus(ctx):


    uptime = int(

        time.time() - START_TIME

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

        value=str(len(bot.guilds))

    )


    await ctx.send(

        embed=embed

    )





# =====================================================
# ERROR HANDLING
# =====================================================


@bot.event
async def on_command_error(ctx, error):


    if isinstance(
        error,
        commands.MissingRequiredArgument
    ):


        await ctx.send(

            "❌ Missing argument. Use `,help`."

        )



    elif isinstance(
        error,
        commands.MemberNotFound
    ):


        await ctx.send(

            "❌ User not found."

        )



    else:


        await ctx.send(

            f"❌ Command failed:\n`{error}`"

        )





# =====================================================
# START BOT
# =====================================================


bot.run(TOKEN)