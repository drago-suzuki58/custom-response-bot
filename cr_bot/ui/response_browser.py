import discord

from cr_bot.ui.common import PAGE_SIZE, VIEW_TIMEOUT, code_block, reject_other_user, truncate_text


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
        await view.update(interaction)


class ResponseBackButton(discord.ui.Button):
    def __init__(self, disabled: bool):
        super().__init__(label="Back to List", style=discord.ButtonStyle.secondary, disabled=disabled, row=2)

    async def callback(self, interaction: discord.Interaction) -> None:
        view: ResponseBrowserView = self.view  # type: ignore[assignment]
        view.selected_index = None
        await view.update(interaction)


class ResponsePrevButton(discord.ui.Button):
    def __init__(self, disabled: bool):
        super().__init__(label="Prev", style=discord.ButtonStyle.primary, disabled=disabled, row=2)

    async def callback(self, interaction: discord.Interaction) -> None:
        view: ResponseBrowserView = self.view  # type: ignore[assignment]
        view.page = max(0, view.page - 1)
        view.selected_index = None
        await view.update(interaction)


class ResponseNextButton(discord.ui.Button):
    def __init__(self, disabled: bool):
        super().__init__(label="Next", style=discord.ButtonStyle.primary, disabled=disabled, row=2)

    async def callback(self, interaction: discord.Interaction) -> None:
        view: ResponseBrowserView = self.view  # type: ignore[assignment]
        view.page += 1
        view.selected_index = None
        await view.update(interaction)


class ResponseCloseButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Close", style=discord.ButtonStyle.danger, row=2)

    async def callback(self, interaction: discord.Interaction) -> None:
        await interaction.response.edit_message(content="レスポンスブラウザを閉じました。", embeds=[], view=None)


class ResponseBrowserView(discord.ui.View):
    def __init__(self, responses: list[dict], owner_id: int):
        super().__init__(timeout=VIEW_TIMEOUT)
        self.responses = responses
        self.owner_id = owner_id
        self.filter_key = "all"
        self.page = 0
        self.selected_index: int | None = None
        self.rebuild_items()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id == self.owner_id:
            return True

        await reject_other_user(interaction)
        return False

    async def update(self, interaction: discord.Interaction) -> None:
        self.rebuild_items()
        await interaction.response.edit_message(embeds=self.build_embeds(), view=self)

    def rebuild_items(self) -> None:
        self.clear_items()
        entries = self.visible_entries

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

    def build_embeds(self) -> list[discord.Embed]:
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
        resp = self.responses[idx]
        trigger = str(resp.get("trigger", ""))
        response = str(resp.get("response", ""))
        flags = ", ".join(self.flags(resp)) or "plain"

        detail = discord.Embed(
            title=f"Response #{idx}",
            color=6956287,
            timestamp=discord.utils.utcnow(),
        )
        detail.add_field(name="Filter", value=f"`{FILTERS[self.filter_key]}`", inline=True)
        detail.add_field(name="Flags", value=f"`{flags}`", inline=True)
        detail.add_field(name="Trigger", value=code_block(truncate_text(trigger, 1000), "regex"), inline=False)
        detail.add_field(name="Response", value=code_block(truncate_text(response, 1000), "text"), inline=False)

        copy_ready = discord.Embed(title="Copy Ready", color=0x2ECC71)
        copy_ready.description = truncate_text(
            f"Trigger\n{code_block(trigger, 'regex')}\nResponse\n{code_block(response, 'text')}",
            4000,
        )
        return [detail, copy_ready]

    @staticmethod
    def flags(resp: dict) -> list[str]:
        response_text = str(resp.get("response", ""))
        result = []
        if "func://" in response_text:
            result.append("func")
        if "func://preset." in response_text:
            result.append("preset")
        if "func://standard." in response_text:
            result.append("standard")
        if "img://" in response_text or "imgs://" in response_text:
            result.append("image")
        return result

    @staticmethod
    def total_pages(count: int) -> int:
        if count <= 0:
            return 1
        return (count + PAGE_SIZE - 1) // PAGE_SIZE
