#   Copyright 2020-present Michael Hall
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

# Original @ https://github.com/unified-moderation-network/salamander/blob/ac2f9b538107daa55360cfb438b939fc03bec63f/src/bot.py#L288-L340

from typing import TypeVar

import discord

_LT = TypeVar("_LT", discord.Embed, str, covariant=True)


class InteractionListMenuView(discord.ui.View):
    def __init__(
        self, user_id: int, listmenu: list[_LT], *, timeout: float = 180, ephemeral: bool = False
    ):
        super().__init__(timeout=timeout)
        self.user_id = user_id
        self.listmenu = listmenu
        self.index: int = 0
        self.ephemeral: bool = ephemeral

    def setup_by_current_index(self) -> discord.Embed | str:
        ln = len(self.listmenu)
        index = (
            self.index % ln
        )  # this is intentional, I don't have a good example to show for why right now, but I will have a reason to want to handle an out of bounds index this way.
        self.previous.disabled = self.jump_first.disabled = index == 0
        self.nxt.disabled = self.jump_last.disabled = index == ln - 1
        return self.listmenu[index]

    async def start(self, response: discord.InteractionResponse):
        # TODO: type this to allow using followup here as well

        element = self.setup_by_current_index()

        if isinstance(element, discord.Embed):
            self.message = await response.send_message(
                embed=element, view=self, ephemeral=self.ephemeral
            )
        else:
            self.message = await response.send_message(element, view=self, ephemeral=self.ephemeral)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.user_id

    async def edit_to_current_index(self, interaction: discord.Interaction):
        element = self.setup_by_current_index()

        if isinstance(element, discord.Embed):
            await interaction.response.edit_message(embed=element, view=self)
        else:
            await interaction.response.edit_message(content=element, view=self)

    # TODO: Fix these button types

    @discord.ui.button(label="<<", style=discord.ButtonStyle.gray)
    async def jump_first(self, interaction: discord.Interaction, button: discord.ui.Button):  # type: ignore
        self.index = 0
        await self.edit_to_current_index(interaction)

    @discord.ui.button(label="<", style=discord.ButtonStyle.gray)
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):  # type: ignore
        self.index -= 1
        await self.edit_to_current_index(interaction)

    @discord.ui.button(label=">", style=discord.ButtonStyle.gray)
    async def nxt(self, interaction: discord.Interaction, button: discord.ui.Button):  # type: ignore
        self.index += 1
        await self.edit_to_current_index(interaction)

    @discord.ui.button(label=">>", style=discord.ButtonStyle.gray)
    async def jump_last(self, interaction: discord.Interaction, button: discord.ui.Button):  # type: ignore
        self.index = -1
        await self.edit_to_current_index(interaction)
