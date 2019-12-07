import unittest

from dht.messages import AbstractMessage, MessageDeclareError, Integer


class TestMessages(unittest.TestCase):

    def test_create(self):
        """
        Should add headers to new instance.
        """
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
            class InvalidMessage(AbstractMessage):
                # No __message__ defined
                pass

        exception = context.exception
        self.assertIsNotNone(exception, "Message declaration did not throw on invalid message type")

    # noinspection PyUnresolvedReferences
    def test_field_registry(self):
        """
        Should store an internal registry of message class fields.
        """

        class FieldsMessage(AbstractMessage):
            __message__ = 2
            one = Integer()

        self.assertIsNotNone(getattr(FieldsMessage, '__fields__', None), "Fields meta field was not set on class")
        self.assertTrue('one' in FieldsMessage.__fields__, "Field one was not found in message class field registry")

    def test_marshal(self):
        """
        Should marshal a message's header and body to a binary stream.
        """
        self.skipTest('TODO')


class FixtureMessage(AbstractMessage):
    __message__ = 1

    value = Integer()