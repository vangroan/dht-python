
from array import array

KEY_SIZE_BITS = 512
KEY_SIZE_BYTES = 64

class Id(object):
    __slots__ = '_data',

    def __init__(self, data):
        print(type(data))
        if not isinstance(data, array):
            raise TypeError('Id data must be array of unsigned bytes')

        self._data = data
    
    @staticmethod
    def generate():
        '''Generates a new random 512-bit ID, and formats it as a hex-digest'''
        # TODO: Replace with Crypto safe RNG
        import random

        # 64 bytes * 8 bits = 512 bits
        data = array('B', [random.randint(0, 0xFF) for _ in range(KEY_SIZE_BYTES)]) # Unsigned Bytes
        return Id(data)
    
    @property
    def hex_digest(self):
        return ''.join(('{:02x}'.format(b) for b in self._data))

    def __repr__(self):
        return "%s('%s')" % (self.__class__.__name__, self.hex_digest)

    def __str__(self):
        return self.hex_digest
    


ROOT_INDEX = 0

class RoutingTable:
    
    def __init__(self, owner_id):
        # Routing table must know the identity of its
        # own node, in order to make decisions on whether
        # to split buckets.
        self._owner_id = owner_id

        # Initial state is one k-bucket at the root.
        self._nodes = [[],]
    
    def insert(self, id):
        raise NotImplementedError()
    