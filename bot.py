import discord
import json
from datetime import datetime
from discord.ext import commands

# Crée une instance de bot avec un préfixe de commande (par exemple '!')
intents = discord.Intents.default()
intents.message_content = True  # Nécessaire pour recevoir le contenu des messages
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)

with open('blacklist.json', 'r') as fichier:
    blacklist = json.load(fichier)


# Événement lorsque le bot est prêt
@bot.event
async def on_ready():
    print(f'Bot connecté en tant que {bot.user}!')

# Commande de base - Répondre avec "pong" lorsqu'on tape "!ping"
@bot.command()
async def ping(ctx):
    await ctx.send('pong!')

def load_data():
    try:
        with open('warning.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# Enregistrer les données dans le fichier JSON
def save_data(data):
    with open('warning.json', 'w') as f:
        json.dump(data, f, indent=4)

warnings = load_data()

@bot.command()
async def warn(ctx, user: discord.User):

    uid = user.id
    # Vérifier si l'utilisateur existe déjà dans le fichier JSON
    if uid not in warnings:
        warnings[uid] = {'warns': 0, 'history': []}

    # Incrémenter le nombre de warns et ajouter un historique
    warnings[uid]['warns'] += 1
    warnings[uid]['history'].append({'timestamp': datetime.now().isoformat(), 'reason': 'Raison de l\'avertissement'})

    # Enregistrer les modifications
    save_data(warnings)
    await ctx.send('l\'utilisateur à été averti')

# Événement lorsque quelqu'un envoie un message
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return  # Ignore les messages du bot lui-même

    if "hello" in message.content.lower():
        await message.channel.send(f'Salut {message.author.name}!')
    
    # On fait appel à process_commands pour traiter les commandes (nécessaire si on override on_message)
    await bot.process_commands(message)

@bot.event
async def on_member_join(member):
    if blacklist["uid"] == member.id:
        await member.kick(reason=None)

    # Spécifie le canal de bienvenue, remplace 'welcome-channel' par le nom ou l'ID de ton canal
    channel = bot.get_channel(1295315646116008051)
    if channel:
        await channel.send(f"Bienvenue sur le serveur, {member.mention} ! Nous sommes ravis de te compter parmi nous.")


# Lancer le bot avec le token (à remplacer par ton token)
bot.run('mettre le secret ici')
