from importlib import metadata

# Dynamically get the version from pyproject.toml
__version__: str = metadata.version("tux")
