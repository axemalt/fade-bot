from typing import List, Dict
import os

import discord
from discord import app_commands

FADE_GUILD = discord.Object(id=1013604604480598046)


class Dropdown(discord.ui.Select):
    def __init__(self):
        # Set the options that will be presented inside the dropdown
        options = [
            discord.SelectOption(label="Whipper"),
            discord.SelectOption(label="Crackshot"),
            discord.SelectOption(label="Scrambler"),
        ]
        self.responded = False

        # The placeholder is what will be shown when no option is chosen
        # The min and max values indicate we can only pick one of the three options
        # The options parameter defines the dropdown options. We defined this above
        super().__init__(
            placeholder="Choose the weapon to tryout for...",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        # Use the interaction object to send a response message containing
        # the user's favourite colour or choice. The self object refers to the
        # Select object, and the values attribute gets a list of the user's
        # selected options. We only want the first one.
        self.responded = True
        await interaction.response.defer()
        self.view.stop()


class DropdownView(discord.ui.View):
    def __init__(self, interaction: discord.Interaction):
        super().__init__(timeout=30)

        # Adds the dropdown to our view object.
        self.dropdown = Dropdown()
        self.interaction = interaction
        self.add_item(self.dropdown)

    async def on_timeout(self):
        assert self is not None
        for child in self.children:
            child.disabled = True
        await self.interaction.edit_original_response(
            content="You took too long to respond.", view=None
        )


class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        # A CommandTree is a special type that holds all the application command
        # state required to make it work. This is a separate class because it
        # allows all the extra state to be opt-in.
        # Whenever you want to work with application commands, your tree is used
        # to store and work with them.
        # Note: When using commands.Bot instead of discord.Client, the bot will
        # maintain its own tree instead.
        self.tree = app_commands.CommandTree(self)

    # In this basic example, we just synchronize the app commands to one guild.
    # Instead of specifying a guild to every command, we copy over our global commands instead.
    # By doing so, we don't have to wait up to an hour until they are shown to the end-user.
    async def setup_hook(self):
        await self.tree.sync(guild=FADE_GUILD)


intents = discord.Intents.default()
intents.members = True
client = MyClient(intents=intents)


@client.event
async def on_ready():
    print(f"Logged in as {client.user} (ID: {client.user.id})")
    print("------")


@client.tree.command()
@app_commands.guilds(FADE_GUILD)
@app_commands.guild_only()
async def tryout(interaction: discord.Interaction):
    """Request a Tryout."""
    guild = client.get_guild(1013604604480598046)

    # getting role objects
    sydney: discord.Role = guild.get_role(1024233268456988672)
    us: discord.Role = guild.get_role(1024234114758492191)
    singa: discord.Role = guild.get_role(1024232417990557768)

    gun_to_role: Dict[str, discord.Role] = {
        "Crackshot": guild.get_role(1013731266450968607),
        "Scrambler": guild.get_role(1013731357874192394),
        "Whipper": guild.get_role(1013731493916455012),
    }

    region_to_tryouter: Dict[discord.Role, discord.Role] = {
        sydney: guild.get_role(1013624486924402848),
        us: guild.get_role(1013619689227812935),
        singa: guild.get_role(1013624304518311947),
    }

    # getting tryout channel
    tryout_channel = guild.get_channel(1013621441855504425)

    # getting useful things from the interaction
    member: discord.Member = interaction.user
    member_roles: List[discord.Role] = member.roles

    # see if member has region role and store the regions of member
    has_region = False
    regions: List[discord.Role] = []

    for role in [sydney, us, singa]:
        if role in member_roles:
            has_region = True
            regions.append(role)

    if not has_region:
        return await interaction.response.send_message(
            "Please get a region role in <#1024232222259167313>, then run this command again."
        )

    # get weapon the member wants to tryout for
    view = DropdownView(interaction)
    await interaction.response.send_message(view=view)
    await view.wait()

    if view.dropdown.responded == False:
        return

    # get the possible roles for tryouter
    weapon: discord.Role = gun_to_role[view.dropdown.values[0]]
    tryouter_regions: List[discord.Role] = [
        region_to_tryouter[role] for role in regions
    ]

    # get possible tryouters
    tryouters: List[discord.Member] = []

    for region in tryouter_regions:
        for tryouter in region.members:
            if weapon in tryouter.roles:
                tryouters.append(tryouter)

    # send message in tryout chat notifying member
    tryouters_string = ", ".join([tryouter.mention for tryouter in tryouters])
    if tryouters_string == "":
        return await interaction.edit_original_response(
            content="Sorry, no tryouters meet those constraints.", view=None
        )

    await interaction.edit_original_response(
        content="Please check <#1013621441855504425> for the next steps of trying out.",
        view=None,
    )

    embed: discord.Embed = discord.Embed(
        title="New Tryout",
        description=f"{member.mention}, your possible tryouters are {tryouters_string}. Feel free to DM them or ask them here to begin a 1v1.",
        color=discord.Color.blue(),
    )

    await tryout_channel.send(member.mention, embed=embed)


client.run(os.getenv("token"))
