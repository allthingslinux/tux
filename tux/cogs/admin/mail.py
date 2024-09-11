import random

import discord
import httpx
from discord import app_commands
from discord.ext import commands
from loguru import logger

from tux.bot import Tux
from tux.utils import checks
from tux.utils.config import CONFIG

MailboxData = dict[str, str | list[str]]


class Mail(commands.Cog):
    def __init__(self, bot: Tux) -> None:
        self.bot = bot
        self.api_url = CONFIG.MAILCOW_API_URL
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-API-Key": CONFIG.MAILCOW_API_KEY,
            "Authorization": f"Bearer {CONFIG.MAILCOW_API_KEY}",
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
    @app_commands.checks.has_any_role("Root", "Admin", "Mod")
    @checks.ac_has_pl(5)
    async def register(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        username: str,
    ) -> None:
        """
        Registers a user for mail.

        Parameters
        ----------
        interaction : discord.Interaction
            The interaction object for the command.
        member : discord.Member
            The member to register for mail.
        username : str
            The username to register for mail.

        Raises
        ------
        discord.Forbidden
            If the bot is unable to send a DM to the member.
        """
        if not username.isalnum():
            await interaction.response.send_message(
                "Username must be alphanumeric and contain no spaces.",
                ephemeral=True,
                delete_after=30,
            )
            return

        if interaction.guild:
            password = self._generate_password()
            mailbox_data = self._prepare_mailbox_data(username, password, member.id)

            async with httpx.AsyncClient(timeout=10.0) as client:
                try:
                    response = await client.post(
                        f"{self.api_url}/add/mailbox",
                        headers=self.headers,
                        json=mailbox_data,
                    )

                    await self._handle_response(interaction, response, member, password)

                except httpx.RequestError as exc:
                    await interaction.response.send_message(
                        f"An error occurred while requesting {exc.request.url!r}.",
                        ephemeral=True,
                        delete_after=30,
                    )
                    logger.error(f"HTTP request error: {exc}")
        else:
            await interaction.response.send_message(
                "This command can only be used in a guild (server).",
                ephemeral=True,
                delete_after=30,
            )

    def _generate_password(self) -> str:
        password = "changeme" + "".join(str(random.randint(0, 9)) for _ in range(6))
        password += "".join(random.choice("!@#$%^&*") for _ in range(4))
        return password

    def _prepare_mailbox_data(
        self,
        username: str,
        password: str,
        member_id: int,
    ) -> MailboxData:
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
        if response.status_code == 200:
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
            await interaction.response.send_message("Unauthorized. Check your API credentials.", ephemeral=True)

        else:
            await interaction.response.send_message(
                f"Failed to register the requested username for mail. Status code: {response.status_code}.",
                ephemeral=True,
                delete_after=30,
            )

    def _extract_mailbox_info(self, result: list[dict[str, str | None]]) -> str | None:
        for item in result:
            if "msg" in item:
                msg = item["msg"]

                if msg and "mailbox_added" in msg:
                    return msg[1]
                if msg and "mailbox_quota_left_exceeded" in msg:
                    return None

        return None

    async def _send_dm(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        mailbox_info: str,
        password: str,
    ) -> None:
        dm_message = f"""
**Your mailbox has been successfully registered!**

**Email Address**: `{mailbox_info}`
**Access Mailbox**: [mail.atl.tools](https://mail.atl.tools)
**Default Password**: ||`{password}`||

**Please change your password after logging in for the first time.**

After changing, you can also set up your mailbox on your mobile device or email client following the instructions provided on the mail server. Alternatively, feel free to use our webmail interface available at [mail.atl.tools/SOGo](https://mail.atl.tools/SOGo/).

If you have any questions or need assistance, please feel free to reach out to the server staff. Enjoy your new mailbox! 📬
        """
        try:
            await member.send(f"Hello {member.mention},\n{dm_message.strip()}", suppress_embeds=True)

        except discord.Forbidden:
            await interaction.response.send_message(
                f"Failed to send a DM to {member.mention}. Please enable DMs from server members.",
                ephemeral=True,
                delete_after=30,
            )


async def setup(bot: Tux) -> None:
    await bot.add_cog(Mail(bot))
