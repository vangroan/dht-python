import importlib

import click

from dht.client import DhtClient
from dht.utils import create_logger

logger = create_logger(__name__)


def import_all(module):
    """
    Emulates importing all from module. `from module import *`

    This is accomplished by importing the module, determining which
    members need to be imported, and inserting them into the global
    scope.
    """
    # get a handle on the module
    mdl = importlib.import_module(module)

    # is there an __all__?  if so respect it
    if "__all__" in mdl.__dict__:
        names = mdl.__dict__["__all__"]
    else:
        # otherwise we import all names that don't begin with _
        names = [x for x in mdl.__dict__ if not x.startswith("_")]

    # now drag them in
    globals().update({k: getattr(mdl, k) for k in names})


@click.command()
@click.option('--address', default='127.0.0.1')
@click.option('--port', default=9000)
@click.option('--module', default='dht.requests',
              help="Module that contains the request and response messages. Default: 'dht.requests'")
@click.argument('message')
def send(address, port, module, message):
    import_all(module)

    client = DhtClient()

    # TODO: Safely parse given `message` into request object
    request = PingRequest()
    logger.info("Sending Message %s" % request)

    response = client.send(address, port, request)
    logger.info("Received Message %s" % repr(response))


if __name__ == '__main__':
    send()
