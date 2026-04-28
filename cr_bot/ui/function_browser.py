import discord

from cr_bot.function_catalog import CatalogNode, FunctionCatalog
from cr_bot.ui.common import PAGE_SIZE, VIEW_TIMEOUT, code_block, reject_other_user, truncate_text


class FunctionNodeSelect(discord.ui.Select):
    def __init__(self, entries: list[CatalogNode]):
        options = []
        for node in entries:
            icon = {"folder": "📁", "package": "📦", "module": "📄", "function": "ƒ"}.get(
                node.kind, "•"
            )
            description = node.kind
            if node.meta is not None and node.meta.summary:
                description = node.meta.summary

            options.append(
                discord.SelectOption(
                    label=truncate_text(f"{icon} {node.name}", 100),
                    value=node.id,
                    description=truncate_text(description, 100),
                )
            )

        super().__init__(placeholder="項目を選択", options=options, row=0)

    async def callback(self, interaction: discord.Interaction) -> None:
        view: FunctionBrowserView = self.view  # type: ignore[assignment]
        view.current_node_id = self.values[0]
        view.page = 0
        await view.update(interaction)


class FunctionBackButton(discord.ui.Button):
    def __init__(self, disabled: bool):
        super().__init__(label="Back", style=discord.ButtonStyle.secondary, disabled=disabled, row=1)

    async def callback(self, interaction: discord.Interaction) -> None:
        view: FunctionBrowserView = self.view  # type: ignore[assignment]
        parent = view.parent_node(view.current_node)
        if parent is not None:
            view.current_node_id = parent.id
            view.page = 0
        await view.update(interaction)


class FunctionRootButton(discord.ui.Button):
    def __init__(self, disabled: bool):
        super().__init__(label="Root", style=discord.ButtonStyle.secondary, disabled=disabled, row=1)

    async def callback(self, interaction: discord.Interaction) -> None:
        view: FunctionBrowserView = self.view  # type: ignore[assignment]
        view.current_node_id = view.catalog.root.id
        view.page = 0
        await view.update(interaction)


class FunctionPrevButton(discord.ui.Button):
    def __init__(self, disabled: bool):
        super().__init__(label="Prev", style=discord.ButtonStyle.primary, disabled=disabled, row=1)

    async def callback(self, interaction: discord.Interaction) -> None:
        view: FunctionBrowserView = self.view  # type: ignore[assignment]
        view.page = max(0, view.page - 1)
        await view.update(interaction)


class FunctionNextButton(discord.ui.Button):
    def __init__(self, disabled: bool):
        super().__init__(label="Next", style=discord.ButtonStyle.primary, disabled=disabled, row=1)

    async def callback(self, interaction: discord.Interaction) -> None:
        view: FunctionBrowserView = self.view  # type: ignore[assignment]
        view.page += 1
        await view.update(interaction)


class FunctionCloseButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Close", style=discord.ButtonStyle.danger, row=1)

    async def callback(self, interaction: discord.Interaction) -> None:
        await interaction.response.edit_message(content="関数ブラウザを閉じました。", embeds=[], view=None)


class FunctionBrowserView(discord.ui.View):
    def __init__(self, catalog: FunctionCatalog, owner_id: int):
        super().__init__(timeout=VIEW_TIMEOUT)
        self.catalog = catalog
        self.owner_id = owner_id
        self.current_node_id = catalog.root.id
        self.page = 0
        self.rebuild_items()

    @property
    def current_node(self) -> CatalogNode:
        return self.catalog.get(self.current_node_id)

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
        node = self.current_node
        children = self.visible_children
        parent = self.parent_node(node)

        if children:
            self.add_item(FunctionNodeSelect(children))

        self.add_item(FunctionBackButton(disabled=parent is None))
        self.add_item(FunctionRootButton(disabled=node.id == self.catalog.root.id))
        self.add_item(FunctionPrevButton(disabled=self.page <= 0 or node.is_function))
        self.add_item(FunctionNextButton(disabled=not self.has_next_page or node.is_function))
        self.add_item(FunctionCloseButton())

    @property
    def visible_children(self) -> list[CatalogNode]:
        if self.current_node.is_function:
            return []

        start = self.page * PAGE_SIZE
        return self.current_node.children[start : start + PAGE_SIZE]

    @property
    def has_next_page(self) -> bool:
        node = self.current_node
        return (self.page + 1) * PAGE_SIZE < len(node.children)

    def parent_node(self, node: CatalogNode) -> CatalogNode | None:
        if not node.path_parts:
            return None

        parent_path = node.path_parts[:-1]
        for candidate in self.catalog.nodes_by_id.values():
            if candidate.path_parts == parent_path:
                return candidate

        return None

    def build_embeds(self) -> list[discord.Embed]:
        node = self.current_node
        if node.is_function:
            return self._build_function_embeds(node)

        return [self._build_container_embed(node)]

    def _build_container_embed(self, node: CatalogNode) -> discord.Embed:
        embed = discord.Embed(
            title="Function Browser",
            color=6956287,
            timestamp=discord.utils.utcnow(),
        )
        embed.add_field(name="Breadcrumb", value=f"`{self.catalog.breadcrumb(node)}`", inline=False)
        embed.add_field(name="Children", value=str(len(node.children)), inline=True)
        embed.add_field(name="Page", value=f"{self.page + 1} / {self.total_pages(node)}", inline=True)

        if not node.children:
            embed.description = "この階層に表示できる関数はありません。"
            return embed

        lines = []
        start = self.page * PAGE_SIZE
        for offset, child in enumerate(self.visible_children, start=1):
            icon = {"folder": "📁", "package": "📦", "module": "📄", "function": "ƒ"}.get(
                child.kind, "•"
            )
            label = f"{start + offset}. {icon} `{child.name}` ({child.kind})"
            if child.meta is not None and child.meta.summary:
                label += f" - {truncate_text(child.meta.summary, 80)}"
            lines.append(label)

        embed.description = "\n".join(lines)
        return embed

    def _build_function_embeds(self, node: CatalogNode) -> list[discord.Embed]:
        meta = node.meta
        if meta is None:
            return [discord.Embed(title="Function Browser", description="関数情報がありません。")]

        detail = discord.Embed(
            title=f"Function: {meta.full_name}",
            color=6956287,
            timestamp=discord.utils.utcnow(),
        )
        detail.add_field(name="Breadcrumb", value=f"`{self.catalog.breadcrumb(node)}`", inline=False)
        detail.add_field(name="Signature", value=code_block(meta.signature, "python"), inline=False)
        if meta.summary:
            detail.add_field(name="Summary", value=truncate_text(meta.summary, 1024), inline=False)
        if meta.doc:
            detail.add_field(name="Docstring", value=truncate_text(meta.doc, 1024), inline=False)
        if meta.source_path:
            detail.add_field(name="Source", value=f"`{meta.source_path}`", inline=False)

        copy_ready = discord.Embed(title="Copy Ready", color=0x2ECC71)
        copy_ready.description = code_block(truncate_text("\n".join(meta.samples), 3900), "text")
        return [detail, copy_ready]

    @staticmethod
    def total_pages(node: CatalogNode) -> int:
        if not node.children:
            return 1
        return (len(node.children) + PAGE_SIZE - 1) // PAGE_SIZE
