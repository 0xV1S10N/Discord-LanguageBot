import discord
import sqlite3
from discord.ext import commands
from discord.ui import Button, View

class Settings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.conn = sqlite3.connect('database/settings.db')
        self.cursor = self.conn.cursor()
        self.cursor.execute("CREATE TABLE IF NOT EXISTS server_settings (id INTEGER PRIMARY KEY, server_id TEXT UNIQUE, language_code TEXT)")
        self.conn.commit()

    @commands.command()
    async def setlang(self, ctx):
        server_id = str(ctx.guild.id)
        self.cursor.execute("SELECT language_code FROM server_settings WHERE server_id=?", (server_id,))
        row = self.cursor.fetchone()
        if row is None:
            current_lang = "en"
        else:
            current_lang = row[0]

        view = SetLangView(current_lang, cursor=self.cursor)
        view.ctx = ctx
        message = await ctx.send(f"{ctx.author.mention}, please select a language:", view=view)
        view.author_id = ctx.author.id
        await view.wait()

        if view.lang != current_lang:
            if row is None:
                self.cursor.execute("INSERT INTO server_settings(server_id, language_code) VALUES (?, ?)", (server_id, view.lang))
            else:
                self.cursor.execute("UPDATE server_settings SET language_code=? WHERE server_id=?", (view.lang, server_id))
            self.conn.commit()

        await message.edit(content=f"{ctx.author.mention}, language preference set to {view.lang}.")

    def cog_unload(self):
        self.conn.close()


class SetLangButton(Button):
    def __init__(self, lang_code, selected=False, author_id=None, cursor=None):
        label = lang_code.upper()
        style = discord.ButtonStyle.green if selected else discord.ButtonStyle.blurple
        if author_id is not None and author_id != 0:
            disabled = True
        else:
            disabled = False
        super().__init__(label=label, style=style, custom_id=lang_code, disabled=disabled)
        self.author_id = author_id
        self.cursor = cursor

    async def callback(self, interaction: discord.Interaction):
        if self.author_id is None or interaction.user.id == self.author_id:
            self.style = discord.ButtonStyle.green
            self.view.lang = self.custom_id
            for child in self.view.children:
                if child != self:
                    child.style = discord.ButtonStyle.blurple
                    child.disabled = True
            await interaction.response.edit_message(view=self.view)

            # Update the database with the new language setting
            server_id = str(interaction.guild.id)
            lang = self.custom_id
            self.cursor.execute("SELECT language_code FROM server_settings WHERE server_id=?", (server_id,))
            row = self.cursor.fetchone()
            if row is None:
                self.cursor.execute("INSERT INTO server_settings(server_id, language_code) VALUES (?, ?)", (server_id, lang))
            elif row[0] != lang:
                self.cursor.execute("UPDATE server_settings SET language_code=? WHERE server_id=?", (lang, server_id))
            self.cursor.connection.commit()
        else:
            self.style = discord.ButtonStyle.blurple
            self.disabled = True
            await interaction.response.edit_message(view=self.view)


class SetLangView(View):
    def __init__(self, lang, cursor=None):
        super().__init__(timeout=None)
        self.lang = lang
        self.author_id = None
        self.cursor = cursor

        self.add_item(SetLangButton("en", lang == "en", self.author_id, cursor=self.cursor))
        self.add_item(SetLangButton("pr", lang == "pr", self.author_id, cursor=self.cursor))

    async def interaction_check(self, interaction: discord.Interaction):
        return interaction.user == self.ctx.author

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
            if child.style == discord.ButtonStyle.green:
                child.label = f"{child.label} ✅"
        await self.message.edit(view=self)

    async def on_button_click(self, interaction: discord.Interaction, button: Button):
        self.lang = button.label.lower()
        for child in self.children:
            child.disabled = False
            child.style = discord.ButtonStyle.blurple
            if child.label.endswith(" ✅"):
                child.label = child.label[:-2]
        button.style = discord.ButtonStyle.green
        button.label = f"{button.label} ✅"
        await interaction.response.edit_message(view=self)
        
async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Settings(bot))