import random

import discord
import httpx
from discord import app_commands
from discord.ext import commands
from loguru import logger

from tux.utils.constants import Constants as CONST


class Mail(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.api_url = CONST.MAILCOW_API_URL
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-API-Key": CONST.MAILCOW_API_KEY,
            "Authorization": f"Bearer {CONST.MAILCOW_API_KEY}",
        }
        self.default_options = {
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

    @mail.command(name="register", description="Registers a user for mail.")
    @app_commands.checks.has_any_role("Root", "Admin", "Mod")
    async def register(
        self, interaction: discord.Interaction, member: discord.Member, username: str
    ) -> None:
        if not username.isalnum():
            await interaction.response.send_message(
                "Username must be alphanumeric and contain no spaces.", ephemeral=True
            )
            return

        if interaction.guild:
            mailbox_data = self.default_options.copy()
            mailbox_data["local_part"] = username
            mailbox_data["name"] = username

            # Generate 6 random numbers
            password = "changeme"
            for _ in range(6):
                password += str(random.randint(0, 9))

            # Generate 4 random special characters
            special_chars = "!@#$%^&*"
            for _ in range(4):
                password += random.choice(special_chars)

            mailbox_data["password"] = password
            mailbox_data["password2"] = password

            # Ensure tags are copied correctly and member ID is added
            tags = (
                self.default_options["tags"]
                if isinstance(self.default_options["tags"], list)
                else []
            )
            tags = tags.copy()  # Ensure it's a fresh copy of the list
            tags.append(str(member.id))
            mailbox_data["tags"] = tags

            api_path = "/add/mailbox"
            api_endpoint = self.api_url + api_path

            async with httpx.AsyncClient(timeout=10.0) as client:
                try:
                    response = await client.post(
                        api_endpoint, headers=self.headers, json=mailbox_data
                    )
                    if response.status_code == 200:
                        result = response.json()
                        logger.info(f"Response JSON: {result}")

                        # Initialize the mailbox_info as 'Unknown'
                        mailbox_info = "Unknown"

                        # Check the response for success or failure messages
                        for item in result:
                            if "msg" in item:
                                if "mailbox_added" in item["msg"]:
                                    mailbox_info = item["msg"][1]
                                    break
                                if "mailbox_quota_left_exceeded" in item["msg"]:
                                    await interaction.response.send_message(
                                        "Failed to register the mailbox. Quota limit exceeded.",
                                        ephemeral=True,
                                    )
                                    return

                        await interaction.response.send_message(
                            f"Successfully registered {mailbox_info} for mail.", ephemeral=True
                        )

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
                            await member.send(
                                f"Hello {member.mention},\n{dm_message.strip()}",
                                suppress_embeds=True,
                            )
                        except discord.Forbidden:
                            await interaction.response.send_message(
                                f"Failed to send a DM to {member.mention}. Please enable DMs from server members.",
                                ephemeral=True,
                            )

                    elif response.status_code == 401:
                        await interaction.response.send_message(
                            "Unauthorized. Check your API credentials.", ephemeral=True
                        )
                    else:
                        await interaction.response.send_message(
                            f"Failed to register {username} for mail. Status code: {response.status_code}.",
                            ephemeral=True,
                        )
                except httpx.RequestError as exc:
                    await interaction.response.send_message(
                        f"An error occurred while requesting {exc.request.url!r}.", ephemeral=True
                    )
                    logger.error(f"An error occurred while requesting, {exc}")
        else:
            await interaction.response.send_message(
                "This command can only be used in a guild (server).", ephemeral=True
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(Mail(bot))
