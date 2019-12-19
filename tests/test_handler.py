import unittest

from dht.handler import MessageHandler, incoming
from dht.messages import Message


class HandlerTest(unittest.TestCase):

    def test_request_register(self):
        """
        Should register methods in internal handler mapping when decorated with request.
        """

        # assume
        class Msg(Message):
            __message__ = 300

        # act
        class Handler(MessageHandler):
            @incoming(Msg)
            def ping(self, msg):
                pass

        # assert
        # noinspection PyUnresolvedReferences
        self.assertEqual(Handler._handler_map.get(Msg), 'ping')

    def test_dispatch(self):
        """
        Should call registered handler method when given a message of the mapping's type.
        """

        # assume
        class Msg(Message):
            __message__ = 300

        class Handler(MessageHandler):
            def __init__(self):
                self.called = False

            @incoming(Msg)
            def ping(self, msg):
                self.called = True

        handler = Handler()

        # act
        handler.dispatch(Msg())

        # assert
        self.assertTrue(handler.called, "Handler method was not called")
