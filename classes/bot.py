import discord
from classes.dbmodels import LBGuild
import utility.funcs as utility
import tortoise.exceptions as te
from discord.ext import commands


class LettersBot(commands.AutoShardedBot):  # when you going

    async def on_ready(self):
        await utility.setup()
        await self.change_presence(activity=discord.Game(name='with you'))
        print("Ready!")

    async def on_message(self, message):
        if message.author.bot:
            return

        user = await utility.db_for_user(message.author.id, True)
        try:  # todo: make this into a db_for_guild function
            await LBGuild.get(id=message.guild.id)
        except te.DoesNotExist:
            await LBGuild.create(
                id=message.guild.id,
                muteRole=0,
                joinMesg=None
            )
            print(f"Created entry for {message.guild}")

        if user.canUseBot:
            await self.process_commands(message)

    async def on_command_error(self, ctx, exception):
        if isinstance(exception, commands.CommandNotFound):
            return

        errembed = discord.Embed(
            title="An error occurred.",
            description=str(exception),
            color=0xAA0000
        )

        errmsg = await ctx.send(embed=errembed)
        await errmsg.delete(delay=10)

    async def on_member_join(self, member):
        guild = member.guild
        guilddb = await LBGuild.filter(id=guild.id).first()
        joinmsg = getattr(guilddb, "joinMesg")
        chid = getattr(guilddb, "joinMesgChannel")
        joinmsgchannel = self.get_channel(chid) or guild.system_channel
        if (joinmsg is not None) and (joinmsgchannel is not None):
            await joinmsgchannel.send(f"{member.mention}\n{joinmsg}")
