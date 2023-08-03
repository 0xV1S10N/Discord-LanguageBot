import discord
import json
import sqlite3
import aiohttp
from discord.ext import commands


en_strings = {}
with open('languages/en.json', encoding='utf-8') as f:
    en_strings = json.load(f)

pr_strings = {}
with open('languages/pr.json', encoding='utf-8') as f:
    pr_strings = json.load(f)

with open('config.json') as f:
    config = json.load(f)

token = config.get('token')
bot_id = config.get('application_id')
prefix = config.get('prefix')

class MyBot(commands.Bot):

    def __init__(self):

        super().__init__(command_prefix = prefix,
                         intents = discord.Intents.all(),
                         case_insensitive=True,
                         application_id =bot_id)
        self.initial_extensions = [
            "cogs.settings"]
        self.added = False

    async def setup_hook(self):
        for cogs in self.initial_extensions: 
            await self.load_extension(cogs)
        print(f"Synced for {self.user}!")

    #closing
    async def close(self):
        await super().close()
        await self.session.close()

    #on_ready message
    async def on_ready(self):
        print(f'{self.user} has connected to Discord!')
        if not self.added:
            self.added = True

bot = MyBot()

conn = sqlite3.connect('database/settings.db')
cursor = conn.cursor()

def initialize_database():
    cursor.execute("""CREATE TABLE IF NOT EXISTS server_settings (
                          id INTEGER PRIMARY KEY,
                          server_id TEXT,
                          language_code TEXT
                       )""")
    conn.commit()

initialize_database()

        
@bot.command()
async def hello(ctx):
    server_id = str(ctx.guild.id)
    cursor.execute("SELECT language_code FROM server_settings WHERE server_id=?", (server_id,))
    row = cursor.fetchone()
    if row is None:
        await ctx.send("Pls Select Lang First use : ``!setlang type``")
    else:
        language_code = row[0]
        if language_code == "en":
            await ctx.send(en_strings["embed_footer"])
        elif language_code == "pr":
            await ctx.send(pr_strings["embed_footer"])
        else:
            await ctx.send(f"Invalid language code: {language_code}")





@bot.event
async def on_guild_remove(guild):
    server_id = str(guild.id)
    cursor.execute("DELETE FROM server_settings WHERE server_id=?", (server_id,))
    conn.commit()

bot.run(token)