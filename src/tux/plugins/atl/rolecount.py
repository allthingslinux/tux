"""
All Things Linux Discord Server - Role Count Plugin.

This plugin is specifically designed for the All Things Linux Discord server
and contains hardcoded role IDs that are specific to that server.

DO NOT USE this plugin on other Discord servers - it will not work correctly
and may cause errors due to missing roles.

This serves as an example of server-specific functionality that should be
implemented as a plugin rather than core bot functionality.
"""

import discord
from discord import app_commands
from reactionmenu import ViewButton, ViewMenu

from tux.core.base_cog import BaseCog
from tux.core.bot import Tux
from tux.ui.embeds import EmbedCreator

# I added comments to all these roles below incase someone really wanted to edit this - meatharvester
# last updated 10/17/2025

des_ids = [
    [1175177565086953523, "_kde"],  # KDE
    [1175177703066968114, "_gnome"],  # GNOME
    [1175177036990533795, "_i3"],  # i3
    [1175222139046080582, "_hyprland"],  # Hyprland
    [1175177087183769660, "_sway"],  # Sway
    [1175243354557128765, "_xfce"],  # XFCE
    [1175220317174632489, "_dwm"],  # DWM/DWL
    [1175177142108160121, "_bspwm"],  # BSPWM
    [1181288708977205318, "_cinnamon"],  # Cinnamon
    [1175242546012753941, "_xmonad"],  # XMonad
    [1175241189935550554, "_awesome"],  # AwesomeWM
    [1175245686489501726, "_mate"],  # MATE
    [1175241537689489408, "_qtile"],  # Qtile
    [1175221470587256852, "_emacs"],  # EXWM
    [1175240614124732487, "_herbstluft"],  # HerbstluftWM
    [1175219898113331331, "_icewm"],  # IceWM
    [1175337897180803082, "_openbox"],  # Openbox
    [1175336806963744788, "_wayfire"],  # Wayfire
    [1367180985602412668, "_cosmic"],  # COSMIC
    [1192149690096033882, "_budgie"],  # Budgie
    [1196324646170148925, "_riverwm"],  # River
    [1350877106606968903, "_niri"],  # Niri
    [1232200058737397771, "_lxqt"],  # LXQt
    [1297922269628338290, "grey_question"],  # Other DE/WM
]

distro_ids = [
    [1175176142899122246, "_arch"],  # Arch
    [1175176866928263220, "_debian"],  # Debian
    [1175176922460860517, "_fedora"],  # Fedora
    [1175176812293271652, "_ubuntu"],  # Ubuntu
    [1175235143707918436, "_windows"],  # Windows
    [1175176279616663573, "_gentoo"],  # Gentoo
    [1175227850119458897, "_freebsd"],  # *BSD
    [1175177831551086593, "_nixos"],  # NixOS
    [1175178088347344916, "_void"],  # Void
    [1175176981936087161, "_opensuse"],  # openSUSE
    [1175244437530611712, "_macos"],  # macOS
    [1175241975818092564, "_alpine"],  # Alpine
    [1175177993526726717, "_linuxmint"],  # Mint
    [1176533514385096714, "_bedrock"],  # Bedrock
    [1290975975919849482, "_arch"],  # Arch-based
    [1182152672447569972, "_slackware"],  # Slackware
    [1178347123905929316, "_ubuntu"],  # Ubuntu-basesd
    [1180570700734546031, "_lfs"],  # LFS
    [1192177499413684226, "_asahi"],  # Asahi
    [1207599112585740309, "_fedoraatomic"],  # Fedora Atomic
    [1210000519272079411, "_redhat"],  # RHEL
    [1212028841103597679, "_plan9"],  # Plan 9
    [1237704018629885983, "_cachyos"],  # CachyOS
    [1237701203404783698, "_fedora"],  # Fedora-based
    [1386793599483646044, "_endeavouros"],  # EndeavourOS
    [1367198731115434035, "_solus"],  # Solus
    [1242497621998698516, "_ublue"],  # Universal Blue
    [1297922102917206109, "grey_question"],  # Other OS
]

lang_ids = [
    [1175612831996055562, "_python"],  # Python
    [1175612831861837864, "_sh"],  # Shell Script
    [1175612831941525574, "_html"],  # HTML/CSS
    [1175612831115260006, "_javascript"],  # JS/TS
    [1175612831652139008, "_c"],  # C-Lang
    [1386793293576409139, "_cplusplus"],  # C++
    [1175612831790534797, "_lua"],  # Lua
    [1175612831631155220, "_rust"],  # Rust
    [1175612831907979336, "_java"],  # Java
    [1175612831798939648, "_csharp"],  # C#
    [1178389324098699294, "_php"],  # PHP
    [1175612831798931556, "_haskell"],  # Haskell
    [1175612831727632404, "_ruby"],  # Ruby
    [1175612831828295680, "_kotlin"],  # Kotlin
    [1175739620437266443, "_go"],  # Go-Lang
    [1175612831731822734, "_lisp"],  # Lisp
    [1175612831920558191, "_perl"],  # Perl
    [1185975879231348838, "_asm"],  # Assembly
    [1175612830389633164, "_ocaml"],  # OCaml
    [1175612831727620127, "_erlang"],  # Erlang
    [1175612831287218250, "_zig"],  # Zig
    [1175612831878615112, "_julia"],  # Julia
    [1175612831429824572, "_crystal"],  # Crystal
    [1175612831761182720, "_elixir"],  # Elixer
    [1207600618542206976, "_clojure"],  # Clojure
    [1232389554426876045, "_godot"],  # GDScript
    [1232390379337285692, "_nim"],  # Nim
    [1237700521465217084, "_swift"],  # Swift
    [1214465450860351498, "_r"],  # R-Lang
    [1263802450591223830, "_dart"],  # Dart
]

editor_ids = [
    [1182069378636849162, "_vsc"],  # VS code
    [1180571441276649613, "_nvim"],  # Vi Based
    [1180660198428393643, "_emacs"],  # Emacs
    [1192140446919561247, "_gnunano"],  # Nano
    [1193242175295729684, "_kate"],  # Kate
    [1192135710443065345, "_micro"],  # Micro
    [1193241331221405716, "_jetbrains"],  # JetBrains
    [1185974067472380015, "_helix"],  # Helix
    [1367199157768425622, "_ed"],  # Ed
    [1392616344075243570, "_Cursor"],  # Cursor
    [1367199970587050035, "_zed"],  # Zed
]

shell_ids = [
    [1198870981733785610, "_bash"],  # /bin/bash
    [1212034189638111232, "_debian"],  # /bin/dash
    [1198874174182133771, "elf"],  # /bin/elvish
    [1198870266680451162, "fish"],  # /bin/fish
    [1198868737227509801, "corn"],  # /bin/ksh
    [1198871282717040670, "new"],  # /bin/nu
    [1198872955598409848, "shell"],  # /bin/sh
    [1198868318266851339, "zap"],  # /bin/zsh
    [1198875780252454932, "_python"],  # /bin/xonsh
]

vanity_ids = [
    [1179277471883993219, "wheel"],  # %wheel
    [1197348658052616254, "mag"],  # Log Reader
    [
        1175237664811790366,
        "regional_indicator_e",
    ],  # ? (Yes seriously thats the role name.)
    [1186473849294962728, "smirk_cat"],  # :3
    [1180568491527516180, "supertuxkart"],  # STKS Award
    [1179551412070404146, "100"],  # Based
    [1183896066588950558, "rabbit"],  # Chronic Hopper
    [1192245668534833242, "cd"],  # Crate Digger
    [1179551519624925294, "hugging"],  # Helpful
    [1175756229168079018, "_git"],  #  FOSS Contributor
    [1197353868103782440, "goblin"],  # VC Goblin
    [1217601089721995264, "old_man"],  # Boomer
    [1346489154766372874, "headphones"],  # ON AIR
    [1184245004198228050, "tux"],  # Tux Contributor
    [1252848417026080809, "crown"],  # Donor Legend
    [1249858729311211611, "first_place"],  # Super Donor
    [1253392359765311518, "second_place"],  # Donor +
    [1249802272007917678, "third_place"],  # Donor
    [1172264612578742334, "rocket"],  # Booster
    [1247532827902480475, "books"],  # Wiki Author
]

# TODO: Figure out how to make rolecount work without hard coded ids and icons


class RoleCount(BaseCog):
    """Role count plugin for ATL Discord server."""

    def __init__(self, bot: Tux):
        """Initialize the RoleCount plugin.

        Parameters
        ----------
        bot : Tux
            The bot instance to initialize the plugin with.
        """
        self.bot = bot
        self.roles_emoji_mapping = {
            "ds": distro_ids,
            "lg": lang_ids,
            "de": des_ids,
            "edit": editor_ids,
            "vanity": vanity_ids,
        }

    @app_commands.command(name="rolecount")
    @app_commands.describe(which="Which option to list!")
    @app_commands.choices(
        which=[
            app_commands.Choice(name="Distro", value="ds"),
            app_commands.Choice(name="Language", value="lg"),
            app_commands.Choice(name="DE/WM", value="de"),
            app_commands.Choice(name="Editors", value="edit"),
            app_commands.Choice(name="Vanity", value="vanity"),
        ],
    )
    async def rolecount(
        self,
        interaction: discord.Interaction,
        which: discord.app_commands.Choice[str],
    ) -> None:
        """
        Show the number of users in each role.

        Parameters
        ----------
        interaction : discord.Interaction
            The interaction object.
        which : discord.app_commands.Choice[str]
            The role type to list.
        """
        if interaction.guild:
            # Get the roles and emojis for the selected option
            roles_emojis: list[list[int | str]] = self.roles_emoji_mapping.get(
                which.value,
                [],
            )
            # Process the roles and emojis for the selected option
            await self._process_roles(interaction, roles_emojis, which)

    async def _process_roles(
        self,
        interaction: discord.Interaction,
        roles_emojis: list[list[int | str]],
        which: discord.app_commands.Choice[str],
    ) -> None:
        """
        Process the roles and emojis for the selected option.

        Parameters
        ----------
        interaction : discord.Interaction
            The interaction object.
        roles_emojis : list[list[int | str]]
            The list of roles and emojis.
        which : discord.app_commands.Choice[str]
            The selected option.
        """
        role_data: list[tuple[discord.Role, list[int | str]]] = []

        for role_emoji in roles_emojis:
            role_id = int(role_emoji[0])

            if interaction.guild and (role := interaction.guild.get_role(role_id)):
                role_data.append((role, role_emoji))

        # Sort roles by the number of members in descending order
        sorted_roles = sorted(role_data, key=lambda x: len(x[0].members), reverse=True)

        pages: list[discord.Embed] = []

        embed = self._create_embed(interaction, which)

        role_count = 0

        for role, role_emoji in sorted_roles:
            role_count, embed = self._format_embed(
                embed,
                interaction,
                role,
                role_count,
                (str(role_emoji[0]), str(role_emoji[1])),
                which,
                pages,
            )

        if embed.fields:
            pages.append(embed)

        await self._send_response(interaction, pages)

    def _format_embed(
        self,
        embed: discord.Embed,
        interaction: discord.Interaction,
        role: discord.Role,
        role_count: int,
        role_emoji: tuple[str, str],
        which: discord.app_commands.Choice[str],
        pages: list[discord.Embed],
    ) -> tuple[int, discord.Embed]:
        """
        Format the embed with the role data.

        Parameters
        ----------
        embed : discord.Embed
            The embed to format.
        interaction : discord.Interaction
            The interaction object.
        role : discord.Role
            The role to format.
        role_count : int
            The current role count.
        role_emoji : tuple[str, str]
            The role emoji. The first element is the role ID and the second is the emoji name.
        which : discord.app_commands.Choice[str]
            The selected option.
        pages : list[discord.Embed]
            The list of embeds to send.

        Returns
        -------
        tuple[int, discord.Embed]
            The updated role count and embed.
        """
        if role_count >= 9:
            pages.append(embed)
            embed = self._create_embed(interaction, which)
            role_count = 0

        emoji = (
            discord.utils.get(self.bot.emojis, name=role_emoji[1])
            or f":{role_emoji[1]}:"
            or "❔"
        )

        embed.add_field(
            name=f"{emoji!s} {role.name}",
            value=f"{len(role.members)} users",
            inline=True,
        )

        role_count += 1

        return role_count, embed

    def _create_embed(
        self,
        interaction: discord.Interaction,
        which: discord.app_commands.Choice[str],
    ) -> discord.Embed:
        """
        Create an embed for the role data.

        Parameters
        ----------
        interaction : discord.Interaction
            The interaction object.
        which : discord.app_commands.Choice[str]
            The selected option.

        Returns
        -------
        discord.Embed
            The created embed.
        """
        return EmbedCreator.create_embed(
            bot=self.bot,
            embed_type=EmbedCreator.INFO,
            user_name=interaction.user.name,
            user_display_avatar=interaction.user.display_avatar.url,
            title=f"{which.name} Roles",
            description="Number of users in each role",
        )

    async def _send_response(
        self,
        interaction: discord.Interaction,
        pages: list[discord.Embed],
    ) -> None:
        """
        Send the response to the interaction.

        Parameters
        ----------
        interaction : discord.Interaction
            The interaction object.
        pages : list[discord.Embed]
            The list of embeds to send.
        """
        if pages:
            menu = ViewMenu(interaction, menu_type=ViewMenu.TypeEmbed)

            for page in pages:
                menu.add_page(page)

            menu.add_button(ViewButton.go_to_first_page())
            menu.add_button(ViewButton.back())
            menu.add_button(ViewButton.next())
            menu.add_button(ViewButton.go_to_last_page())
            menu.add_button(ViewButton.end_session())

            await menu.start()


async def setup(bot: Tux):
    """Set up the rolecount plugin.

    Parameters
    ----------
    bot : Tux
        The bot instance to add the cog to.
    """
    await bot.add_cog(RoleCount(bot))
