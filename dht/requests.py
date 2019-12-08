"""
Concrete request message types.
"""
import random

from dht.messages import Message, Integer


class PingRequest(Message):
    """
    Health check to indicate whether a peer is still available.

    Contains a random number that should be sent back in the pong response.
    """
    __message__ = 100
    value = Integer()

    def __init__(self, *args, **kwargs):
        super().__init__()

        self.value = random.randint(0, (2**32) - 1)


class PongResponse(Message):
    """
    Response to a ping request. Indicates that the peer on the other side is listening.
    """
    __message__ = 101
    value = Integer()
