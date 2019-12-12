import logging

from dht.route import NodeId
from gevent.server import DatagramServer
from dht.messages import MessageMeta
from dht.utils import create_logger

# Import concrete messages so they get registered in the meta class.
# noinspection PyUnresolvedReferences
from dht import requests


class PeerServer(DatagramServer):
    """
    Peer UDP Server

    Acts as the primary interface to this peer node.
    """

    def __init__(self, address, port, node_id=None, bootstrap=None):
        """
        Creates a new peer, with the given settings.

        Does not bind a socket yet. Call `serve_forever` to bind and listen.

        >>> PeerServer('', '9000').serve_forever()

        :param address: IP address to bind to
        :param port: Port to bind to
        :param node_id: Optional Node identifier, if this
                   peer already has a persisted identity.
        :param bootstrap: A list of (ip, port) tuples used
                          as an entry point into the network.
        """
        super().__init__('%s:%s' % (address, port))

        self._node_id = NodeId.generate() if node_id is None else node_id
        self._bootstrap = list(bootstrap) if bootstrap else list()
        self._logger = create_logger(__name__)

    @property
    def id(self):
        """Unique identifier for this node."""
        return self._node_id

    def bootstrap(self, nodes):
        """
        Joins a DHT network overlay via a physical network entry point.

        Accepts an iterable of known nodes, as (ip, port) tuples.
        """
        raise NotImplementedError()

    def start(self):
        self._logger.debug("Starting Peer %s", repr(self._node_id))

        # Print message map
        buf = []
        types = MessageMeta.message_types()
        for key in iter(types):
            buf.append(str(key))
            buf.append(" : ")
            buf.append(types[key].fullname())
            buf.append("\n")
        self._logger.debug("Message Types:\n%s", "".join(buf).strip())

        return super().start()

    def handle(self, data, address):  # pylint:disable=method-hidden
        self._logger.debug('{}:{}: got {}'.format(address[0], address[1], [hex(d) for d in data]))
        # self.socket.sendto(('Received %s bytes' %
        #                     len(data)).encode('utf-8'), address)
        try:
            self._dispatch(data, address)
        except Exception as ex:
            self._logger.exception("Exception while handling message", ex)

    def _dispatch(self, data, address):
        # TODO: Map message type class to handler.
        # TODO: Middleware chain.

        # For now message enum is at front of packet.
        enum_bytes = data[:4]
        message_enum = int.from_bytes(enum_bytes, 'big')
        message_type = MessageMeta.message_types().get(message_enum, None)
        message = message_type.unmarshal(data[4:])
        self._logger.debug("Received message %s", repr(message))

        # TODO: Dynamically dispatch to handler.
        if type(message) is requests.PingRequest:
            response = message.respond(requests.PongResponse, value=message.value)
            self.socket.sendto(response.marshal(), address)
