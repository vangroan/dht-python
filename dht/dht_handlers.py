from handler import MessageHandler, incoming, outgoing
from requests import PingRequest, PongResponse
from utils import create_logger

logger = create_logger(__name__)


class DefaultDhtHandler(MessageHandler):

    @incoming(PingRequest)
    @outgoing(PongResponse)
    def ping(self, msg):
        logger.debug("Received Ping %d" % msg.value)

        address, port = self.context['sender']
        logger.debug("Inserting peer %s:%i" % (address, port))

        routing_table = self.context['routing_table']
        # TODO: Need sender's NodeId in order to insert

        response = msg.respond(PongResponse, value=msg.value)
        self.respond(response)
