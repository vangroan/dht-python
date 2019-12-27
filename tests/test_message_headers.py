import unittest

from dht.messages import MessageHeader


class TestMessageHeaders(unittest.TestCase):

    def test_marshal_unmarshal(self):
        # assume
        header = MessageHeader()

        # act
        data = header.marshal()
        new_header = MessageHeader.unmarshal(data)

        # assume
        self.assertEqual(header._message_type_id, new_header._message_type_id, "Message type Ids don't match")
        self.assertEqual(header._guid, new_header._guid, "GUIDs don't match")
