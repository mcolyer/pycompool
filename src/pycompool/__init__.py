"""
pycompool - Control Pentair/Compool LX3xxx pool and spa systems via RS-485.

This package provides a Python library and command-line interface for
controlling Pentair Compool LX3xxx series pool controllers.
"""

from .connection import ConnectionError
from .controller import PoolController
from .protocol import PacketType, ProtocolError

__version__ = "0.2.3"
__all__ = ["PoolController", "ProtocolError", "PacketType", "ConnectionError"]
