
import gevent

from peer import PeerServer


if __name__ == '__main__':
    print('Starting up')

    # Stop gevent from outputting exception
    # details on keyboard interrupt.
    gevent.get_hub().NOT_ERROR += (KeyboardInterrupt,)
    
    peer = PeerServer('', '9000')
    cancel = gevent.event.Event()
    
    try:
        peer.start()
        print('Bootstrap here')
        cancel.wait()
    except KeyboardInterrupt:
        print('User requested stop')
    finally:
        print('Stopping')
        peer.stop(timeout=1)

        # Currently this doesn't do anything, as the
        # cancel event is just used to stop main() execution.
        cancel.set()


