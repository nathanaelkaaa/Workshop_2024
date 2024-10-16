import discord
import json
from datetime import datetime
import os
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
        del warnings[uid]  # Supprime l'utilisateur du dictionnaire de warnings
        save_data('warning', warnings)
        await ctx.send("Les avertissements de l'utilisateur ont été supprimés.")

@bot.command()
async def blacklist(ctx, user: discord.User, raison):   
    with open('blacklist.json', 'r') as f:
        blacklist = json.load(f)

    blacklist[user.id] = {'raison': raison}

    with open('blacklist.json', 'w') as f:
        json.dump(blacklist, f, indent=4)
    
    await user.send("Tu as été black listé")
    await ctx.guild.kick(user, reason=None)

def load_scores():
    if os.path.exists('scoreUser.json'):
        with open('scoreUser.json', 'r') as file:
            return json.load(file)
    else:
        return {}

def save_scores(scores):
    with open('scoreUser.json', 'w') as file:
        json.dump(scores, file, indent=4)

def get_score(user_id, scores):
    return scores.get(str(user_id), 60)  # 60 est le score par défaut

# Mettre à jour le score d'un utilisateur
def update_score(user_id, points, scores):
    current_score = get_score(user_id, scores)
    new_score = max(0, min(100, current_score + points))  # Limiter le score entre 0 et 100
    scores[str(user_id)] = new_score
    save_scores(scores)
    return new_score

def initialize_user(user_id, scores):
    if str(user_id) not in scores:
        scores[str(user_id)] = 60  # Score initial de 60
        save_scores(scores)

# Déterminer le nombre d'étoiles basé sur le score
def get_star_rating(score):
    if score >= 81:
        return "⭐ ⭐ ⭐ ⭐ ⭐"  # 5 étoiles
    elif score >= 61:
        return "⭐ ⭐ ⭐ ⭐"  # 4 étoiles
    elif score >= 41:
        return "⭐ ⭐ ⭐"  # 3 étoiles
    elif score >= 21:
        return "⭐ ⭐"  # 2 étoiles
    else:
        return "⭐"  # 1 étoile

# Événement lorsque quelqu'un envoie un message
@bot.event
async def on_message(message):

    content = message.content.lower()
    scores = load_scores()

    if message.author == bot.user:
        return  # Ignore les messages du bot lui-même

    for word in banwordList:
        if word in content:
            await message.delete()
            await message.channel.send("Message supprimé car il contient un mot interdit.")
            return
        
    if any(word in content for word in ["merci", "aide", "positif"]):
        # Message positif ou constructif
        new_score = update_score(message.author.id, 3, scores)
        await message.channel.send(f"Merci pour votre contribution positive ! Nouveau score : {new_score}.")
    elif any(word in content for word in ["mauvais", "dislike"]):
        # Message de mauvaise qualité
        await message.channel.send("Message neutre détecté, score inchangé.")
    elif any(word in content for word in ["insulte", "spam", "pub"]):
        # Message inapproprié
        new_score = update_score(message.author.id, -10, scores)
        await message.channel.send(f"Attention, comportement inapproprié. Nouveau score : {new_score}.")

    # Sanction ou récompense en fonction du score
    score = get_score(message.author.id, scores)
    stars = get_star_rating(score)
    #if score <= 20:
     #   await message.channel.send(f"Votre score est bas ({stars} étoiles). Vous êtes temporairement mute.")
        # Ici, vous pouvez ajouter une logique pour mute l'utilisateur
    #elif score >= 80:
     #   await message.channel.send(f"Bravo ! Vous avez {stars} étoiles et un accès à des salons exclusifs.")
        # Ajouter une logique pour attribuer des récompenses

    
    # On fait appel à process_commands pour traiter les commandes (nécessaire si on override on_message)
    await bot.process_commands(message)

@bot.command()
async def score(ctx, member: discord.Member = None):
    member = member or ctx.author
    scores = load_scores()  # Charger les scores depuis le fichier JSON
    score = get_score(member.id, scores)
    stars = get_star_rating(score)
    await ctx.send(f"L'utilisateur {member.display_name} a {score} points de confiance ({stars} étoiles).")

# Commande pour réinitialiser un score (par un modérateur)
@bot.command()
@commands.has_permissions(administrator=True)
async def reset_score(ctx, member: discord.Member):
    scores = load_scores()  # Charger les scores depuis le fichier JSON
    initialize_user(member.id, scores)
    scores[str(member.id)] = 60  # Réinitialiser à 60 points
    save_scores(scores)
    await ctx.send(f"Le score de {member.display_name} a été réinitialisé à 60 points.")


@bot.event
async def on_member_join(member):
    with open('blacklist.json', 'r') as f:
        blacklist = json.load(f)

    try:
        if blacklist[str(member.id)]:
            await member.kick(reason=None)
    except KeyError as e:
        print("Membre non trouvé dans la blacklist")

    # Spécifie le canal de bienvenue, remplace 'welcome-channel' par le nom ou l'ID de ton canal
    channel = bot.get_channel(1295315646116008051)
    if channel:
        await channel.send(f"Bienvenue sur le serveur, {member.mention} ! Nous sommes ravis de te compter parmi nous.")

# Lancer le bot avec le token (à remplacer par ton token)
bot.run('oui')
