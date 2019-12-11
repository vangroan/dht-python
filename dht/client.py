"""
UDP client for connecting to a Peer, but not participating in the network.
"""
from gevent import socket

from dht.messages import MessageMeta
from dht.utils import create_logger


class DhtClient(object):

    def __init__(self):
        self._logger = create_logger(__name__)

    def send(self, address, port, message):
        """
        Send a message to the given peer address, and returns the response message.

        :param address: IP address of peer.
        :param port: Peer port to connect to.
        :param message: Message payload to send.
        :return: Response message.
        """
        with socket.socket(type=socket.SOCK_DGRAM) as sock:
            # Request
            sock.connect((address, port))
            sock.settimeout(10.0)  # seconds
            sock.send(message.marshal())

            # Response
            data, _ = sock.recvfrom(8192)
            self._logger.info("Received {}".format(data))

            # Assumes that message types are registered in message meta registry.
            # TODO: throw exception when message type is unknown, or unmarshalling fails
            enum_bytes = data[:4]
            message_enum = int.from_bytes(enum_bytes, 'big')
            message_type = MessageMeta.message_types().get(message_enum, None)
            return message_type.unmarshal(data[4:])
