import os
import random
import asyncio
import sqlite3
from datetime import datetime, timezone

import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
SPAWN_INTERVAL_MINUTES = int(os.getenv("SPAWN_INTERVAL_MINUTES", "30"))

# Lista inicial de Digimons clássicos. Expanda este arquivo/lista conforme desejar.
DIGIMONS = [
    {"name": "Agumon", "stage": "Rookie", "hint": "Um pequeno Digimon dinossauro que cospe fogo."},
    {"name": "Gabumon", "stage": "Rookie", "hint": "Usa uma pele listrada que lembra a de um lobo."},
    {"name": "Patamon", "stage": "Rookie", "hint": "Um pequeno Digimon alado com orelhas enormes."},
    {"name": "Biyomon", "stage": "Rookie", "hint": "Um Digimon pássaro rosa."},
    {"name": "Tentomon", "stage": "Rookie", "hint": "Um Digimon inseto com carapaça vermelha."},
    {"name": "Palmon", "stage": "Rookie", "hint": "Um Digimon planta com uma flor na cabeça."},
    {"name": "Gomamon", "stage": "Rookie", "hint": "Um Digimon aquático com pelos brancos."},
    {"name": "Gatomon", "stage": "Champion", "hint": "Um Digimon felino que usa luvas especiais."},
    {"name": "Veemon", "stage": "Rookie", "hint": "Um pequeno Digimon azul, parceiro de Davis."},
    {"name": "Wormmon", "stage": "Rookie", "hint": "Um Digimon inseto verde, parceiro de Ken."},
    {"name": "Greymon", "stage": "Champion", "hint": "Uma evolução de Agumon com aparência de dinossauro."},
    {"name": "Garurumon", "stage": "Champion", "hint": "Um lobo azul que corre em alta velocidade."},
    {"name": "Angemon", "stage": "Champion", "hint": "Um Digimon angelical com seis asas."},
    {"name": "Angewomon", "stage": "Ultimate", "hint": "Uma guerreira angelical de armadura branca."},
    {"name": "Devimon", "stage": "Champion", "hint": "Um Digimon sombrio com asas de morcego."},
    {"name": "Kabuterimon", "stage": "Champion", "hint": "Um grande inseto azul com um chifre."},
    {"name": "Birdramon", "stage": "Champion", "hint": "Uma ave gigante feita de fogo."},
    {"name": "Togemon", "stage": "Champion", "hint": "Um Digimon cacto que usa luvas de boxe."},
    {"name": "Ikkakumon", "stage": "Champion", "hint": "Um Digimon marinho branco com um chifre."},
    {"name": "MetalGreymon", "stage": "Ultimate", "hint": "Uma poderosa forma ciborgue de Greymon."},
    {"name": "WereGarurumon", "stage": "Ultimate", "hint": "Uma forma humanoide e lutadora de Garurumon."},
    {"name": "WarGreymon", "stage": "Mega", "hint": "Um guerreiro dragão com armadura e Dramon Killers."},
    {"name": "MetalGarurumon", "stage": "Mega", "hint": "Um lobo mecânico equipado com armamentos."},
    {"name": "Omnimon", "stage": "Mega", "hint": "Uma fusão lendária de WarGreymon e MetalGarurumon."},
]

DB_PATH = "digworld.sqlite3"
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

active_spawns = {}  # channel_id -> Digimon dict


def db():
    return sqlite3.connect(DB_PATH)


def init_db():
    with db() as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                guild_id INTEGER PRIMARY KEY,
                channel_id INTEGER NOT NULL
            )
        """)
        con.execute("""
            CREATE TABLE IF NOT EXISTS catches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                guild_id INTEGER NOT NULL,
                digimon_name TEXT NOT NULL,
                stage TEXT NOT NULL,
                caught_at TEXT NOT NULL
            )
        """)


def normalize(value: str) -> str:
    return " ".join(value.casefold().strip().split())


def get_spawn_channel(guild_id):
    with db() as con:
        row = con.execute(
            "SELECT channel_id FROM settings WHERE guild_id = ?", (guild_id,)
        ).fetchone()
    return row[0] if row else None


def save_catch(user_id, guild_id, digimon):
    with db() as con:
        con.execute(
            """INSERT INTO catches
               (user_id, guild_id, digimon_name, stage, caught_at)
               VALUES (?, ?, ?, ?, ?)""",
            (user_id, guild_id, digimon["name"], digimon["stage"],
             datetime.now(timezone.utc).isoformat())
        )


def user_catches(user_id, guild_id):
    with db() as con:
        return con.execute(
            """SELECT digimon_name, stage, COUNT(*) FROM catches
               WHERE user_id = ? AND guild_id = ?
               GROUP BY digimon_name, stage
               ORDER BY digimon_name""",
            (user_id, guild_id)
        ).fetchall()


def spawn_embed(digimon):
    embed = discord.Embed(
        title="Um Digimon selvagem apareceu!",
        description=(
            "Uma silhueta misteriosa surgiu!\n\n"
            f"**Dica:** {digimon['hint']}\n\n"
            "Digite o nome do Digimon no chat para tentar capturá-lo."
        ),
        color=discord.Color.blurple()
    )
    embed.set_footer(text="DigiWorld • Quem será esse Digimon?")
    return embed


async def spawn_in_channel(channel):
    if channel.id in active_spawns:
        return
    digimon = random.choice(DIGIMONS)
    active_spawns[channel.id] = digimon
    await channel.send(embed=spawn_embed(digimon))


@tasks.loop(minutes=SPAWN_INTERVAL_MINUTES)
async def automatic_spawns():
    for guild in bot.guilds:
        channel_id = get_spawn_channel(guild.id)
        if not channel_id:
            continue
        channel = guild.get_channel(channel_id)
        if channel:
            await spawn_in_channel(channel)


@automatic_spawns.before_loop
async def before_spawns():
    await bot.wait_until_ready()


@bot.event
async def on_ready():
    init_db()
    if not automatic_spawns.is_running():
        automatic_spawns.start()
    print(f"DigiWorld conectado como {bot.user}.")


@bot.event
async def on_message(message):
    if message.author.bot or not message.guild:
        return

    digimon = active_spawns.get(message.channel.id)
    if digimon and normalize(message.content) == normalize(digimon["name"]):
        del active_spawns[message.channel.id]
        save_catch(message.author.id, message.guild.id, digimon)
        embed = discord.Embed(
            title="Digimon capturado!",
            description=(
                f"{message.author.mention} capturou **{digimon['name']}**!\n"
                f"**Estágio:** {digimon['stage']}"
            ),
            color=discord.Color.green()
        )
        await message.channel.send(embed=embed)

    await bot.process_commands(message)


@bot.command(name="configurar")
@commands.has_permissions(manage_guild=True)
async def configurar(ctx):
    with db() as con:
        con.execute(
            """INSERT INTO settings (guild_id, channel_id) VALUES (?, ?)
               ON CONFLICT(guild_id) DO UPDATE SET channel_id = excluded.channel_id""",
            (ctx.guild.id, ctx.channel.id)
        )
    await ctx.send("Canal de aparições configurado neste canal!")


@bot.command(name="spawn")
@commands.has_permissions(manage_guild=True)
async def manual_spawn(ctx):
    await spawn_in_channel(ctx.channel)


@bot.command(name="dex", aliases=["colecao", "coleção"])
async def dex(ctx, member: discord.Member = None):
    member = member or ctx.author
    rows = user_catches(member.id, ctx.guild.id)
    if not rows:
        await ctx.send(f"{member.display_name} ainda não capturou nenhum Digimon.")
        return

    lines = [f"**{name}** — {stage} ×{count}" for name, stage, count in rows]
    embed = discord.Embed(
        title=f"Digipédia de {member.display_name}",
        description="\n".join(lines[:25]),
        color=discord.Color.blurple()
    )
    embed.set_footer(text=f"Espécies capturadas: {len(rows)}")
    await ctx.send(embed=embed)


@bot.command(name="perfil")
async def perfil(ctx, member: discord.Member = None):
    member = member or ctx.author
    rows = user_catches(member.id, ctx.guild.id)
    total = sum(row[2] for row in rows)
    unique = len(rows)
    embed = discord.Embed(
        title=f"Treinador: {member.display_name}",
        description=f"**Digimons capturados:** {total}\n**Espécies diferentes:** {unique}",
        color=discord.Color.gold()
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    await ctx.send(embed=embed)


@bot.command(name="ajuda")
async def ajuda(ctx):
    embed = discord.Embed(
        title="DigiWorld — Comandos",
        description=(
            "`!configurar` — define o canal de aparições (administradores)\n"
            "`!spawn` — faz um Digimon aparecer (administradores)\n"
            "`!dex` — mostra sua coleção\n"
            "`!dex @membro` — mostra a coleção de alguém\n"
            "`!perfil` — mostra suas estatísticas\n"
            "`!ajuda` — mostra esta mensagem\n\n"
            "Quando um Digimon aparecer, digite o nome dele para capturá-lo."
        ),
        color=discord.Color.blurple()
    )
    await ctx.send(embed=embed)


@configurar.error
@manual_spawn.error
async def admin_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("Você precisa da permissão **Gerenciar servidor** para usar esse comando.")
    else:
        await ctx.send("Não consegui executar esse comando. Confira as permissões do bot.")


if not TOKEN:
    raise RuntimeError("Configure DISCORD_TOKEN no arquivo .env antes de iniciar o bot.")

bot.run(TOKEN)
