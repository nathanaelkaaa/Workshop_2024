import discord
import json
from datetime import datetime
from discord.ext import commands

# Crée une instance de bot avec un préfixe de commande (par exemple '!')
intents = discord.Intents.default()
intents.message_content = True  # Nécessaire pour recevoir le contenu des messages
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)


with open('banword.json', 'r') as fichier:
    banwordList = json.load(fichier)


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
def save_data(filename, data):
    with open(f'{filename}.json', 'w') as f:
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
    save_data('warning',warnings)
    await ctx.send('l\'utilisateur à été averti')

    if warnings[uid]['warns'] >= 3:
        await ctx.guild.kick(user, reason="3 avertissements atteints.")
        await ctx.send(f"{user.mention} a été expulsé du serveur.")
        del warnings[uid]  # Supprimer l'utilisateur du fichier JSON
        save_data('warning',warnings) # TODO faire en sorte que la suppresion des warn après le kick se fasse

@bot.command()
async def blacklist(ctx, user: discord.User, raison):   
    with open('blacklist.json', 'r') as f:
        blacklist = json.load(f)

    blacklist[user.id] = {'raison': raison}

    with open('blacklist.json', 'w') as f:
        json.dump(blacklist, f, indent=4)
    
    await ctx.guild.kick(user, reason=None)


# Événement lorsque quelqu'un envoie un message
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return  # Ignore les messages du bot lui-même

    for word in banwordList:
        if word in message.content.lower():
            await message.delete()
            await message.channel.send("Message supprimé car il contient un mot interdit.")
            return
    
    # On fait appel à process_commands pour traiter les commandes (nécessaire si on override on_message)
    await bot.process_commands(message)

@bot.event
async def on_member_join(member):
    with open('blacklist.json', 'r') as f:
        blacklist = json.load(f)

    if blacklist[str(member.id)]:
        await member.kick(reason=None)

    # Spécifie le canal de bienvenue, remplace 'welcome-channel' par le nom ou l'ID de ton canal
    channel = bot.get_channel(1295315646116008051)
    if channel:
        await channel.send(f"Bienvenue sur le serveur, {member.mention} ! Nous sommes ravis de te compter parmi nous.")

# Lancer le bot avec le token (à remplacer par ton token)
bot.run('ton token')
