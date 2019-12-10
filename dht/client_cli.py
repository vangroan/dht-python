
import click

from dht.client import DhtClient
from dht.utils import create_logger
from dht.requests import *

logger = create_logger(__name__)


@click.command()
@click.option('--address', default='127.0.0.1')
@click.option('--port', default=9000)
@click.argument('message')
def send(address, port, message):
    client = DhtClient()

    client.send(address, port, PingRequest())


if __name__ == '__main__':
    send()
