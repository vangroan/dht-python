from handler import MessageHandler, incoming, outgoing
from requests import PingRequest, PongResponse


class DefaultDhtHandler(MessageHandler):

    @incoming(PingRequest)
    @outgoing(PongResponse)
    def ping(self, msg):
        pass
