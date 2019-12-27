import unittest
from copy import deepcopy
from uuid import UUID

from dht.messages import Message, MessageDeclareError, Integer, MessageMeta, MessageCreateError, NodeIdField, GuidField
from dht.route import NodeId


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

    def test_new_default(self):
        """
        Should assign default values to fields of new message instance.
        """

        # assume
        class DefaultMessage(Message):
            __message__ = 34
            integer = Integer()
            node_id = NodeIdField()

        # act
        msg = DefaultMessage()

        # assert
        self.assertEqual(Integer().default_value, msg.integer)
        self.assertEqual(NodeIdField().default_value, msg.node_id)

    def test_marshal(self):
        """
        Should marshal a message's header and body to a binary array.
        """

        # assume
        class FixtureMessage(Message):
            __message__ = 567  #
            one = Integer()  # 4-bytes
            two = GuidField()  # 16-bytes
            three = NodeIdField()  # 20-bytes

        message = FixtureMessage(one=1, two=UUID(int=255), three=NodeId(12345))

        # act
        data = message.marshal()

        # assert
        # NOTE: Binary format not considered complete yet
        self.assertEqual([0, 0, 2, 55], list(data[:4]))  # message type id
        self.assertEqual([0, 0, 0, 1], list(data[4:8]))  # one
        self.assertEqual([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 255], list(data[8:24]))  # two
        self.assertEqual([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 48, 57], list(data[24:44]))  # three

    def test_unmarshal(self):
        """
        Should unmarshal a message's header and body from a binary array.
        """

        # assume
        class FixtureMessage(Message):
            __message__ = 567  #
            one = Integer()

            def __init__(self, one):
                self.one = one

        data = [0, 0, 2, 55, 0, 0, 0, 1]

        # act
        message = FixtureMessage.unmarshal(data[4:])

        # assert
        # NOTE: Binary format not considered complete yet
        self.assertEqual(1, message.one)

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
            node_id = NodeIdField()

        msg = FirstMessage()

        # act
        response = msg.respond(SecondMessage, foo=713, node_id=NodeId(765))

        # assert
        self.assertEqual(msg.header.guid, response.header.request_guid,
                         "Response message does not contain the request GUID")
        self.assertEqual(713, response.foo, "Response message does not contain value passed via constructor")
        self.assertEqual(NodeId(765), response.node_id,
                         "Response message does not contain value passed via constructor")

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

    def test_node_id_field_marshal(self):
        """
        Should correctly marshal and unmarshal a node id.
        """
        # assume
        node_id = NodeId(947)
        field = NodeIdField()

        # act
        data = field.marshal(deepcopy(node_id))  # copy to ensure no sneaky mutation >_>
        node_id_back, _size = field.unmarshal(data)

        # assert
        self.assertEqual(NodeId(947), node_id_back, "Unmarshalled node id does not match original value")

    def test_extract_message_type(self):
        """
        Should extract the message type from bytes.
        """

        # assume
        class Msg(Message):
            __message__ = 4567

        data = Msg().marshal()

        # act
        message_type = Message.extract_message_type(data)

        # assert
        self.assertIsNotNone(message_type, "Message type not found")
        self.assertEqual(message_type, Msg, "Unexpected message type extracted")
