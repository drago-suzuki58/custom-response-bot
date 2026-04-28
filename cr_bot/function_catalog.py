from dataclasses import dataclass, field
import importlib
import inspect
from pathlib import Path
import re

from loguru import logger


@dataclass(slots=True)
class FunctionMeta:
    name: str
    full_name: str
    module_name: str
    signature: str
    summary: str
    doc: str
    samples: list[str]
    source_path: str


@dataclass(slots=True)
class CatalogNode:
    id: str
    name: str
    kind: str
    path_parts: tuple[str, ...]
    children: list["CatalogNode"] = field(default_factory=list)
    meta: FunctionMeta | None = None

    @property
    def is_function(self) -> bool:
        return self.kind == "function"


class FunctionCatalog:
    def __init__(self, root_path: str = "function", root_package: str = "function"):
        self.root_path = Path(root_path)
        self.root_package = root_package
        self.root = CatalogNode(
            id="",
            name=root_package,
            kind="folder",
            path_parts=(),
        )
        self.nodes_by_id: dict[str, CatalogNode] = {}
        self.refresh()

    def refresh(self) -> None:
        self.root.children.clear()
        if not self.root_path.exists():
            logger.warning(f"Function root not found: {self.root_path}")
            self._assign_ids()
            return

        self._scan_directory(self.root_path, self.root, ())
        self._sort_tree(self.root)
        self._assign_ids()

    def get(self, node_id: str) -> CatalogNode:
        return self.nodes_by_id[node_id]

    def breadcrumb(self, node: CatalogNode) -> str:
        return " > ".join((self.root_package, *node.path_parts))

    def _scan_directory(
        self, directory: Path, parent: CatalogNode, package_parts: tuple[str, ...]
    ) -> None:
        init_file = directory / "__init__.py"
        if init_file.exists():
            self._add_module_functions(parent, package_parts)

        for child_dir in directory.iterdir():
            if not child_dir.is_dir() or self._should_skip_path(child_dir):
                continue

            child_node = CatalogNode(
                id="",
                name=child_dir.name,
                kind="package" if (child_dir / "__init__.py").exists() else "folder",
                path_parts=(*package_parts, child_dir.name),
            )
            self._scan_directory(child_dir, child_node, child_node.path_parts)
            if child_node.children:
                parent.children.append(child_node)

        for py_file in directory.glob("*.py"):
            if py_file.name == "__init__.py" or self._should_skip_path(py_file):
                continue

            module_parts = (*package_parts, py_file.stem)
            module_node = CatalogNode(
                id="",
                name=py_file.stem,
                kind="module",
                path_parts=module_parts,
            )
            self._add_module_functions(module_node, module_parts)
            if module_node.children:
                parent.children.append(module_node)

    def _add_module_functions(
        self, parent: CatalogNode, module_parts: tuple[str, ...]
    ) -> None:
        module_name = ".".join((self.root_package, *module_parts))
        try:
            module = importlib.import_module(module_name)
        except Exception as exc:
            logger.warning(f"Failed to import function module {module_name}: {exc}")
            return

        for name, func in inspect.getmembers(module, inspect.isfunction):
            if name.startswith("_") or func.__module__ != module.__name__:
                continue

            full_name = ".".join((*module_parts, name))
            parent.children.append(
                CatalogNode(
                    id="",
                    name=name,
                    kind="function",
                    path_parts=(*module_parts, name),
                    meta=self._build_function_meta(func, full_name, module_name),
                )
            )

    def _build_function_meta(
        self, func, full_name: str, module_name: str
    ) -> FunctionMeta:
        doc = inspect.getdoc(func) or ""
        summary = next((line.strip() for line in doc.splitlines() if line.strip()), "")
        samples = list(dict.fromkeys(re.findall(r"func://[^\s`]+", doc)))
        source_path = inspect.getsourcefile(func) or ""
        return FunctionMeta(
            name=func.__name__,
            full_name=full_name,
            module_name=module_name,
            signature=f"{func.__name__}{inspect.signature(func)}",
            summary=summary,
            doc=doc,
            samples=samples or [f"func://{full_name}"],
            source_path=source_path,
        )

    def _assign_ids(self) -> None:
        self.nodes_by_id.clear()

        def walk(node: CatalogNode, next_id: list[int]) -> None:
            node.id = str(next_id[0])
            next_id[0] += 1
            self.nodes_by_id[node.id] = node
            for child in node.children:
                walk(child, next_id)

        walk(self.root, [0])

    def _sort_tree(self, node: CatalogNode) -> None:
        rank = {"folder": 0, "package": 0, "module": 1, "function": 2}
        node.children.sort(key=lambda child: (rank.get(child.kind, 99), child.name))
        for child in node.children:
            self._sort_tree(child)

    @staticmethod
    def _should_skip_path(path: Path) -> bool:
        return path.name.startswith("_") or path.name == "__pycache__"
