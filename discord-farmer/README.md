# Discord Hour Farmer

Self-bot Discord — connexion vocale 24/7, mute + casque + screen share noir.

## Setup Render.com

1. Push ce dossier sur un repo GitHub privé
2. render.com → New → Background Worker → connecte le repo
3. Dans Environment, ajoute ces 3 variables :

```
TOKEN       = ton_token_discord
GUILD_ID    = id_du_serveur
CHANNEL_ID  = id_du_salon_vocal
```

4. Deploy

## Setup UptimeRobot (anti spin-down)

1. uptimerobot.com → New Monitor
2. Type : HTTP(s)
3. URL : https://NOM.onrender.com/ping
4. Interval : 5 minutes

## Récupérer les IDs

- Mode Développeur : Paramètres Discord → Avancé → Mode développeur ON
- guild_id  : clic droit sur le serveur → Copier l'identifiant
- channel_id : clic droit sur le salon vocal → Copier l'identifiant
- token     : F12 dans le navigateur Discord → Console → `localStorage.token`

## Commandes terminal (si run en local)

| Commande     | Action                    |
|--------------|---------------------------|
| `connect`    | Rejoint le vocal          |
| `disconnect` | Quitte le vocal           |
| `status`     | Affiche l'état            |
| `quit`       | Arrêt propre              |

## Run local

```bash
pip install -r requirements.txt
export TOKEN="ton_token"
export GUILD_ID="123456789"
export CHANNEL_ID="123456789"
python bot.py
```
