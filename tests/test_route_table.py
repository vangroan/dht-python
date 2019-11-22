
import unittest

from dht import route
from dht.route import NodeId, RoutingTable


class TestroutingTable(unittest.TestCase):

    def setUp(self):
        self.prev_key_size = route.KEY_SIZE_BYTES

        # Small key size for testing purposes
        route.KEY_SIZE_BYTES = 4

    def tearDown(self):
        # restore
        route.KEY_SIZE_BYTES = self.prev_key_size
        del self.prev_key_size

    def test_first_insert(self):
        '''Should split root node when only first bucket is present.'''
        owner_id = NodeId('00000003')
        table = RoutingTable(owner_id)

        table.insert('127.0.0.1', '9001', NodeId('00000002'))
        
        
