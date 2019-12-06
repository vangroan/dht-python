
from dht.route import NodeId
from gevent.server import DatagramServer


class PeerServer(DatagramServer):
    """
    Peer UDP Server

    Acts as the primary interface to this peer node.
    """

    def __init__(self, address, port, id=None, bootstrap=[]):
        """
        Creates a new peer, with the given settings.

        Does not bind a socket yet. Call `serve_forever` to bind and listen.

        >>> PeerServer('', '9000').serve_forever()

        :param address: IP address to bind to
        :param port: Port to bind to
        :param id: Optional Node identifier, if this
                   peer already has a persisted identity.
        :param bootstrap: A list of (ip, port) tuples used
                          as an entry point into the network.
        """
        super().__init__('%s:%s' % (address, port))

        self._id = NodeId.generate() if id is None else id
        self._bootstrap = list(bootstrap)
        print('Starting Peer %s' % repr(self._id))

    @property
    def id(self):
        """Unique identifier for this node."""
        return self._id

    def bootstrap(self, nodes):
        """
        Joins a DHT network overlay via a physical network entry point.

        Accepts an iterable of known nodes, as (ip, port) tuples.
        """
        raise NotImplementedError()

    def handle(self, data, address):  # pylint:disable=method-hidden
        print('%s:%s: got %r' % (address[0], address[1], data))
        self.socket.sendto(('Received %s bytes' %
                            len(data)).encode('utf-8'), address)


def generate_id():
    """
    Generates a new random 512-bit ID, and formats it as a hex-digest.
    """
    # TODO: Replace with Crypto safe RNG
    import random

    return ''.join(['{:02x}'.format(random.randint(0, 0xFF)) for _ in range(64)])
