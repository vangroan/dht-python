
import unittest
from dht import route
from dht.route import NodeId


class IdTests(unittest.TestCase):

    def setUp(self):
        self.prev_key_size = route.KEY_SIZE_BYTES

        # Small key size for testing purposes
        route.KEY_SIZE_BYTES = 4

    def tearDown(self):
        # restore
        route.KEY_SIZE_BYTES = self.prev_key_size
        del self.prev_key_size

    def test_xor(self):
        id_1 = NodeId('00000001')
        id_2 = NodeId('00000002')

        self.assertEqual(NodeId('00000003'), id_1 ^ id_2)

    def test_has_prefix(self):
        nodeid = NodeId(0xf550000000000000000000000000000000000000)

        self.assertTrue(nodeid.has_prefix(0xf5))
        self.assertFalse(nodeid.has_prefix(0xaa))

    def test_append_bit(self):
        self.assertEqual(route._append_bit('a', 1), '15')
        self.assertEqual(route._append_bit('6', 0), '0c')
        self.assertEqual(route._append_bit('6', 1), '0d')

    def test_nth_bit(self):
        # ‭10011000011101100101010000110010‬...
        nodeid = NodeId(0x9876543200000000000000000000000000000000)

        self.assertEqual(nodeid.nth_bit(0), 1)
        self.assertEqual(nodeid.nth_bit(1), 0)
        self.assertEqual(nodeid.nth_bit(2), 0)
        self.assertEqual(nodeid.nth_bit(3), 1)
        self.assertEqual(nodeid.nth_bit(4), 1)
        self.assertEqual(nodeid.nth_bit(5), 0)
