import discord

from cr_bot.response import ResponseManager
from cr_bot.ui.common import PAGE_SIZE, VIEW_TIMEOUT, reject_other_user, truncate_text
from cr_bot.ui.response_display import (
    build_response_copy_text,
    build_response_detail_embed,
    response_flags,
)


FILTERS = {
    "all": "All",
    "func": "Uses func://",
    "image": "Uses img://",
    "preset": "Uses preset",
    "standard": "Uses standard",
    "plain": "Plain text",
}


class ResponseFilterSelect(discord.ui.Select):
    def __init__(self, current_filter: str):
        options = [
            discord.SelectOption(
                label=label,
                value=value,
                default=value == current_filter,
            )
            for value, label in FILTERS.items()
        ]
        super().__init__(placeholder="フィルタ", options=options, row=0)

    async def callback(self, interaction: discord.Interaction) -> None:
        view: ResponseBrowserView = self.view  # type: ignore[assignment]
        view.filter_key = self.values[0]
        view.page = 0
        view.selected_index = None
        view.copy_mode = False
        view.delete_confirm_mode = False
        view.deleted_response = None
        await view.update(interaction)


class ResponseSelect(discord.ui.Select):
    def __init__(self, entries: list[tuple[int, dict]]):
        options = []
        for idx, resp in entries:
            trigger = str(resp.get("trigger", ""))
            response = str(resp.get("response", ""))
            options.append(
                discord.SelectOption(
                    label=truncate_text(f"#{idx}: {trigger}", 100),
                    value=str(idx),
                    description=truncate_text(response, 100) or "(empty)",
                )
            )

        super().__init__(placeholder="レスポンスを選択", options=options, row=1)

    async def callback(self, interaction: discord.Interaction) -> None:
        view: ResponseBrowserView = self.view  # type: ignore[assignment]
        view.selected_index = int(self.values[0])
        view.copy_mode = False
        view.delete_confirm_mode = False
        view.deleted_response = None
        view.detail_title = None
        view.detail_color = 6956287
        await view.update(interaction)


class ResponseBackButton(discord.ui.Button):
    def __init__(self, disabled: bool):
        super().__init__(label="Back to List", style=discord.ButtonStyle.secondary, disabled=disabled, row=2)

    async def callback(self, interaction: discord.Interaction) -> None:
        view: ResponseBrowserView = self.view  # type: ignore[assignment]
        view.selected_index = None
        view.copy_mode = False
        view.delete_confirm_mode = False
        view.deleted_response = None
        view.detail_title = None
        view.detail_color = 6956287
        await view.update(interaction)


class ResponsePrevButton(discord.ui.Button):
    def __init__(self, disabled: bool):
        super().__init__(label="Prev", style=discord.ButtonStyle.primary, disabled=disabled, row=2)

    async def callback(self, interaction: discord.Interaction) -> None:
        view: ResponseBrowserView = self.view  # type: ignore[assignment]
        view.page = max(0, view.page - 1)
        view.selected_index = None
        view.copy_mode = False
        view.delete_confirm_mode = False
        view.deleted_response = None
        await view.update(interaction)


class ResponseNextButton(discord.ui.Button):
    def __init__(self, disabled: bool):
        super().__init__(label="Next", style=discord.ButtonStyle.primary, disabled=disabled, row=2)

    async def callback(self, interaction: discord.Interaction) -> None:
        view: ResponseBrowserView = self.view  # type: ignore[assignment]
        view.page += 1
        view.selected_index = None
        view.copy_mode = False
        view.delete_confirm_mode = False
        view.deleted_response = None
        await view.update(interaction)


class ResponseCloseButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Close", style=discord.ButtonStyle.danger, row=2)

    async def callback(self, interaction: discord.Interaction) -> None:
        await interaction.response.edit_message(content="レスポンスブラウザを閉じました。", embeds=[], view=None)


class ResponseCopyButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Copy", style=discord.ButtonStyle.success, row=0)

    async def callback(self, interaction: discord.Interaction) -> None:
        view: ResponseBrowserView = self.view  # type: ignore[assignment]
        view.copy_mode = True
        await view.update(interaction)


class ResponseBackToDetailButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Back to Detail", style=discord.ButtonStyle.secondary, row=0)

    async def callback(self, interaction: discord.Interaction) -> None:
        view: ResponseBrowserView = self.view  # type: ignore[assignment]
        view.copy_mode = False
        await view.update(interaction)


class ResponseEditButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Edit", style=discord.ButtonStyle.primary, row=0)

    async def callback(self, interaction: discord.Interaction) -> None:
        view: ResponseBrowserView = self.view  # type: ignore[assignment]
        if view.selected_index is None:
            await interaction.response.send_message("編集対象が選択されていません。", ephemeral=True)
            return

        try:
            resp = view.responses[view.selected_index]
        except IndexError:
            await interaction.response.send_message("編集対象が見つかりません。", ephemeral=True)
            return

        await interaction.response.send_modal(ResponseEditModal(view, view.selected_index, resp))


class ResponseDeleteButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Delete", style=discord.ButtonStyle.danger, row=0)

    async def callback(self, interaction: discord.Interaction) -> None:
        view: ResponseBrowserView = self.view  # type: ignore[assignment]
        view.copy_mode = False
        view.delete_confirm_mode = True
        await view.update(interaction)


class ResponseConfirmDeleteButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Confirm Delete", style=discord.ButtonStyle.danger, row=0)

    async def callback(self, interaction: discord.Interaction) -> None:
        view: ResponseBrowserView = self.view  # type: ignore[assignment]
        if view.selected_index is None:
            await interaction.response.send_message("削除対象が選択されていません。", ephemeral=True)
            return

        try:
            deleted_response = view.responses[view.selected_index]
            deleted_id = view.selected_index
            view.response_manager.remove(view.selected_index)
        except IndexError:
            await interaction.response.send_message("削除対象が見つかりません。", ephemeral=True)
            return

        view.deleted_response = (deleted_id, deleted_response)
        view.selected_index = None
        view.copy_mode = False
        view.delete_confirm_mode = False
        view.detail_title = None
        view.detail_color = 6956287
        view.ensure_page_in_range()
        await view.update(interaction)


class ResponseCancelDeleteButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Cancel", style=discord.ButtonStyle.secondary, row=0)

    async def callback(self, interaction: discord.Interaction) -> None:
        view: ResponseBrowserView = self.view  # type: ignore[assignment]
        view.delete_confirm_mode = False
        await view.update(interaction)


class ResponseEditModal(discord.ui.Modal):
    def __init__(self, view: "ResponseBrowserView", idx: int, resp: dict):
        super().__init__(title=f"Edit Response #{idx}")
        self.browser_view = view
        self.idx = idx
        self.trigger_input = discord.ui.TextInput(
            label="Trigger",
            style=discord.TextStyle.paragraph,
            default=str(resp.get("trigger", ""))[:4000],
            max_length=4000,
            required=True,
        )
        self.response_input = discord.ui.TextInput(
            label="Response",
            style=discord.TextStyle.paragraph,
            default=str(resp.get("response", ""))[:4000],
            max_length=4000,
            required=True,
        )
        self.add_item(self.trigger_input)
        self.add_item(self.response_input)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        try:
            self.browser_view.response_manager.update(
                self.idx,
                str(self.trigger_input.value),
                str(self.response_input.value),
            )
        except IndexError:
            await interaction.response.send_message("更新対象が見つかりません。", ephemeral=True)
            return

        self.browser_view.selected_index = self.idx
        self.browser_view.copy_mode = False
        self.browser_view.delete_confirm_mode = False
        self.browser_view.deleted_response = None
        self.browser_view.detail_title = "Response Updated"
        self.browser_view.detail_color = 0x2ECC71
        await self.browser_view.update(interaction)


class AddResponseModal(discord.ui.Modal):
    def __init__(self, response_manager: ResponseManager, owner_id: int):
        super().__init__(title="Add Response")
        self.response_manager = response_manager
        self.owner_id = owner_id
        self.trigger_input = discord.ui.TextInput(
            label="Trigger",
            style=discord.TextStyle.paragraph,
            max_length=4000,
            required=True,
        )
        self.response_input = discord.ui.TextInput(
            label="Response",
            style=discord.TextStyle.paragraph,
            max_length=4000,
            required=True,
        )
        self.add_item(self.trigger_input)
        self.add_item(self.response_input)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        new_id = len(self.response_manager.list())
        self.response_manager.add(
            str(self.trigger_input.value),
            str(self.response_input.value),
        )
        added_response = self.response_manager.get(new_id)
        view = AddedResponseView(new_id, added_response, self.owner_id)
        await interaction.response.send_message(
            content=view.build_content(),
            embeds=view.build_embeds(),
            view=view,
            ephemeral=True,
        )


class AddedResponseCopyButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Copy", style=discord.ButtonStyle.success, row=0)

    async def callback(self, interaction: discord.Interaction) -> None:
        view: AddedResponseView = self.view  # type: ignore[assignment]
        view.copy_mode = True
        await view.update(interaction)


class AddedResponseBackToDetailButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Back to Detail", style=discord.ButtonStyle.secondary, row=0)

    async def callback(self, interaction: discord.Interaction) -> None:
        view: AddedResponseView = self.view  # type: ignore[assignment]
        view.copy_mode = False
        await view.update(interaction)


class AddedResponseCloseButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Close", style=discord.ButtonStyle.danger, row=0)

    async def callback(self, interaction: discord.Interaction) -> None:
        await interaction.response.edit_message(content="レスポンス追加結果を閉じました。", embeds=[], view=None)


class AddedResponseView(discord.ui.View):
    def __init__(self, idx: int, resp: dict, owner_id: int):
        super().__init__(timeout=VIEW_TIMEOUT)
        self.idx = idx
        self.resp = resp
        self.owner_id = owner_id
        self.copy_mode = False
        self.rebuild_items()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id == self.owner_id:
            return True

        await reject_other_user(interaction)
        return False

    async def update(self, interaction: discord.Interaction) -> None:
        self.rebuild_items()
        await interaction.response.edit_message(
            content=self.build_content(), embeds=self.build_embeds(), view=self
        )

    def rebuild_items(self) -> None:
        self.clear_items()
        if self.copy_mode:
            self.add_item(AddedResponseBackToDetailButton())
            self.add_item(AddedResponseCloseButton())
            return

        self.add_item(AddedResponseCopyButton())
        self.add_item(AddedResponseCloseButton())

    def build_content(self) -> str | None:
        if not self.copy_mode:
            return None

        return build_response_copy_text(self.resp)

    def build_embeds(self) -> list[discord.Embed]:
        if self.copy_mode:
            return []

        embed = build_response_detail_embed(
            self.idx,
            self.resp,
            title="Response Added",
            color=0x2ECC71,
        )
        embed.set_footer(text="/list_responses からも確認できます。")
        return [embed]


class ResponseBrowserView(discord.ui.View):
    def __init__(self, response_manager: ResponseManager, owner_id: int):
        super().__init__(timeout=VIEW_TIMEOUT)
        self.response_manager = response_manager
        self.owner_id = owner_id
        self.filter_key = "all"
        self.page = 0
        self.selected_index: int | None = None
        self.copy_mode = False
        self.delete_confirm_mode = False
        self.deleted_response: tuple[int, dict] | None = None
        self.detail_title: str | None = None
        self.detail_color = 6956287
        self.rebuild_items()

    @property
    def responses(self) -> list[dict]:
        return self.response_manager.list()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id == self.owner_id:
            return True

        await reject_other_user(interaction)
        return False

    async def update(self, interaction: discord.Interaction) -> None:
        self.rebuild_items()
        await interaction.response.edit_message(
            content=self.build_content(), embeds=self.build_embeds(), view=self
        )

    def rebuild_items(self) -> None:
        self.clear_items()
        entries = self.visible_entries

        if self.copy_mode:
            self.add_item(ResponseBackToDetailButton())
            self.add_item(ResponseCloseButton())
            return

        if self.deleted_response is not None:
            self.add_item(ResponseBackButton(disabled=False))
            self.add_item(ResponseCloseButton())
            return

        if self.delete_confirm_mode:
            self.add_item(ResponseConfirmDeleteButton())
            self.add_item(ResponseCancelDeleteButton())
            self.add_item(ResponseCloseButton())
            return

        if self.selected_index is not None:
            self.add_item(ResponseCopyButton())
            self.add_item(ResponseEditButton())
            self.add_item(ResponseDeleteButton())
            self.add_item(ResponseBackButton(disabled=False))
            self.add_item(ResponseCloseButton())
            return

        self.add_item(ResponseFilterSelect(self.filter_key))
        if entries:
            self.add_item(ResponseSelect(entries))

        self.add_item(ResponseBackButton(disabled=self.selected_index is None))
        self.add_item(ResponsePrevButton(disabled=self.page <= 0))
        self.add_item(ResponseNextButton(disabled=not self.has_next_page))
        self.add_item(ResponseCloseButton())

    @property
    def filtered_entries(self) -> list[tuple[int, dict]]:
        return [
            (idx, resp)
            for idx, resp in enumerate(self.responses)
            if self.matches_filter(resp)
        ]

    @property
    def visible_entries(self) -> list[tuple[int, dict]]:
        start = self.page * PAGE_SIZE
        return self.filtered_entries[start : start + PAGE_SIZE]

    @property
    def has_next_page(self) -> bool:
        return (self.page + 1) * PAGE_SIZE < len(self.filtered_entries)

    def ensure_page_in_range(self) -> None:
        max_page = self.total_pages(len(self.filtered_entries)) - 1
        self.page = min(self.page, max(0, max_page))

    def matches_filter(self, resp: dict) -> bool:
        response_text = str(resp.get("response", ""))
        if self.filter_key == "all":
            return True
        if self.filter_key == "func":
            return "func://" in response_text
        if self.filter_key == "image":
            return "img://" in response_text or "imgs://" in response_text
        if self.filter_key == "preset":
            return "func://preset." in response_text
        if self.filter_key == "standard":
            return "func://standard." in response_text
        if self.filter_key == "plain":
            return not any(token in response_text for token in ("func://", "img://", "imgs://"))
        return True

    def build_content(self) -> str | None:
        if not self.copy_mode or self.selected_index is None:
            return None

        resp = self.responses[self.selected_index]
        return build_response_copy_text(resp)

    def build_embeds(self) -> list[discord.Embed]:
        if self.copy_mode:
            return []

        if self.deleted_response is not None:
            deleted_id, deleted_response = self.deleted_response
            embed = build_response_detail_embed(
                deleted_id,
                deleted_response,
                title="Response Deleted",
                color=0xE74C3C,
            )
            embed.set_footer(text="削除後は後続のIDが詰まります。")
            return [embed]

        if self.delete_confirm_mode and self.selected_index is not None:
            embed = build_response_detail_embed(
                self.selected_index,
                self.responses[self.selected_index],
                title="Confirm Delete",
                color=0xE74C3C,
            )
            embed.description = "このレスポンスを削除します。操作は取り消せません。"
            return [embed]

        if self.selected_index is not None:
            return self._build_detail_embeds(self.selected_index)

        return [self._build_list_embed()]

    def _build_list_embed(self) -> discord.Embed:
        entries = self.visible_entries
        filtered_count = len(self.filtered_entries)
        embed = discord.Embed(
            title="Response Browser",
            color=6956287,
            timestamp=discord.utils.utcnow(),
        )
        embed.add_field(name="Filter", value=f"`{FILTERS[self.filter_key]}`", inline=True)
        embed.add_field(name="Count", value=str(filtered_count), inline=True)
        embed.add_field(name="Page", value=f"{self.page + 1} / {self.total_pages(filtered_count)}", inline=True)

        if not entries:
            embed.description = "表示できるレスポンスはありません。"
            return embed

        lines = []
        for idx, resp in entries:
            trigger = truncate_text(str(resp.get("trigger", "")), 80)
            response = truncate_text(str(resp.get("response", "")), 100)
            flags = ", ".join(self.flags(resp)) or "plain"
            lines.append(f"#{idx} `{flags}`\nTrigger: `{trigger}`\nResponse: {response}")

        embed.description = truncate_text("\n\n".join(lines), 4000)
        return embed

    def _build_detail_embeds(self, idx: int) -> list[discord.Embed]:
        return [
            build_response_detail_embed(
                idx,
                self.responses[idx],
                title=self.detail_title,
                color=self.detail_color,
                filter_label=FILTERS[self.filter_key],
            )
        ]

    @staticmethod
    def flags(resp: dict) -> list[str]:
        return response_flags(resp)

    @staticmethod
    def total_pages(count: int) -> int:
        if count <= 0:
            return 1
        return (count + PAGE_SIZE - 1) // PAGE_SIZE
