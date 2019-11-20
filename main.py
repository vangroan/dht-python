
from peer import PeerServer

if __name__ == '__main__':
    print('Starting up')
    
    PeerServer('', '9000').serve_forever()
