"""
Mail Plugin for Tux Bot.

This plugin provides email account management functionality for the ATL Discord server,
allowing administrators to create and manage email accounts through the Mailcow API.
"""

import random

import discord
import httpx
from discord import app_commands
from loguru import logger

from tux.core.base_cog import BaseCog
from tux.core.bot import Tux
from tux.core.checks import requires_command_permission
from tux.services.http_client import http_client
from tux.shared.config import CONFIG
from tux.shared.constants import HTTP_OK

MailboxData = dict[str, str | list[str]]


class Mail(BaseCog):
    """Mail plugin for managing email accounts via Mailcow API."""

    def __init__(self, bot: Tux) -> None:
        """Initialize the Mail plugin.

        Parameters
        ----------
        bot : Tux
            The bot instance to initialize the plugin with.
        """
        super().__init__(bot)
        self.api_url = CONFIG.EXTERNAL_SERVICES.MAILCOW_API_URL
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-API-Key": CONFIG.EXTERNAL_SERVICES.MAILCOW_API_KEY,
            "Authorization": f"Bearer {CONFIG.EXTERNAL_SERVICES.MAILCOW_API_KEY}",
        }
        self.default_options: dict[str, str | list[str]] = {
            "active": "1",
            "domain": "atl.tools",
            "password": "ErrorPleaseReportThis",
            "password2": "ErrorPleaseReportThis",
            "quota": "3072",
            "force_pw_update": "1",
            "tls_enforce_in": "0",
            "tls_enforce_out": "0",
            "tags": ["discord_member"],
        }

    mail = app_commands.Group(name="mail", description="Mail commands.")

    @mail.command(name="register")
    @requires_command_permission()
    async def register(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        username: str,
    ) -> None:
        """
        Register a user for mail.

        Parameters
        ----------
        interaction : discord.Interaction
            The interaction object for the command.
        member : discord.Member
            The member to register for mail.
        username : str
            The username to register for mail.
        """
        if not username.isalnum():
            await interaction.response.send_message(
                "Username must be alphanumeric and contain no spaces.",
                ephemeral=True,
            )
            return

        if interaction.guild:
            password = self._generate_password()
            mailbox_data = self._prepare_mailbox_data(username, password, member.id)

            try:
                response = await http_client.post(
                    f"{self.api_url}/add/mailbox",
                    headers=self.headers,
                    json=mailbox_data,
                    timeout=10.0,
                )

                await self._handle_response(interaction, response, member, password)

            except httpx.RequestError as exc:
                await interaction.response.send_message(
                    f"An error occurred while requesting {exc.request.url!r}.",
                    ephemeral=True,
                )
                logger.error(f"HTTP request error: {exc}")
        else:
            await interaction.response.send_message(
                "This command can only be used in a guild (server).",
                ephemeral=True,
            )

    @staticmethod
    def _generate_password() -> str:
        """
        Generate a random password for the mailbox.

        Returns
        -------
        str
            The generated password.
        """
        password = "changeme" + "".join(str(random.randint(0, 9)) for _ in range(6))
        password += "".join(random.choice("!@#$%^&*") for _ in range(4))
        return password

    def _prepare_mailbox_data(
        self,
        username: str,
        password: str,
        member_id: int,
    ) -> MailboxData:
        """
        Prepare the mailbox data for the API request.

        Parameters
        ----------
        username : str
            The username to register for mail.
        password : str
            The password to register for mail.
        member_id : int
            The ID of the member to register for mail.

        Returns
        -------
        MailboxData
            The prepared mailbox data dictionary.
        """
        mailbox_data = self.default_options.copy()

        mailbox_data.update(
            {
                "local_part": username,
                "name": username,
                "password": password,
                "password2": password,
                "tags": self.default_options["tags"] + [str(member_id)]
                if isinstance(self.default_options["tags"], list)
                else [str(member_id)],
            },
        )

        return mailbox_data

    async def _handle_response(
        self,
        interaction: discord.Interaction,
        response: httpx.Response,
        member: discord.Member,
        password: str,
    ) -> None:
        """
        Handle the response from the API request.

        Parameters
        ----------
        interaction : discord.Interaction
            The interaction object for the command.
        response : httpx.Response
            The response from the API request.
        member : discord.Member
            The member to register for mail.
        password : str
            The password to register for mail.
        """
        if response.status_code == HTTP_OK:
            result: list[dict[str, str | None]] = response.json()
            logger.info(f"Response JSON: {result}")

            if mailbox_info := self._extract_mailbox_info(result):
                await interaction.response.send_message(
                    f"Successfully registered {mailbox_info} for mail.",
                    ephemeral=True,
                )

                await self._send_dm(interaction, member, mailbox_info, password)

            else:
                await interaction.response.send_message(
                    "Failed to register the mailbox. Quota limit exceeded.",
                    ephemeral=True,
                )

        elif response.status_code == 401:
            await interaction.response.send_message(
                "Unauthorized. Check your API credentials.",
                ephemeral=True,
            )

        else:
            await interaction.response.send_message(
                f"Failed to register the requested username for mail. Status code: {response.status_code}.",
                ephemeral=True,
            )

    @staticmethod
    def _extract_mailbox_info(result: list[dict[str, str | None]]) -> str | None:
        """
        Extract the mailbox information from the response.

        Parameters
        ----------
        result : list[dict[str, str | None]]
            The response from the API request.

        Returns
        -------
        str | None
            The mailbox information.
        """
        for item in result:
            if "msg" in item:
                msg = item["msg"]

                if msg and "mailbox_added" in msg:
                    return msg[1]
                if msg and "mailbox_quota_left_exceeded" in msg:
                    return None

        return None

    @staticmethod
    async def _send_dm(
        interaction: discord.Interaction,
        member: discord.Member,
        mailbox_info: str,
        password: str,
    ) -> None:
        """
        Send a DM to the member with the mailbox information.

        Parameters
        ----------
        interaction : discord.Interaction
            The interaction object for the command.
        member : discord.Member
            The member to send the DM to.
        mailbox_info : str
            The mailbox information to send to the member.
        password : str
            The password to send to the member.
        """
        dm_message = f"""
**Your mailbox has been successfully registered!**

**Email Address**: `{mailbox_info}`
**Access Mailbox**: [mail.atl.tools](https://mail.atl.tools)
**Default Password**: ||`{password}`||

**Please change your password after logging in for the first time.**

After changing, you Ban also set up your mailbox on your mobile device or email client following the instructions provided on the mail server. Alternatively, feel free to use our webmail interface available at [mail.atl.tools/SOGo](https://mail.atl.tools/SOGo/).

If you have any questions or need assistance, please feel free to reach out to the server staff. Enjoy your new mailbox! 📬
        """
        try:
            await member.send(
                f"Hello {member.mention},\n{dm_message.strip()}",
                suppress_embeds=True,
            )

        except discord.Forbidden:
            await interaction.response.send_message(
                f"Failed to send a DM to {member.mention}. Please enable DMs from server members.",
                ephemeral=True,
            )


async def setup(bot: Tux) -> None:
    """Set up the mail plugin.

    Parameters
    ----------
    bot : Tux
        The bot instance to add the cog to.
    """
    await bot.add_cog(Mail(bot))
