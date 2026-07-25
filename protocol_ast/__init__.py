"""On-the-fly AST discovery for unknown binary protocols.

Keep this module import-light: Termux ships only a subset of helpers
(aes_gcm, find_keylog, pcapng_secrets, tls_keylog). Heavy exports are lazy.
"""

from __future__ import annotations

__all__ = ["discover_and_parse", "DiscoveryResult", "__version__"]
__version__ = "0.1.0"


def __getattr__(name: str):
    if name in ("discover_and_parse", "DiscoveryResult"):
        from .pipeline import DiscoveryResult, discover_and_parse

        return discover_and_parse if name == "discover_and_parse" else DiscoveryResult
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
