import random
from os import getenv

import requests
from discord import Intents, Message
from discord.ext import commands
from discord.ext.commands import Context
from dotenv import load_dotenv
from notifiers import get_notifier
import json

load_dotenv()
TOKEN = getenv("TOKEN")
IMGFLIP_API_URL = "https://api.imgflip.com"

bot = commands.Bot(command_prefix="!",
                   case_insensitive=True,
                   intents=Intents.all())


class MemeGenerator:
    def __init__(self) -> None:
        print("imin")

    def list_memes(self) -> str:
        request = requests.get('https://api.imgflip.com/get_memes')
        r = json.loads(request.text)
        memes = r['data']['memes']
        lists = []
        for x, i in enumerate(memes):
            if memes[x]['id'] not in lists:
                lists.append(f"{memes[x]['id']: <10} {memes[x]['name']}")

        return lists

    def make_meme(self, template_id: int, top_text: str,
                  bottom_text: str) -> str:
        my_notjson = {
            "template_id": template_id,
            "username": "karlikbot",
            "password": "passw0rD",
            "text0": top_text,
            "text1": bottom_text,
            }
        my_meme = requests.post('https://api.imgflip.com/caption_image',
                                data=my_notjson)
        my_meme2 = json.loads(my_meme.text)
        my_meme2 = my_meme2['data']['url']
        print(f"{my_meme2}")
        return my_meme2


subbed = []


class MentionsNotifier:
    def __init__(self) -> None:
        print("k")

    def subscribe(self, user_id: int, email: str) -> None:
        self.user_id = user_id
        self.email = email

        if user_id in subbed:
            subbedindex = subbed.index(user_id)
            subbed[subbedindex+1] = email
        else:
            subbed.append(user_id)
            subbed.append(email)

    def unsubscribe(self, user_id: int) -> None:
        subbedindex = subbed.index(user_id)
        subbed.remove(user_id)
        subbed.pop(subbedindex)


class Hangman:
    lives = 7
    guessesbad = []
    guessesgood = []
    guesses = []
    wordlist = []
    wordlist = open("words.txt").read().split()
    word = ""
    hidden = ""
    guessedword = ""
    msg = ""
    quote = ""


meme_generator = MemeGenerator()


@bot.command(name="list_memes")
async def list_memes(ctx: Context) -> None:
    meme_list = meme_generator.list_memes()
    list_result = '\n'.join(meme_list[:25])
    await ctx.send(f"**Memes**\n```{list_result}```")


@bot.command(name="make_meme")
async def make_meme(ctx: Context, template_id: int, top_text: str,
                    bottom_text: str) -> None:
    meme_url = meme_generator.make_meme(template_id, top_text, bottom_text)

    await ctx.send(f'{meme_url}')


mentions_notifier = MentionsNotifier()


@bot.command(name="subscribe")
async def subscribe(ctx: Context, email: str) -> None:
    mentions_notifier.subscribe(ctx.author.id, email)


@bot.command(name="unsubscribe")
async def unsubscribe(ctx: Context) -> None:
    mentions_notifier.unsubscribe(ctx.author.id)


@bot.command(name="list_commands")
async def list_commands(ctx: Context) -> None:
    await ctx.send(f'**Commands**```\nlist_meme - lists IDs and template names'
                   f'\nmake_meme <id> "<top_text>" "<bottom_text>"'
                   f' - make your own meme\nsubscribe <email-address> '
                   f'- subscribe for notifications\nunsubcribe - stops sending'
                   f' notifications\nplay_hangman - start hangman session'
                   f'\nguess <letter> - guess letter in hangman game```')


@bot.event
async def on_message(message: Message) -> None:
    i = 0
    mention = message.mentions
    while i < len(mention):
        mentionid = (message.mentions[i].id)
        if mentionid in subbed:
            channel = message.jump_url
            subbedindex = subbed.index(mentionid)
            mail = subbed[subbedindex+1]
            mail = mail.replace(" ", "")
            email = get_notifier('email')
            settings = {
                'host': '',
                'port': 465,
                'ssl': True,

                'username': '',
                'password': '',

                'to': mail,
                'from': '',

                'subject': "Discord notification",
                'message': f"someone mentioned you in channel {channel}",
            }
            res = email.notify(**settings)
            print(mail)
            print(channel)
        i += 1

    await bot.process_commands(message)


# --------- LEVEL 3 ----------
hangman = Hangman()

hangman_games = {}


@bot.command(name="play_hangman")
async def play_hangman(ctx: Context) -> None:
    player_id = ctx.author.id

    if player_id in hangman_games.keys():
        current_game = hangman_games[player_id]
    else:
        current_game = Hangman()
        current_game.word = random.choice(hangman.wordlist)
        hangman_games[player_id] = current_game
    current_game.guess = ', '.join(current_game.guesses)
    current_game.guess = current_game.guess.upper()
    current_game.lives = 7
    current_game.word = random.choice(current_game.wordlist)
    current_game.word = current_game.word.upper()
    current_game.hidden = ""
    current_game.guessedword = ""
    current_game.guesses = []
    current_game.guessesbad = []
    current_game.quote = ""
    i = 0
    while i < len(current_game.word):
        current_game.hidden += current_game.word[i].\
            replace(current_game.word[i], "- ")
        i += 1
    current_game.msg = await ctx.send(f'**Hangman**\nPlayer: '
                                      f'{ctx.author.name}\n'
                                      f'Guesses: {current_game.guess}\nLives: '
                                      f'{current_game.lives}\nWord: '
                                      f'{current_game.hidden}')
    # TODO: Implementujte tento prĂ­kaz s vyuĹľitĂ­m triedy Hangman.
    pass


@bot.command(name="guess")
async def guess(ctx: Context, letter: str) -> None:
    player_id = ctx.author.id

    await ctx.message.delete()

    if player_id in hangman_games.keys():
        current_game = hangman_games[player_id]
    else:
        current_game = Hangman()
        hangman_games[player_id] = current_game
    letter = letter

    async def send_message():
        await current_game.msg.edit(content=f'**Hangman**\nPlayer: '
                                            f'{ctx.author.name}\n'
                                            f'Guesses: {current_game.guess}\n'
                                            f'Lives: {current_game.lives}\n'
                                            f'Word: {current_game.guessedword}'
                                            f'\n{current_game.quote}')

    async def game_state():
        if current_game.lives <= 0:
            current_game.quote = f"You lost, the word was" \
                                 f" **{current_game.word}**"
            await send_message()
            return
        if current_game.guessedword.replace(" ", "")\
                == current_game.word.upper():
            current_game.quote = "You win!"
            await send_message()
            return

    await game_state()

    if current_game.lives <= 0:
        current_game.quote = f'You already lost, ' \
                             f'you need to start new !play_hangman'
        await send_message()
        return

    if current_game.guessedword.replace(" ", "") == current_game.word.upper():
        current_game.quote = f'You already won, ' \
                             f'you need to start new !play_hangman'
        await send_message()
        return

    if len(letter) > 1:
        return

    if letter.upper() in current_game.guesses:
        current_game.quote = "You already guessed that"
        await send_message()
        return

    lettercheck = letter.isalpha()
    if lettercheck is False:
        current_game.quote = "Only letters"
        await send_message()
        return

    current_game.guessedword = ""
    for i in current_game.word.lower():
        if letter.lower() == i or i.upper() in current_game.guesses:
            current_game.guessedword += i.upper()+" "
            current_game.guessesgood.append(letter.upper())
            current_game.quote = "Correct Guess"
        else:
            current_game.guessedword += "- "

    if letter.lower() not in current_game.word.lower():
        if letter.upper() not in current_game.guesses:
            current_game.guesses.append(letter.upper())
            current_game.guessesbad.append(letter.upper())
            current_game.quote = "Wrong Guess"

    if letter.upper() not in current_game.guesses:
        current_game.guesses.append(letter.upper())

    current_game.guess = ', '.join(current_game.guesses)
    current_game.lives = 7 - (len(current_game.guessesbad))

    await game_state()
    await send_message()
    # TODO: Implementujte tento prĂ­kaz s vyuĹľitĂ­m triedy Hangman.
    pass

bot.run(TOKEN)
