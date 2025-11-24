"""Dependency tracking for hot reload system."""

import ast
from abc import ABC, abstractmethod
from collections import defaultdict
from pathlib import Path

from loguru import logger


class DependencyTracker(ABC):
    """Abstract base class for dependency tracking."""

    @abstractmethod
    def get_dependencies(self, module_path: Path) -> set[str]:
        """Get dependencies for a module."""

    @abstractmethod
    def get_dependents(self, module_name: str) -> set[str]:
        """Get modules that depend on the given module."""


class ClassDefinitionTracker:
    """Tracks class definitions and their changes."""

    def __init__(self) -> None:
        """Initialize the class definition tracker."""
        self._class_signatures: dict[str, dict[str, str]] = {}

    def extract_class_signatures(self, file_path: Path) -> dict[str, str]:
        """
        Extract class method signatures from a Python file.

        Returns
        -------
        dict[str, str]
            Dictionary mapping class names to their method signatures.
        """
        try:
            with file_path.open(encoding="utf-8") as f:
                source = f.read()

            tree = ast.parse(source)
            signatures: dict[str, str] = {}

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    class_methods: list[str] = []
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            # Create method signature
                            args = [arg.arg for arg in item.args.args]
                            signature = f"{item.name}({', '.join(args)})"
                            class_methods.append(signature)

                    signatures[node.name] = "\n".join(sorted(class_methods))

        except Exception as e:
            logger.warning(f"Failed to extract class signatures from {file_path}: {e}")
            return {}
        else:
            return signatures

    def has_class_changed(self, file_path: Path, class_name: str) -> bool:
        """
        Check if a class definition has changed.

        Returns
        -------
        bool
            True if the class has changed, False otherwise.
        """
        current_signatures = self.extract_class_signatures(file_path)
        file_key = str(file_path)

        if file_key not in self._class_signatures:
            self._class_signatures[file_key] = current_signatures
            return True

        old_signature = self._class_signatures[file_key].get(class_name, "")
        new_signature = current_signatures.get(class_name, "")

        if old_signature != new_signature:
            self._class_signatures[file_key] = current_signatures
            return True

        return False

    def update_signatures(self, file_path: Path) -> None:
        """Update stored signatures for a file."""
        self._class_signatures[str(file_path)] = self.extract_class_signatures(
            file_path,
        )


class DependencyGraph(DependencyTracker):
    """Tracks module dependencies using AST analysis."""

    def __init__(self, max_depth: int = 10) -> None:
        """
        Initialize the dependency graph.

        Parameters
        ----------
        max_depth : int, optional
            Maximum dependency depth to traverse, by default 10.
        """
        self.max_depth = max_depth
        self._dependencies: dict[str, set[str]] = defaultdict(set)
        self._dependents: dict[str, set[str]] = defaultdict(set)
        self._module_cache: dict[Path, set[str]] = {}

    def get_dependencies(self, module_path: Path) -> set[str]:
        """
        Get dependencies for a module using AST analysis.

        Returns
        -------
        set[str]
            Set of module dependencies.
        """
        if module_path in self._module_cache:
            return self._module_cache[module_path]

        try:
            dependencies = self._extract_imports(module_path)
            self._module_cache[module_path] = dependencies
        except Exception as e:
            logger.warning(f"Failed to extract dependencies from {module_path}: {e}")
            return set()
        else:
            return dependencies

    def _extract_imports(self, file_path: Path) -> set[str]:
        """
        Extract import statements from a Python file.

        Returns
        -------
        set[str]
            Set of imported module names.
        """
        try:
            with file_path.open(encoding="utf-8") as f:
                source = f.read()

            tree = ast.parse(source)
            imports: set[str] = set()

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.add(alias.name)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imports.add(node.module)
                    # Also add submodule imports
                    for alias in node.names:
                        if alias.name != "*":
                            imports.add(f"{node.module}.{alias.name}")

        except Exception as e:
            logger.warning(f"Failed to parse imports from {file_path}: {e}")
            return set()
        else:
            return imports

    def get_dependents(self, module_name: str) -> set[str]:
        """
        Get modules that depend on the given module.

        Returns
        -------
        set[str]
            Set of dependent module names.
        """
        return self._dependents.get(module_name, set())

    def add_dependency(self, dependent: str, dependency: str) -> None:
        """Add a dependency relationship."""
        self._dependencies[dependent].add(dependency)
        self._dependents[dependency].add(dependent)

    def remove_module(self, module_name: str) -> None:
        """Remove a module from the dependency graph."""
        # Remove as dependent
        for dep in self._dependencies.get(module_name, set()):
            self._dependents[dep].discard(module_name)

        # Remove as dependency
        for dependent in self._dependents.get(module_name, set()):
            self._dependencies[dependent].discard(module_name)

        # Clean up
        self._dependencies.pop(module_name, None)
        self._dependents.pop(module_name, None)

    def get_reload_order(self, changed_modules: set[str]) -> list[str]:
        """
        Get optimal reload order for changed modules.

        Returns
        -------
        list[str]
            List of modules in optimal reload order.
        """
        reload_order: list[str] = []
        visited: set[str] = set()

        def visit(module: str, depth: int = 0) -> None:
            """
            Visit a module and its dependencies to determine reload order.

            Parameters
            ----------
            module : str
                The module to visit.
            depth : int, optional
                Current depth in the dependency tree, by default 0.
            """
            if depth > self.max_depth:
                logger.warning(f"Max dependency depth reached for {module}")
                return

            if module in visited:
                return

            visited.add(module)

            # Visit dependencies first
            for dep in self._dependencies.get(module, set()):
                if dep in changed_modules:
                    visit(dep, depth + 1)

            if module not in reload_order:
                reload_order.append(module)

        for module in changed_modules:
            visit(module)

        return reload_order

    def clear_cache(self) -> None:
        """Clear the module cache."""
        self._module_cache.clear()
