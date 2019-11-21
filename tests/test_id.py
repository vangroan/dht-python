
import unittest
from dht import route
from dht.route import Id


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
        id_1 = Id('00000001')
        id_2 = Id('00000002')

        self.assertEqual(Id('00000003'), id_1 ^ id_2)
