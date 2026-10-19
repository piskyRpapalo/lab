"""Local, deterministic context selection for the lab."""

from .core import Chunk, SelectionPolicy, select_chunks
from .package import build_two_pass_package

__all__ = ["Chunk", "SelectionPolicy", "select_chunks", "build_two_pass_package"]
