"""
Common message classes.
"""

from abc import ABCMeta, abstractmethod
from collections import OrderedDict
from copy import deepcopy
from uuid import uuid4
from datetime import datetime


# TODO: Remember endianess

# =============================================================================
# Fields


class MessageField(metaclass=ABCMeta):
    # TODO: Validation abstract method
    # TODO: Explicit field order
    pass


class Integer(MessageField):
    # TODO: Validate type
    pass


# =============================================================================
# Messages

class MessageDeclareError(Exception):
    """
    Error thrown during the meta- or abstract class processing of a message type, during
    module declaration.
    """
    pass


class MessageMeta(ABCMeta):
    def __new__(mcs, clsname, bases, attrs):
        # Validate that message enum is provided.
        if clsname != 'AbstractMessage':
            # Field not expected on abstract class
            if '__message__' not in attrs:
                raise MessageDeclareError("message type %s must have a '__message__' field defined" % clsname)

        # Find message fields from class and add to class level
        # registry. Used for marshalling.
        #
        # Note that field registry is ordered, because field order is
        # relevant to binary marshalling.
        attrs['__fields__'] = OrderedDict()
        for key in attrs:
            if isinstance(attrs[key], MessageField):
                attrs['__fields__'][key] = attrs[key]

        return super(MessageMeta, mcs).__new__(mcs, clsname, bases, attrs)


class AbstractMessage(object, metaclass=MessageMeta):
    """
    Base class for messages sent over a peer's network transport.
    """

    def __new__(cls, *args, **kwargs):
        """
        Creates a new message with standard message header.

        :returns: New instance of derived class.
        """
        instance = super().__new__(cls, *args, **kwargs)

        instance._header = MessageHeader()

        return instance

    @property
    def header(self):
        """
        Meta data of the message, used by the protocol in handling messages.

        Headers cannot be mutated, because the message is referenced by middleware
        up the pipeline's chain. Changing the contents of a message can effect
        upstream middleware in an unexpected way.

        :returns: Copy of headers.
        """
        return deepcopy(self._header)

    def marshal(self):
        return b''

    @classmethod
    def unmarshal(cls, byte_data):
        pass


class MessageHeader(object):

    def __init__(self):
        # Global identifier used to match requests to responses.
        self._guid = uuid4()

        # None for requests. For responses, global identifier of
        # request this message is responding to.
        self._request_id = None

        # Protocol version for this message.
        self._version = 1

        # UTC timestamp of when this message was first created by it's sender.
        self._created_on = datetime

    @property
    def guid(self):
        return deepcopy(self._guid)
