
class Id(object):
    __slots__ = '_data',

    def __init__(self, data):
        self._data = data
    
    @staticmethod
    def generate():
        '''Generates a new random 512-bit ID, and formats it as a hex-digest'''
        # TODO: Replace with Crypto safe RNG
        import random

        return Id(''.join(['{:02x}'.format(random.randint(0, 0xFF)) for _ in range(64)]))


class RoutingTable:
    
    def __init__(self):
        self._nodes = []
    
    