"""
Concrete request message types.
"""
from dht.messages import AbstractMessage


class PingRequest(AbstractMessage):
    """
    Health check to indicate whether a peer is still available.
    """
    __message__ = 100


class PongResponse(AbstractMessage):
    """
    Response to a ping request. Indicates that the peer on the other side is listening.
    """
    __message__ = 101
