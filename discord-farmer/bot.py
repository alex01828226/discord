import discord
import asyncio
import os
import sys
import signal
import logging
from aiohttp import web

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
log = logging.getLogger(__name__)

TOKEN      = os.environ.get("TOKEN", "")
GUILD_ID   = int(os.environ.get("GUILD_ID", "0"))
CHANNEL_ID = int(os.environ.get("CHANNEL_ID", "0"))

if not TOKEN or GUILD_ID == 0 or CHANNEL_ID == 0:
    log.error("TOKEN, GUILD_ID ou CHANNEL_ID manquant dans les variables d'environnement.")
    sys.exit(1)

client = discord.Client()
voice_client: discord.VoiceClient | None = None


class SilentAudioSource(discord.AudioSource):
    def read(self) -> bytes:
        return b"\x00" * 3840

    def is_opus(self) -> bool:
        return False


async def connect_voice():
    global voice_client

    guild = client.get_guild(GUILD_ID)
    if guild is None:
        log.error("Guild introuvable. Vérifie GUILD_ID.")
        return

    channel = guild.get_channel(CHANNEL_ID)
    if channel is None or not isinstance(channel, discord.VoiceChannel):
        log.error("Channel vocal introuvable. Vérifie CHANNEL_ID.")
        return

    if voice_client and voice_client.is_connected():
        log.info("Déjà connecté.")
        return

    try:
        voice_client = await channel.connect(self_mute=True, self_deaf=True)
        log.info(f"Connecté à #{channel.name} (mute + casque)")

        voice_client.play(
            SilentAudioSource(),
            after=lambda e: log.warning(f"Audio stopped: {e}")
        )

        await send_stream_create(voice_client, channel)

    except Exception as e:
        log.error(f"Erreur connexion vocale: {e}")


async def send_stream_create(vc: discord.VoiceClient, channel: discord.VoiceChannel):
    try:
        ws = vc.ws
        payload = {
            "op": 18,
            "d": {
                "type": "screen",
                "guild_id": str(channel.guild.id),
                "channel_id": str(channel.id),
                "preferred_region": None,
            }
        }
        await ws.send_as_json(payload)
        log.info("Stream Create (screen share) envoyé.")
    except Exception as e:
        log.warning(f"Stream create failed: {e}")


async def disconnect_voice():
    global voice_client
    if voice_client and voice_client.is_connected():
        await voice_client.disconnect()
        voice_client = None
        log.info("Déconnecté du vocal.")
    else:
        log.info("Pas connecté au vocal.")


async def handle_ping(request):
    status = "connected" if (voice_client and voice_client.is_connected()) else "disconnected"
    return web.Response(text=f"ok | voice: {status}")


async def start_http():
    app = web.Application()
    app.router.add_get("/ping", handle_ping)
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    await site.start()
    log.info("Serveur HTTP ping actif sur :8080")


@client.event
async def on_ready():
    log.info(f"Connecté en tant que {client.user} (ID: {client.user.id})")
    asyncio.create_task(start_http())
    await asyncio.sleep(2)
    await connect_voice()
    asyncio.create_task(cli_loop())


@client.event
async def on_voice_state_update(member, before, after):
    global voice_client
    if member.id == client.user.id:
        if before.channel is not None and after.channel is None:
            log.warning("Éjecté du vocal. Reconnexion dans 5s...")
            await asyncio.sleep(5)
            await connect_voice()


async def cli_loop():
    loop = asyncio.get_event_loop()
    while True:
        try:
            cmd = await loop.run_in_executor(None, sys.stdin.readline)
            cmd = cmd.strip().lower()

            if cmd == "connect":
                await connect_voice()
            elif cmd == "disconnect":
                await disconnect_voice()
            elif cmd == "status":
                if voice_client and voice_client.is_connected():
                    log.info(f"STATUS: Connecté à {voice_client.channel.name}")
                else:
                    log.info("STATUS: Pas connecté.")
            elif cmd in ("quit", "exit"):
                await disconnect_voice()
                await client.close()
                break
            elif cmd:
                log.info("Commandes: connect / disconnect / status / quit")
        except Exception as e:
            log.error(f"CLI error: {e}")


def handle_sigterm(*_):
    log.info("SIGTERM reçu, arrêt propre...")
    asyncio.create_task(shutdown())


async def shutdown():
    await disconnect_voice()
    await client.close()


signal.signal(signal.SIGTERM, handle_sigterm)

if __name__ == "__main__":
    try:
        client.run(TOKEN, bot=False)
    except discord.LoginFailure:
        log.error("Token invalide. Vérifie la variable TOKEN.")
    except KeyboardInterrupt:
        log.info("Arrêt par Ctrl+C")
