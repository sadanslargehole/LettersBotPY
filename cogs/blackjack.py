
import discord
from discord.ext import commands
from math import floor
from discord.ext.commands.cooldowns import BucketType
import utility.gameutils.blackjack as bj
hands = {}
dealer_hands = {}
decks = {}
bets = {}
active_game = {}
active_game_bot = {}
user_db = {}
# TODO: move unhiding the dealers hand into a function
# TODO: add color to all the embeds
# TODO: add winnings to all winning embeds
#   green for win
#   red for loss
#   nothing for tie


class blj(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["bjq"])
    async def blackjackquit(self, ctx):
        """ Quits any game of blackjack you have going """
        active_game[ctx.author.id] = None
        active_game_bot[ctx.author.id] = None
        await ctx.message.add_reaction('✅')

    @commands.command(aliases=['bjr'])
    @commands.cooldown(1, 600 , BucketType.user) #pervent spamming
    async def blackjackResend(self, ctx):
        """ Resends any active blackjack game message you lost """
        if active_game[ctx.author.id]:
            active_game[ctx.author.id] = ctx.message
            readable_hand = [card.name for card in hands[ctx.author.id]]
            readable_dealer_hand = [card.name for card in dealer_hands[ctx.author.id]]
            active_game_bot = await ctx.send( embed=discord.Embed(
                title="Blackjack!",
                description=f"Player's hand: {' | '.join(readable_hand)} (total {bj.value(hands[ctx.author.id])})\n" +
                f"Dealer's hand: {' | '.join(readable_dealer_hand)} (total {bj.value(dealer_hands[ctx.author.id])})"
            ).set_footer(text="Thanks for Playing")
                
            )
            await active_game_bot[ctx.author.id].add_reaction("🃏")
            await active_game_bot[ctx.author.id].add_reaction("🖐️")
        else:
            raise Exception("You dont have any active game to resend")
    @commands.command(aliases=["bj"])
    async def blackjack(self, ctx, wager: int):
        """ Blackjack! Maximum wager 7500 """
        # here goes nothing
        bal = await bj.get_bal(ctx.author.id)
        # check if bal is enough
        wager = floor(wager)
        if wager > bal:
            raise Exception("You can't afford that wager.")
        if wager > 7500:
            raise Exception("Maximum wager is 7500.")
        if wager < 15:
            raise Exception("Minimum wager is 15.")
        if active_game.get(ctx.author.id):  # wok made dude shit himself :sob:
            raise Exception(
                "You already have a game in progress. Finish that first.\n" +
                f"You can also use {self.bot.command_prefix}bjq to end your active game\n"+
                f'or use {self.bot.command_prefix}bjr to resend the blackjack message ')
        # This shit is a little bit of a mess
        decks[ctx.author.id] = bj.new_deck()
        deck = decks[ctx.author.id]
        active_game[ctx.author.id] = ctx.message

        hands[ctx.author.id] = [bj.deal(deck), bj.deal(deck)]
        dealer_hands[ctx.author.id] = [bj.deal(deck), bj.deal(deck)]
        dealer_hands[ctx.author.id][1].hidden = True  # lol, horrorcode
        dealer_hands[ctx.author.id][1].name = "?? of ?"
        bets[ctx.author.id] = wager
        await bj.update_bal(ctx.author.id, 0-wager)

        # did we already win? trick question: you're programming, you never win
        # there has to be a better way to do this

        if bj.value(hands[ctx.author.id]) == 21:  # player got a blackjack
            readable_hand = [card.name for card in hands[ctx.author.id]]
            readable_dealer_hand = [card.name for card in dealer_hands[ctx.author.id]]
            for card in dealer_hands[ctx.author.id]:
                card.hidden = False
                card.name = str(card.symbol) + " " + card.suit
            if not bj.value_with_hidden(dealer_hands[ctx.author.id]) == 21:  # bot did not black jack
                win_embed = discord.Embed(
                    title="You Won!",
                    description=f"Player's hand: {' | '.join(readable_hand)} (total {bj.value(hands[ctx.author.id])})\n" +
                    f"Dealer's hand: {' | '.join(readable_dealer_hand)} (total {bj.value(dealer_hands[ctx.author.id])})",
                    color=discord.Color.green()
                ).set_footer(text="Thanks for Playing")
                winnings = bets[ctx.author.id] * 3.5
                win_embed.add_field(name="Winnings", value=winnings)
                await bj.update_bal(ctx.author.id, winnings)
                active_game[ctx.author.id] = None
                active_game_bot[ctx.author.id] = None
                return await ctx.send(embed=win_embed)
            else:
                # return the users money
                readable_hand = [card.name for card in hands[ctx.author.id]]
                readable_dealer_hand = [card.name for card in dealer_hands[ctx.author.id]]

                await bj.update_bal(ctx.author.id, bets[ctx.author.id])
                # send the tie embed
                tie_embed = discord.Embed(
                    title="You Tied",
                    description=f"Player's hand: {' | '.join(readable_hand)} (total {bj.value(hands[ctx.author.id])})\n" +
                    f"Dealer's hand: {' | '.join(readable_dealer_hand)} (total {bj.value(dealer_hands[ctx.author.id])})"
                ).set_footer(text="Thanks for Playing")
                await ctx.send(embed=tie_embed)
                active_game[ctx.author.id] = None
                active_game_bot[ctx.author.id] = None
                return

        if bj.value_with_hidden(dealer_hands[ctx.author.id]) == 21:
            # player loses
            for card in dealer_hands[ctx.author.id]:
                card.hidden = False
                card.name = str(card.symbol) + " " + card.suit
            readable_hand = [card.name for card in hands[ctx.author.id]]
            readable_dealer_hand = [card.name for card in dealer_hands[ctx.author.id]]
            lossembed = discord.Embed(
                title="You Lost.",
                description="The Dealer got 21.\n" +
                f"Player's hand: {' | '.join(readable_hand)} (total {bj.value(hands[ctx.author.id])})\n" +
                f"Dealer's hand: {' | '.join(readable_dealer_hand)} (total {bj.value(dealer_hands[ctx.author.id])})",
                color=discord.Color.red()
            ).set_footer(text="Thanks for Playing")
            await ctx.send(embed=lossembed)
            # end the game
            active_game[ctx.author.id] = None
            active_game_bot[ctx.author.id] = None
            return

        readable_hand = [card.name for card in hands[ctx.author.id]]
        readable_dealer_hand = [card.name for card in dealer_hands[ctx.author.id]]
        active_game_bot[ctx.author.id] = await ctx.send(embed=discord.Embed(
            title="Blackjack",
            description=f"Player's hand: {' | '.join(readable_hand)} (total {bj.value(hands[ctx.author.id])})\n" +
            f"Dealer's hand: {' | '.join(readable_dealer_hand)} (total {bj.value(dealer_hands[ctx.author.id])})",
        ).set_footer(text="🃏 HIT | 🖐️ STAND")
        )
        await active_game_bot[ctx.author.id].add_reaction("🃏")
        await active_game_bot[ctx.author.id].add_reaction("🖐️")

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        newtitle = ''

        if not user.bot:
            if active_game[user.id]:
                if (reaction.emoji == "🃏" or "🖐️"):
                    await reaction.remove(user)

                if reaction.emoji == "🃏":
                    # hit
                    hit = bj.player_hit(bj.deal(decks[user.id]), hands[user.id])

                    if bj.value(hit) == 21:  # explicitly check for true, it could be a truthy value
                        color = discord.Color.green()
                        newtitle = "You Win!"
                        # unhide dealer cards for the embed message
                        for card in dealer_hands[user.id]:
                            card.hidden = False
                            card.name = str(card.symbol) + " " + card.suit
                        dealer_hands[user.id] = bj.dealer_finish(dealer_hands[user.id], decks[user.id])
                        # uhh this should work
                        # check if the dealer also got black jack, if so, push
                        if bj.value(dealer_hands[user.id]) == 21:
                            await bj.update_bal(user.id, bets[user.id])
                            newtitle = "Push!"
                            color = discord.Color.default()
                        else:
                            await bj.update_bal(user.id, bets[user.id] * 2.5)
                        readable_hand = [card.name for card in hands[user.id]]
                        readable_dealer_hand = [card.name for card in dealer_hands[user.id]]
                        win_embed = discord.Embed(
                            title=newtitle,
                            description=f"Player's hand: {' | '.join(readable_hand)} (total {bj.value(hands[user.id])})\n" +
                            f"Dealer's hand: {' | '.join(readable_dealer_hand)} (total {bj.value(dealer_hands[user.id])})",
                            color=color
                        )
                        win_embed.add_field(name="Winnings", value=bets[user.id] * 2.5)
                        await active_game_bot[user.id].edit(embed=win_embed)
                        active_game[user.id] = None
                        active_game_bot[user.id] = None  # clean up
                        return

                    elif bj.value(hit) > 21:
                        newtitle = "You busted!"
                        for card in dealer_hands[user.id]:
                            card.hidden = False
                            card.name = card.name = str(card.symbol) + " " + card.suit
                        hand = bj.dealer_finish(dealer_hands[user.id], decks[user.id])
                        readable_hand = [card.name for card in hands[user.id]]
                        readable_dealer_hand = [card.name for card in dealer_hands[user.id]]
                        # i didnt forget to update the embed for this
                        if bj.value(hand) > 21:
                            newtitle = 'You Both Busted!'
                            await active_game_bot[user.id].edit(embed=discord.Embed(
                                title=newtitle or "Blackjack",
                                description=f"Player's hand: {' | '.join(readable_hand)} (total {bj.value(hands[user.id])})\n" +
                                f"Dealer's hand: {' | '.join(readable_dealer_hand)} (total {bj.value(dealer_hands[user.id])})",
                            )
                                .set_footer(text="Thanks For Playing!"))
                            # they both busted, return users money
                            await bj.update_bal(user.id, bets[user.id])
                        else:
                            await active_game_bot[user.id].edit(embed=discord.Embed(
                                title=newtitle,
                                description=f"Player's hand: {' | '.join(readable_hand)} (total {bj.value(hands[user.id])})\n" +
                                f"Dealer's hand: {' | '.join(readable_dealer_hand)} (total {bj.value(dealer_hands[user.id])})",
                                color=discord.Color.red()
                            ).set_footer(text="Thanks For Playing!"))
                        # in either case, clean up
                        active_game[user.id] = None
                        active_game_bot[user.id] = None

                    else:
                        readable_hand = [card.name for card in hands[user.id]]
                        readable_dealer_hand = [card.name for card in dealer_hands[user.id]]
                        await active_game_bot[user.id].edit(embed=discord.Embed(
                            title=newtitle or "Blackjack",
                            description=f"Player's hand: {' | '.join(readable_hand)} (total {bj.value(hands[user.id])})\n" +
                            f"Dealer's hand: {' | '.join(readable_dealer_hand)} (total {bj.value(dealer_hands[user.id])})",
                        ).set_footer(text="🃏 HIT | 🖐️ STAND"))

                if reaction.emoji == "🖐️" and not user.bot:
                    # user stands
                    footer = 'Thanks For Playing'
                    # store users bal in a vairable
                    # the user cant hit anymore; unhide the cards
                    for card in dealer_hands[user.id]:
                        card.hidden = False
                        card.name = str(card.symbol) + " " + card.suit

                    dealer_hands[user.id] = bj.dealer_finish(dealer_hands[user.id], decks[user.id])
                    dealer_value = bj.value(dealer_hands[user.id])
                    user_value = bj.value(hands[user.id])
                    readable_hand = [card.name for card in hands[user.id]]
                    readable_dealer_hand = [card.name for card in dealer_hands[user.id]]
                    embed = discord.Embed(
                        title=newtitle or 'Blackjack',
                        description=f"Player's hand: {' | '.join(readable_hand)} (total {bj.value(hands[user.id])})\n" +
                        f"Dealer's hand: {' | '.join(readable_dealer_hand)} (total {bj.value(dealer_hands[user.id])})"
                    ).set_footer(text=footer)

                    if dealer_value > user_value and not (dealer_value > 21):
                        embed.title = "Dealer Wins!"
                        embed.color = discord.Color.red()
                    if dealer_value < user_value or (dealer_value > 21):
                        embed.title = "You win!"
                        await bj.update_bal(user.id, bets[user.id] * 1.5)
                        embed.add_field(name="Winnings", value=bets[user.id] * 1.5)
                        embed.color = discord.Color.green()
                    if dealer_value == user_value:
                        embed.title = "Push!"
                        await bj.update_bal(user.id, bets[user.id])
                    readable_hand = [card.name for card in hands[user.id]]
                    readable_dealer_hand = [card.name for card in dealer_hands[user.id]]
                    await active_game_bot[user.id].edit(embed=embed)
                    # clear game
                    active_game[user.id] = None
                    active_game_bot[user.id] = None


async def setup(bot):
    await bot.add_cog(blj(bot))
