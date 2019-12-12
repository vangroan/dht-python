"""
Concrete request message types.
"""
import random

from dht.messages import Message, Integer, NodeIdField


class PingRequest(Message):
    """
    Health check to indicate whether a peer is still available.

    Contains a random number that should be sent back in the pong response.
    """
    __message__ = 100
    value = Integer()

    @staticmethod
    def generate():
        """
        Creates a ping request with a random value.
        """
        return PingRequest(value=random.randint(0, (2 ** 32) - 1))


class PongResponse(Message):
    """
    Response to a ping request. Indicates that the peer on the other side is listening.
    """
    __message__ = 101
    value = Integer()


class FindClosestRequest(Message):
    """
    Query a peer for the node id it knows about, which is the closest to the given id.
    """
    __message__ = 200
    node_id = NodeIdField()
