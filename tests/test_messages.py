import unittest

from dht.messages import Message, MessageDeclareError, Integer, MessageMeta, MessageCreateError


class TestMessages(unittest.TestCase):

    def setUp(self):
        # Ensure tests don't effect each other
        MessageMeta.flush_message_types()

    def test_create(self):
        """
        Should add headers to new instance.
        """

        # assume
        class FixtureMessage(Message):
            __message__ = 1
            value = Integer()

        # act
        msg = FixtureMessage()

        # assert
        self.assertIsNotNone(getattr(msg, 'header', None))

        header = msg.header
        self.assertIsNotNone(getattr(header, 'guid', None), "GUID header is not set")

    def test_verify_message_enum(self):
        """
        Should raise exception when a message does not have a type enum defined.
        """
        with self.assertRaises(MessageDeclareError) as context:
            class InvalidMessage(Message):
                # No __message__ defined
                pass

        exception = context.exception
        self.assertIsNotNone(exception, "Message declaration did not throw on invalid message type")

    # noinspection PyUnresolvedReferences
    def test_field_registry(self):
        """
        Should store an internal registry of message class fields.
        """

        class FieldsMessage(Message):
            __message__ = 2
            one = Integer()

        self.assertIsNotNone(getattr(FieldsMessage, '__fields__', None), "Fields meta field was not set on class")
        self.assertTrue('one' in FieldsMessage.__fields__, "Field one was not found in message class field registry")

    def test_message_type_mapping(self):
        """
        Should store mapping of message enums to message classes.
        """

        class OneMessage(Message):
            __message__ = 10000

        class TwoMessage(Message):
            __message__ = 20000

        self.assertEqual(2, len(MessageMeta.message_types()))
        self.assertEqual(OneMessage, MessageMeta.message_types()[10000])
        self.assertEqual(TwoMessage, MessageMeta.message_types()[20000])

    def test_init_basic(self):
        """
        Should assign kwargs passed to constructor to message fields.
        """

        # assume
        class FixtureMessage(Message):
            __message__ = 34
            one = Integer()
            two = Integer()

        # act
        msg = FixtureMessage(one=1, two=2)

        # assert
        self.assertEqual(1, msg.one)
        self.assertEqual(2, msg.two)

    def test_marshal(self):
        """
        Should marshal a message's header and body to a binary stream.
        """

        # assume
        class FixtureMessage(Message):
            __message__ = 567
            one = Integer()

            def __init__(self, one):
                self.one = one

        message = FixtureMessage(one=1)

        # act
        data = message.marshal()

        # assert
        self.skipTest("TODO: Determine binary layout first before it can be tested")

    def test_init_field_skip(self):
        """
        Should not overwrite fields set in the concrete message's __init__ method.
        """
        self.skipTest("TODO")

    def test_message_respond(self):
        """
        Should create a response message.
        """

        # assume
        class FirstMessage(Message):
            __message__ = 400

        class SecondMessage(Message):
            __message__ = 500
            foo = Integer()

        msg = FirstMessage()

        # act
        response = msg.respond(SecondMessage, foo=713)

        # assert
        self.assertEqual(msg.header.guid, response.header.request_guid,
                         "Response message does not contain the request GUID")
        self.assertEqual(713, response.foo, "Response message does not contain value passed via constructor")

    def test_message_respond_incorrect_type(self):
        """
        Should raise an exception when an invalid type is given as a response class.
        """

        # assume
        class FirstMessage(Message):
            __message__ = 600

        class SecondMessage(object):
            __message__ = 700
            foo = Integer()

            def __init__(self, *args, **kwargs):
                pass

        msg = FirstMessage()

        # act
        with self.assertRaises(MessageCreateError) as context:
            _response = msg.respond(SecondMessage, foo=891)

        # assert
        exception = context.exception
        self.assertIsNotNone(exception)
