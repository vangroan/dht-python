import gevent
import gevent.event

from dht.peer import PeerServer
from dht.utils import create_logger


def main():
    logger = create_logger(__name__)
    logger.info("Starting up")

    # Stop gevent from outputting exception
    # details on keyboard interrupt.
    gevent.get_hub().NOT_ERROR += (KeyboardInterrupt,)

    peer = PeerServer('', '9000')
    cancel = gevent.event.Event()

    try:
        peer.start()
        logger.debug("TODO: Bootstrap here")
        cancel.wait()
    except KeyboardInterrupt:
        logger.info("User requested stop")
    finally:
        logger.info("Stopping")
        peer.stop(timeout=1)

        # Currently this doesn't do anything, as the
        # cancel event is just used to stop main() execution.
        cancel.set()


if __name__ == '__main__':
    main()
