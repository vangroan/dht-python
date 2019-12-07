import unittest
from datetime import datetime

from dht.route import NodeId, KBucket, Contact


class TestKBucket(unittest.TestCase):

    def test_contains(self):
        bucket = KBucket()
        bucket.add(Contact('127.0.0.1', 9090, NodeId(0x1000)))

        self.assertTrue(bucket.contains(NodeId(0x1000)))

    def test_sort(self):
        """
        Should sort contacts by last seen datetime.
        """
        # assume
        bucket = KBucket()
        bucket.add(Contact(None, None, NodeId(7)))
        bucket.add(Contact(None, None, NodeId(3)))
        bucket.add(Contact(None, None, NodeId(1)))

        bucket.get(NodeId(1)).last_seen = datetime(2019, 9, 2)
        bucket.get(NodeId(7)).last_seen = datetime(2019, 9, 3)
        bucket.get(NodeId(3)).last_seen = datetime(2019, 10, 1)

        # act
        bucket.sort()

        # assert
        self.assertEqual(NodeId(3), bucket._contacts[-1].node_id, )
