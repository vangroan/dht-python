
from array import array

KEY_SIZE_BITS = 512
KEY_SIZE_BYTES = 64


class Id(object):
    __slots__ = '_data',

    def __init__(self, data):
        if isinstance(data, str):
            self._data = Id._parse(data)
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
        return Id(data)

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
    def hex_digest(self):
        return ''.join(('{:02x}'.format(b) for b in self._data))

    def __xor__(self, rhs):
        result = array('B', [0 for _ in range(KEY_SIZE_BYTES)])
        for i in range(KEY_SIZE_BYTES):
            result[i] = self._data[i] ^ rhs._data[i]
        return Id(result)

    def __repr__(self):
        return "%s('%s')" % (self.__class__.__name__, self.hex_digest)

    def __str__(self):
        return self.hex_digest

    def __eq__(self, rhs):
        for i in range(KEY_SIZE_BYTES):
            if self._data[i] != rhs._data[i]:
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
        self._root = Bucket(initial=[Contact(None, None, owner_id, None)])

    def insert(self, id):
        raise NotImplementedError()


class Bucket:
    '''Leaf node of binary tree.'''

    def __init__(self, initial=[]):
        self.contacts = initial


class Node:
    '''Branch node of binary tree.'''

    def __init__(self):
        self.left = None
        self.right = None


class Contact:
    def __init__(self, address, port, id, last_seen):
        self.address = address
        self.port = port
        self.id = id
        self.last_seen = last_seen
