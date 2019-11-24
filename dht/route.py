
import math
from array import array
from datetime import datetime
from copy import deepcopy

KEY_SIZE_BITS = 512
KEY_SIZE_BYTES = 64


class NodeId(object):
    __slots__ = ('_data',)

    def __init__(self, data):
        if isinstance(data, str):
            self._data = NodeId._parse(data)
        elif not isinstance(data, array):
            raise TypeError('Id data must be array of unsigned bytes')
        else:
            self._data = data

    @staticmethod
    def generate():
        '''
        Generates a new random 512-bit ID, and formats it as a hex-digest.
        '''
        # TODO: Replace with Crypto safe RNG
        import random

        # 64 bytes * 8 bits = 512 bits
        data = array('B', [random.randint(0, 0xFF)
                           for _ in range(KEY_SIZE_BYTES)])  # Unsigned Bytes
        return NodeId(data)

    @staticmethod
    def _parse(str_data):
        '''
        Given a hex digest string, return ID data in byte array form.
        '''

        # Each byte is represented by 2 hex digits
        if len(str_data) != KEY_SIZE_BYTES * 2:
            raise ValueError(
                'hex digest is incorrect length to be %d-bit ID' % (KEY_SIZE_BYTES * 8))

        result = array('B')

        for i in range(KEY_SIZE_BYTES):
            result.append(int(str_data[i:i+2], 16))

        return result

    @property
    def raw_data(self):
        '''
        Byte array representation of internal data.
        '''
        return deepcopy(self._data)

    @property
    def hex_digest(self):
        '''
        Hex digest representation of internal data.
        '''
        return ''.join(('{:02x}'.format(b) for b in self._data))

    def has_prefix(self, prefix: str):
        '''
        Checks whether the node ID starts with the given prefix.

        The prefix must be supplied as a hex digest.
        '''
        i, j = 0, 0
        while i < len(prefix) and j < KEY_SIZE_BYTES:
            if int(prefix[i:i+2], 16) != self._data[j]:
                return False
            i += 2
            j += 1
        return True

    def nth_bit(self, n: int):
        '''
        Return the n-th bit of this ID, starting from the most significant bit.
        '''
        i = math.floor(n / 8)  # each element is an 8-bit byte
        r = 7 - (n % 8)  # bit index inside byte element
        return (self._data[i] >> r) & 0x01

    def __xor__(self, rhs):
        result = array('B', [0 for _ in range(KEY_SIZE_BYTES)])
        for i in range(KEY_SIZE_BYTES):
            result[i] = self._data[i] ^ rhs._data[i]  # pylint: disable=protected-access
        return NodeId(result)

    def __repr__(self):
        return "%s('%s')" % (self.__class__.__name__, self.hex_digest)

    def __str__(self):
        return self.hex_digest

    def __eq__(self, rhs):
        if rhs is None:
            return False

        for i in range(KEY_SIZE_BYTES):
            if self._data[i] != rhs._data[i]:  # pylint: disable=protected-access
                return False

        return True


ROOT_INDEX = 0


class RoutingTable:

    def __init__(self, owner_id):
        # Routing table must know the identity of its
        # own node, in order to make decisions on whether
        # to split buckets.
        self._owner_id = owner_id

        # Initial state is one k-bucket at the root.
        bucket = KBucket.default()
        bucket.add(Contact(None, None, owner_id))
        self._root = bucket

        # Maximum number of contacts allowed in a k-bucket.
        self._ksize = 20

        # Maximum number of shared prefix bits allowed to be shared
        # between contacts inside the same bucket.
        self._depth = 5

    def insert(self, address, port, nodeid):
        self._insert(self._root, Contact(address, port, nodeid))

    def _insert(self, node, contact, level=0):
        '''
        Internal recursive insert method.
        '''

        if isinstance(node, KBucket):
            # Always split when encountering the owner node
            if node.contains(self._owner_id):
                pass

    def _split(self, bucket):
        '''
        Accepts a k-bucket, splits it into two new buckets, distributes
        the contacts correctly between them, and returns a new branch node.
        '''
        (left, right) = bucket.split()
        return (left, right)

    def find(self, nodeid: NodeId):
        return self._find(nodeid, self._root)

    def _find(self, nodeid, node, level=0):
        if isinstance(node, KBucket):
            # Reached leaf
            if len(node.contacts) > 0:
                # TODO: Return the most recently seen contact
                return node.contacts[0]
            else:
                return None
        elif isinstance(node, Node):
            # Determine down which path we should search
            if nodeid.nth_bit(level) == 1:
                return self._find(nodeid, node.left, level+1)
            elif nodeid.nth_bit(level) == 0:
                return self._find(nodeid, node.right, level+1)


class KBucket:
    '''
    Container for node contacts.

    Leaf node of binary tree.
    '''
    __slots__ = ('_low', '_high', '_contacts')

    def __init__(self, low, high):
        self._low = min(low, high)
        self._high = max(low, high)
        self._contacts = []

    @staticmethod
    def default():
        '''
        Creates a default bucket that covers the whole key space.
        '''
        return KBucket(2 ** 0, 2 ** 160)

    @property
    def low(self):
        return self._low

    @property
    def high(self):
        return self._high

    @property
    def depth(self):
        '''
        Bucket depth is defined as the count of prefix bits that all contacts
        in the bucket share.
        '''
        raise NotImplementedError()

    @property
    def contacts(self):
        return self._contacts

    def split(self):
        '''
        Splits the bucket into a two new buckets.
        '''
        mid = int((self._low + self._high) / 2)
        left = KBucket(self._left, mid)
        right = KBucket(mid, self._right)
        return (left, right)

    def contains(self, node_id):
        '''
        Returns True if this bucket contains an exact match of the
        given node ID.
        '''
        for contact in self._contacts:
            if node_id == contact.node_id:
                return True
        return False

    def add(self, contact):
        contact.touch()
        self._contacts.append(contact)


def _append_bit(prefix: str, bit: int):
    '''Given a prefix in hex digest form, shift to the left and append the given
    bit.

    Returns a new prefix in hex digest.
    '''
    i = int(prefix, 16) << 1
    b = bit & 0x01  # mask out potential junk
    return '{:02x}'.format(i | b)


class Node:
    '''Branch node of binary tree.'''

    def __init__(self):
        self.left = None
        self.right = None


class Contact:
    '''
    Represents this peer's knowledge of another peer.
    '''

    def __init__(self, address, port, node_id):
        self.address = address
        self.port = port
        self.node_id = node_id
        self.last_seen = None
        self.touch()

    def touch(self):
        self.last_seen = datetime.utcnow()
