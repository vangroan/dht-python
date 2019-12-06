
import unittest
from dht import route
from dht.route import NodeId


class IdTests(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_xor(self):
        id_1 = NodeId(0x01)
        id_2 = NodeId(0x02)

        self.assertEqual(NodeId(0x03), id_1 ^ id_2)

    def test_has_prefix(self):
        node_id = NodeId(0xf550000000000000000000000000000000000000)

        self.assertTrue(node_id.has_prefix(0xf5))
        self.assertFalse(node_id.has_prefix(0xaa))

    def test_append_bit(self):
        self.assertEqual(route._append_bit('a', 1), '15')
        self.assertEqual(route._append_bit('6', 0), '0c')
        self.assertEqual(route._append_bit('6', 1), '0d')

    def test_nth_bit(self):
        # ‭10011000011101100101010000110010‬...
        node_id = NodeId(0x9876543200000000000000000000000000000000)

        self.assertEqual(node_id.nth_bit(0), 1)
        self.assertEqual(node_id.nth_bit(1), 0)
        self.assertEqual(node_id.nth_bit(2), 0)
        self.assertEqual(node_id.nth_bit(3), 1)
        self.assertEqual(node_id.nth_bit(4), 1)
        self.assertEqual(node_id.nth_bit(5), 0)
