
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
        '''Generates a new random 512-bit ID, and formats it as a hex-digest'''
        # TODO: Replace with Crypto safe RNG
        import random

        # 64 bytes * 8 bits = 512 bits
        data = array('B', [random.randint(0, 0xFF)
                           for _ in range(KEY_SIZE_BYTES)])  # Unsigned Bytes
        return NodeId(data)

    @staticmethod
    def _parse(str_data):
        '''Given a hex digest string, return ID data in byte array form.'''

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
        '''Byte array representation of internal data.'''
        return deepcopy(self._data)

    @property
    def hex_digest(self):
        '''Hex digest representation of internal data.'''
        return ''.join(('{:02x}'.format(b) for b in self._data))

    def has_prefix(self, prefix: str):
        '''Checks whether the node ID starts with the given prefix.

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
        '''Return the n-th bit of this ID, starting from the most significant bit.'''
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
        self._root = Bucket('', initial=[Contact(None, None, owner_id, None)])

    def insert(self, address, port, nodeid):
        self._insert(self._root, Contact(
            address, port, nodeid, datetime.utcnow()))

    def _insert(self, node, contact, level=0):
        '''Internal recursive insert method.'''

        if isinstance(node, Bucket):
            # Always split when encountering the owner node
            if node.contains_id(self._owner_id):
                pass

    def _split(self, bucket):
        '''Accepts a k-bucket, splits it into two new buckets, distributes
        the contacts correctly between them, and returns a new branch node.
        '''
        prefix = bucket.prefix

        node = Node()
        node.left = Bucket(_append_bit(prefix, 1) if prefix else '1')
        node.right = Bucket(_append_bit(prefix, 0) if prefix else '0')

        for contact in bucket.contacts:
            if contact.nodeid.has_prefix(node.left.prefix):
                node.left.contacts.append(contact)
            elif contact.nodeid.has+prefix(node.right.prefix):
                node.right.contacts.append(contact)

        return node

    def find(self, nodeid: NodeId):
        return self._find(nodeid, self._root)

    def _find(self, nodeid, node, level=0):
        if isinstance(node, Bucket):
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


class Bucket:
    '''Leaf node of binary tree.'''

    def __init__(self, prefix, initial=list()):
        self.prefix = prefix
        self.contacts = initial

    def contains_id(self, nodeid):
        '''Returns True if this bucket contains an exact match of the
        given node ID.
        '''
        for c in self.contacts:
            if c.nodeid == nodeid:
                return True
        return False


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
    def __init__(self, address: str, port: str, nodeid: NodeId, last_seen: datetime):
        self.address = address
        self.port = port
        self.nodeid = nodeid
        self.last_seen = last_seen
