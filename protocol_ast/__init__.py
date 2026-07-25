"""On-the-fly AST discovery for unknown binary protocols."""

from .pipeline import discover_and_parse, DiscoveryResult

__all__ = ["discover_and_parse", "DiscoveryResult"]
__version__ = "0.1.0"
