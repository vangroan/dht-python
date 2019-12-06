import unittest

from dht import route
from dht.route import NodeId, KBucket, Contact


class TestKBucket(unittest.TestCase):

    def test_contains(self):
        bucket = KBucket()
        bucket.add(Contact('127.0.0.1', 9090, NodeId(0x1000)))

        self.assertTrue(bucket.contains(NodeId(0x1000)))
