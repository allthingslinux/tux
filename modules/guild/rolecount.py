import discord
from bot import Tux
from discord import app_commands
from discord.ext import commands
from reactionmenu import ViewButton, ViewMenu
from ui.embeds import EmbedCreator

# FIXME: THIS IS A ALL THINGS LINUX SPECIFIC FILE
# This will be moved to a plugin as soon as possible
# Please do not enable this cog in your bot if you are not All Things Linux

des_ids = [
    [1175177565086953523, "_kde"],
    [1175177703066968114, "_gnome"],
    [1175177036990533795, "_i3"],
    [1175222139046080582, "_hyprland"],
    [1175177087183769660, "_sway"],
    [1175243354557128765, "_xfce"],
    [1175220317174632489, "_dwm"],
    [1175177142108160121, "_bspwm"],
    [1181288708977205318, "_cinnamon"],
    [1175242546012753941, "_xmonad"],
    [1175241189935550554, "_awesome"],
    [1175245686489501726, "_mate"],
    [1175241537689489408, "_qtile"],
    [1175221470587256852, "_emacs"],
    [1175240614124732487, "_herbstluft"],
    [1175219898113331331, "_icewm"],
    [1175337897180803082, "_openbox"],
    [1175336806963744788, "_wayfire"],
    [1185972642260455445, "_berry"],
    [1192097654818226256, "_leftwm"],
    [1192149690096033882, "_budgie"],
    [1196324646170148925, "_riverwm"],
    [1212033435858898995, "_enlightenment"],
    [1212031657805221930, "_stumpwm"],
    [1232200058737397771, "_lxqt"],
]

distro_ids = [
    [1175176142899122246, "_arch"],
    [1175176866928263220, "_debian"],
    [1175176922460860517, "_fedora"],
    [1175176812293271652, "_ubuntu"],
    [1175235143707918436, "_windows"],
    [1175176279616663573, "_gentoo"],
    [1175227850119458897, "_freebsd"],
    [1175177831551086593, "_nixos"],
    [1175178088347344916, "_void"],
    [1175176981936087161, "_opensuse"],
    [1175244437530611712, "_macos"],
    [1175241975818092564, "_alpine"],
    [1175177993526726717, "_linuxmint"],
    [1175221054684286996, "_openbsd"],
    [1176533514385096714, "_bedrock"],
    [1178347402730688542, "_endeavouros"],
    [1178391378812735508, "_artix"],
    [1182152672447569972, "_slackware"],
    [1178347123905929316, "_popos"],
    [1175177750143848520, "_kisslinux"],
    [1180570700734546031, "_lfs"],
    [1191106506276479067, "_garuda"],
    [1192177499413684226, "_asahi"],
    [1207599112585740309, "_fedoraatomic"],
    [1232383833152819282, "_solus"],
    [1210000519272079411, "_redhat"],
    [1232199326722293790, "_mxlinux"],
    [1232387598107017227, "_netbsd"],
    [1232385920335089734, "_qubesos"],
    [1212028841103597679, "_plan9"],
    [1232390816312590369, "_devuan"],
    [1221123322100584518, "_zorin"],
    [1220995767813013544, "_chimera"],
    [1237701796940611635, "_antix"],
    [1237704018629885983, "_cachyos"],
    [1237702486421147698, "_rockylinux"],
    [1237701203404783698, "_nobara"],
    [1237700290732490762, "_deepin"],
    [1269381234384048169, "_vanillaos"],
]

lang_ids = [
    [1175612831996055562, "_python"],
    [1175612831861837864, "_bash"],
    [1175612831941525574, "_html"],
    [1175612831115260006, "_javascript"],
    [1175612831652139008, "_c"],
    [1175612832029609994, "_cplusplus"],
    [1175612831790534797, "_lua"],
    [1175612831631155220, "_rust"],
    [1175612831907979336, "_java"],
    [1175612831798939648, "_csharp"],
    [1178389324098699294, "_php"],
    [1175612831798931556, "_haskell"],
    [1175612831727632404, "_ruby"],
    [1175612831828295680, "_kotlin"],
    [1175739620437266443, "_go"],
    [1175612831731822734, "_lisp"],
    [1175612831920558191, "_perl"],
    [1185975879231348838, "_asm"],
    [1175612830389633164, "_ocaml"],
    [1175612831727620127, "_erlang"],
    [1175612831287218250, "_zig"],
    [1175612831878615112, "_julia"],
    [1175612831429824572, "_crystal"],
    [1175612831761182720, "_elixir"],
    [1207600618542206976, "_clojure"],
    [1232389554426876045, "_godot"],
    [1232390379337285692, "_nim"],
    [1237700521465217084, "_swift"],
]

vanity_ids = [
    [1179277471883993219, "wheel"],
    [1197348658052616254, "mag"],
    [1175237664811790366, "regional_indicator_e"],
    [1186473849294962728, "smirk_cat"],
    [1180568491527516180, "supertuxkart"],
    [1179551412070404146, "100"],
    [1183896066588950558, "rabbit"],
    [1192245668534833242, "cd"],
    [1179551519624925294, "hugging"],
    [1183897526613577818, "hdtroll"],
    [1175756229168079018, "_git"],
    [1197353868103782440, "goblin"],
    [1202544488262664262, "bar_chart"],
    [1186473904773017722, "man_mage"],
    [1208233484230074408, "ghost"],
    [1217601089721995264, "old_man"],
    [1217866697751400518, "ear_of_rice"],
    [1212039041269366854, "chess_pawn"],
]

misc_ids = [
    [1182069378636849162, "_vsc"],
    [1180571441276649613, "_nvim"],
    [1180660198428393643, "_emacs"],
    [1192140446919561247, "_gnunano"],
    [1193242175295729684, "_kate"],
    [1192135710443065345, "_micro"],
    [1193241331221405716, "_jetbrains"],
    [1185974067472380015, "_helix"],
    [1192139311919935518, "_kakoune"],
    [1187804435578093690, "_ed"],
    [1189236454153527367, "_gecko"],
    [1189236400571301958, "_chromium"],
]

# TODO: Figure out how to make rolecount work without hard coded ids


class RoleCount(commands.Cog):
    def __init__(self, bot: Tux):
        self.bot = bot
        self.roles_emoji_mapping = {
            "ds": distro_ids,
            "lg": lang_ids,
            "de": des_ids,
            "misc": misc_ids,
            "vanity": vanity_ids,
        }

    @app_commands.command(name="rolecount")
    @app_commands.describe(which="Which option to list!")
    @app_commands.choices(
        which=[
            app_commands.Choice(name="Distro", value="ds"),
            app_commands.Choice(name="Language", value="lg"),
            app_commands.Choice(name="DE/WM", value="de"),
            app_commands.Choice(name="Misc", value="misc"),
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
            roles_emojis: list[list[int | str]] = self.roles_emoji_mapping.get(which.value, [])
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

        emoji = discord.utils.get(self.bot.emojis, name=role_emoji[1]) or f":{role_emoji[1]}:" or "❔"

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
    await bot.add_cog(RoleCount(bot))
