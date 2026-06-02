import discord
from discord.ext import commands, tasks
import datetime
import pytz
import os
import logging

# =========================
# LOGGING — ดู log ใน Railway
# =========================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%d/%m/%Y %H:%M:%S"
)
log = logging.getLogger("BOT_AVIDA")

# =========================
# INTENTS
# =========================

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# =========================
# CONFIG
# =========================

BKK_TZ = pytz.timezone("Asia/Bangkok")

announcement_channel_id = None
announce_hour = None
announce_minute = None
announce_message = None
last_sent_date = None

# =========================
# READY
# =========================

@bot.event
async def on_ready():
    log.info(f"🤖 {bot.user} ออนไลน์แล้ว!")
    log.info(f"📋 Servers: {len(bot.guilds)}")
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="!helpme"
        )
    )
    if not daily_announcement.is_running():
        daily_announcement.start()
        log.info("✅ Daily announcement loop started")

# =========================
# DAILY ANNOUNCEMENT LOOP
# =========================

@tasks.loop(seconds=10)
async def daily_announcement():
    global last_sent_date

    if None in (announcement_channel_id, announce_hour, announce_minute, announce_message):
        return

    now = datetime.datetime.now(BKK_TZ)

    if now.hour == announce_hour and now.minute == announce_minute:
        today = now.date()
        if last_sent_date == today:
            return

        try:
            channel = bot.get_channel(announcement_channel_id) or \
                      await bot.fetch_channel(announcement_channel_id)
            await channel.send(announce_message)
            last_sent_date = today
            log.info(f"📢 Auto-announce sent at {now.strftime('%H:%M:%S')}")
        except discord.NotFound:
            log.error("❌ ไม่พบ channel ที่ตั้งไว้")
        except discord.Forbidden:
            log.error("❌ บอทไม่มีสิทธิ์ส่งข้อความใน channel นั้น")
        except Exception as e:
            log.error(f"❌ Error: {e}")

@daily_announcement.before_loop
async def before_loop():
    await bot.wait_until_ready()

# =========================
# KICK
# =========================

@bot.command()
@commands.has_permissions(administrator=True)
async def kick(ctx, member: discord.Member, *, reason="ไม่ได้ระบุเหตุผล"):
    if member == ctx.author:
        await ctx.send("❌ คุณไม่สามารถเตะตัวเองได้")
        return

    if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
        await ctx.send("❌ คุณไม่มีสิทธิ์เตะคนที่มี role เท่ากันหรือสูงกว่า")
        return

    try:
        await member.send(
            f"⚠️ คุณถูกเตะออกจาก **{ctx.guild.name}**\n"
            f"📝 เหตุผล: {reason}"
        )
    except discord.Forbidden:
        pass

    await member.kick(reason=reason)
    log.info(f"👢 Kicked {member} by {ctx.author} | Reason: {reason}")

    embed = discord.Embed(title="👢 เตะสมาชิก", color=discord.Color.orange())
    embed.add_field(name="สมาชิก", value=f"{member.mention} ({member})", inline=False)
    embed.add_field(name="เหตุผล", value=reason, inline=False)
    embed.add_field(name="ดำเนินการโดย", value=ctx.author.mention, inline=False)
    embed.set_footer(text=datetime.datetime.now(BKK_TZ).strftime("%d/%m/%Y %H:%M"))
    await ctx.send(embed=embed)

# =========================
# SAY
# =========================

@bot.command()
@commands.has_permissions(administrator=True)
async def say(ctx, *, message):
    try:
        await ctx.message.delete()
    except discord.Forbidden:
        pass
    await ctx.send(message)

# =========================
# SAYTO
# =========================

@bot.command()
@commands.has_permissions(administrator=True)
async def sayto(ctx, channel: discord.TextChannel, *, message):
    try:
        await ctx.message.delete()
    except discord.Forbidden:
        pass
    try:
        await channel.send(message)
        await ctx.send(f"✅ ส่งข้อความไปที่ {channel.mention} แล้ว", delete_after=5)
    except discord.Forbidden:
        await ctx.send(f"❌ บอทไม่มีสิทธิ์ส่งข้อความใน {channel.mention}")

# =========================
# ANNOUNCE
# =========================

@bot.command()
@commands.has_permissions(administrator=True)
async def announce(ctx, time_text: str, *, message: str):
    global announce_hour, announce_minute, announce_message

    try:
        parts = time_text.split(":")
        if len(parts) != 2:
            raise ValueError

        hour, minute = int(parts[0]), int(parts[1])

        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            await ctx.send("❌ เวลาไม่ถูกต้อง เช่น `08:00` หรือ `20:30`")
            return

        announce_hour = hour
        announce_minute = minute
        announce_message = message

        embed = discord.Embed(title="✅ ตั้งประกาศอัตโนมัติสำเร็จ", color=discord.Color.green())
        embed.add_field(name="⏰ เวลา", value=f"{hour:02d}:{minute:02d} (เวลาไทย)", inline=False)
        embed.add_field(name="📝 ข้อความ", value=message, inline=False)
        ch = f"<#{announcement_channel_id}>" if announcement_channel_id else "⚠️ ยังไม่ได้ตั้ง (ใช้ !setchannel)"
        embed.add_field(name="📢 ห้องที่จะส่ง", value=ch, inline=False)
        await ctx.send(embed=embed)

    except ValueError:
        await ctx.send("❌ ใช้แบบนี้: `!announce 17:40 ข้อความ`")

# =========================
# CANCELANNOUNCE
# =========================

@bot.command()
@commands.has_permissions(administrator=True)
async def cancelannounce(ctx):
    global announce_hour, announce_minute, announce_message
    announce_hour = None
    announce_minute = None
    announce_message = None
    await ctx.send("✅ ยกเลิกประกาศอัตโนมัติแล้ว")

# =========================
# SETCHANNEL
# =========================

@bot.command()
@commands.has_permissions(administrator=True)
async def setchannel(ctx):
    global announcement_channel_id
    announcement_channel_id = ctx.channel.id
    await ctx.send(f"✅ ตั้ง {ctx.channel.mention} เป็นห้องประกาศอัตโนมัติแล้ว")

# =========================
# STATUS
# =========================

@bot.command()
@commands.has_permissions(administrator=True)
async def status(ctx):
    channel_text = f"<#{announcement_channel_id}>" if announcement_channel_id else "ยังไม่ได้ตั้ง"
    time_text = f"{announce_hour:02d}:{announce_minute:02d}" if announce_hour is not None else "ยังไม่ได้ตั้ง"
    msg_text = announce_message or "ยังไม่ได้ตั้ง"
    now = datetime.datetime.now(BKK_TZ).strftime("%d/%m/%Y %H:%M:%S")

    embed = discord.Embed(title="⚙️ สถานะ BOT AVIDA", color=discord.Color.purple())
    embed.add_field(name="📢 ห้องประกาศ", value=channel_text, inline=False)
    embed.add_field(name="⏰ เวลาประกาศ", value=time_text, inline=False)
    embed.add_field(name="📝 ข้อความประกาศ", value=msg_text, inline=False)
    embed.add_field(name="🕐 เวลาปัจจุบัน (ไทย)", value=now, inline=False)
    embed.set_footer(text="BOT AVIDA")
    await ctx.send(embed=embed)

# =========================
# PING
# =========================

@bot.command()
async def ping(ctx):
    await ctx.send(f"🏓 Pong! `{round(bot.latency * 1000)}ms`")

# =========================
# HELPME
# =========================

@bot.command()
async def helpme(ctx):
    embed = discord.Embed(
        title="🤖 BOT AVIDA — คำสั่งทั้งหมด",
        description="⚠️ คำสั่งส่วนใหญ่ต้องการสิทธิ์ **ผู้ดูแล (Administrator)**",
        color=discord.Color.purple()
    )
    embed.add_field(
        name="📢 ส่งข้อความในนามบอท",
        value="`!say <ข้อความ>` — บอทพูดในห้องนี้\n`!sayto <#ห้อง> <ข้อความ>` — บอทพูดในห้องที่กำหนด",
        inline=False
    )
    embed.add_field(
        name="⏰ ประกาศอัตโนมัติทุกวัน",
        value="`!setchannel` — ตั้งห้องนี้เป็นห้องประกาศ\n`!announce <HH:MM> <ข้อความ>` — ตั้งเวลาประกาศ\n`!cancelannounce` — ยกเลิกประกาศ",
        inline=False
    )
    embed.add_field(
        name="👢 จัดการสมาชิก",
        value="`!kick <@สมาชิก> [เหตุผล]` — เตะสมาชิกออก",
        inline=False
    )
    embed.add_field(
        name="🔧 ทั่วไป",
        value="`!status` — ดูการตั้งค่า\n`!ping` — เช็คบอท\n`!helpme` — แสดงคำสั่ง",
        inline=False
    )
    embed.set_footer(text="BOT AVIDA")
    await ctx.send(embed=embed)

# =========================
# ERROR HANDLER
# =========================

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ คุณต้องมีสิทธิ์ **ผู้ดูแล (Administrator)** ถึงจะใช้คำสั่งนี้ได้")
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send("❌ ไม่พบสมาชิกที่ระบุ ลองแท็ก @ชื่อ ให้ถูกต้อง")
    elif isinstance(error, commands.ChannelNotFound):
        await ctx.send("❌ ไม่พบห้องที่ระบุ ลองแท็ก #ชื่อห้อง ให้ถูกต้อง")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ ใส่ข้อมูลไม่ครบ พิมพ์ `!helpme` เพื่อดูวิธีใช้")
    elif isinstance(error, commands.CommandNotFound):
        return
    else:
        log.error(f"Unhandled error: {error}")

# =========================
# RUN — ดึง Token จาก Environment Variable
# =========================

TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise ValueError("❌ ไม่พบ DISCORD_TOKEN ใน Environment Variables")

bot.run(TOKEN, log_handler=None)
