
import math
from array import array
from datetime import datetime
from copy import deepcopy

KEY_SIZE_BITS = 512
KEY_SIZE_BYTES = 64


class RoutingTableError(Exception):
    pass


class NodeId(object):
    __slots__ = ('_data',)

    def __init__(self, data):
        if isinstance(data, str):
            if str.startswith('0x', data):
                # Hex
                self._data = int(data, 16)
            elif str.startswith('0b', data):
                # Binary
                self._data = int(data, 2)
            else:
                # Decimal
                self._data = int(data, 10)
        elif isinstance(data, int):
            self._data = data
        else:
            raise TypeError(
                'node Id data must be an integer or string representation of an integer')

    @staticmethod
    def generate():
        '''
        Generates a new random 160-bit ID, and formats it as a hex-digest.
        '''
        # TODO: Replace with Crypto safe RNG
        import random

        # -1 because random is inclusive
        return NodeId(random.randint(0, (2**160) - 1))

    @property
    def raw_data(self):
        '''
        Integer representation of internal data.
        '''
        return deepcopy(self._data)

    @property
    def hex_digest(self):
        '''
        Hex digest representation of internal data.
        '''
        return hex(self._data)

    def has_prefix(self, prefix: int):
        '''
        Checks whether the node ID starts with the given prefix.

        The prefix must be supplied as a hex digest.
        '''
        p = len(bin(prefix)) - 2  # bit count using binary - '0x'
        i, j = 0, 0
        while i < p and j < 160:
            a = prefix >> (p - 1 - i) & 1
            b = (self._data >> (159 - j)) & 1
            if a != b:
                return False
            i += 1
            j += 1
        return True

    def nth_bit(self, n: int):
        '''
        Return the n-th bit of this ID, starting from the most significant bit.
        '''
        return (self._data >> (160 - 1 - n)) & 0x01

    def __xor__(self, rhs):
        return NodeId(self._data ^ rhs._data)  # pylint: disable=protected-access

    def __repr__(self):
        return "%s('%s')" % (self.__class__.__name__, self.hex_digest)

    def __str__(self):
        return self.hex_digest

    def __eq__(self, rhs):
        if rhs is None:
            return False

        if self._data != rhs._data:  # pylint: disable=protected-access
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
        self._root = Tree.create_leaf(bucket)

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

        if node.is_leaf:
            if node.kbucket.contains(self._owner_id):
                # Always split when encountering the owner node
                pass
            elif len(node.kbucket) >= self._ksize:
                # k-bucket is full and needs to be split
                (left, right) = node.kbucket.split()
                node.to_branch(left, right)
            else:
                node.kbucket.add(contact)
        elif node.is_branch:
            # Check which branch to recurse down
            pass

    def _split(self, bucket):
        '''
        Accepts a k-bucket, splits it into two new buckets, distributes
        the contacts correctly between them, and returns a new branch node.
        '''
        (left, right) = bucket.split()
        return (left, right)

    def find(self, node_id: NodeId):
        return self._find(node_id, self._root)

    def _find(self, node_id, node, level=0):
        if node.is_leaf:
            # Reached leaf
            if len(node.kbucket.contacts) > 0:
                # TODO: Return the most recently seen contact
                return node.kbucket.contacts[0]
            else:
                return None
        elif node.is_branch:
            # Determine down which path we should search
            if node_id.nth_bit(level) == 1:
                return self._find(node_id, node.left, level+1)
            elif node_id.nth_bit(level) == 0:
                return self._find(node_id, node.right, level+1)


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
        left = KBucket(self._low, mid)
        right = KBucket(mid, self._high)
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

    def __len__(self):
        return len(self._contacts)


def _append_bit(prefix: str, bit: int):
    '''
    Given a prefix in hex digest form, shift to the left and append the given
    bit.

    Returns a new prefix in hex digest.
    '''
    i = int(prefix, 16) << 1
    b = bit & 0x01  # mask out potential junk
    return '{:02x}'.format(i | b)


class Tree:
    '''Binary tree node.'''

    __slots__ = ('_l', '_r', '_kbucket')

    def __init__(self, kbucket, left, right):
        self._l = left
        self._r = right
        self._kbucket = kbucket

    @staticmethod
    def create_leaf(kbucket):
        if kbucket is None:
            raise ValueError('kbucket is None')

        return Tree(kbucket, None, None)

    @staticmethod
    def create_branch(left, right):
        if left is None:
            raise ValueError('left is None')

        if right is None:
            raise ValueError('right is None')

        return Tree(None, left, right)

    def to_branch(self, left, right):
        '''
        Changes this leaf node to a branch node.

        The k-bucket contained in this None will be discarded.

        Will throw an exception if this node is already a branch.
        '''
        if not self.is_leaf:
            raise RoutingTableError(
                'cannot change binary tree node to branch, already branch')

        self._kbucket = None
        self._l = left
        self._r = right

    @property
    def is_leaf(self):
        return self._kbucket is not None

    @property
    def is_branch(self):
        return self._kbucket is None

    @property
    def left(self):
        return self._l

    @property
    def right(self):
        return self._r

    @property
    def kbucket(self):
        return self._kbucket


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
