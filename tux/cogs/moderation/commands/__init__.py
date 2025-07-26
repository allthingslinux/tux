"""Import all moderation command modules so their metaclasses register them."""
from importlib import import_module
from pkgutil import iter_modules
from pathlib import Path

_pkg_path = Path(__file__).parent
for _finder, _name, _is_pkg in iter_modules([str(_pkg_path)]):
    if _name.startswith("__"):
        continue
    import_module(f"{__name__}.{_name}")

del import_module, iter_modules, Path, _pkg_path