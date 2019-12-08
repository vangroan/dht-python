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


class MessageField(object):
    # TODO: Validation abstract method
    # TODO: Explicit field order

    def __init__(self, default_value):
        self._default_value = default_value

    @abstractmethod
    def marshal(self, val):
        raise NotImplementedError()

    @abstractmethod
    def unmarshal(self, data):
        raise NotImplementedError()


class Integer(MessageField):
    # TODO: Validate type

    def __init__(self, default=0):
        super().__init__(default)

    def marshal(self, val):
        return val.to_bytes(4, 'big')

    def unmarshal(self, data):
        return int.from_bytes(data, 'big')


# =============================================================================
# Messages

class MessageDeclareError(Exception):
    """
    Error thrown during the meta- or abstract class processing of a message type, during
    module declaration.
    """
    pass


class MessageMeta(ABCMeta):
    _message_types = dict()

    def __new__(mcs, clsname, bases, attrs):
        # Attributes dictionary is cleared after class is declared later.
        message_enum = None

        # Validate that message enum is provided.
        if clsname != 'AbstractMessage':
            # Field not expected on abstract class
            if '__message__' not in attrs:
                raise MessageDeclareError("message type %s must have a '__message__' field defined" % clsname)

            message_enum = attrs['__message__']

        # Find message fields from class and add to class level
        # registry. Used for marshalling.
        #
        # Note that field registry is ordered, because field order is
        # relevant to binary marshalling.
        attrs['__fields__'] = OrderedDict()
        for key in attrs:
            if isinstance(attrs[key], MessageField):
                attrs['__fields__'][key] = attrs[key]

        # Declare class.
        cls = super(MessageMeta, mcs).__new__(mcs, clsname, bases, attrs)

        # Allow lookup of message enum marker to concrete message class.
        if message_enum is not None:
            mcs._message_types[message_enum] = cls

        return cls

    @classmethod
    def message_types(mcs):
        return mcs._message_types

    @classmethod
    def flush_message_types(mcs):
        """
        Clears all message classes from the internal registry.
        """
        mcs._message_types.clear()


class AbstractMessage(object, metaclass=MessageMeta):
    """
    Base class for messages sent over a peer's network transport.
    """
    __fields__ = None

    def __new__(cls, *args, **kwargs):
        """
        Creates a new message with standard message header.

        Uses the given kwargs to assign fields to the resulting instance.

        :returns: New instance of derived class.
        """
        # object constructor takes no arguments
        instance = super().__new__(cls)

        fields = cls.__fields__
        for field_name in fields:
            field = fields[field_name]
            # noinspection PyProtectedMember
            setattr(instance, field_name, kwargs.get(field_name, field._default_value))

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

    # noinspection PyUnresolvedReferences
    def marshal(self):
        fields = self.__class__.__fields__
        buf = []

        # Message enum
        enum_field = Integer()
        buf.extend(enum_field.marshal(self.__class__.__message__))

        # Fields
        for field_name in fields:
            field = fields[field_name]
            # TODO: Default value from field.
            val = getattr(self, field_name, None)
            buf.extend(field.marshal(val))

        return bytes(buf)

    @classmethod
    def unmarshal(cls, byte_data):
        pass

    @classmethod
    def fullname(cls):
        """
        Helper for printing the module name along with the class' name.
        """
        module = cls.__module__
        if module is None or module == str.__class__.__module__:
            return cls.__name__  # Avoid reporting __builtin__
        else:
            return module + '.' + cls.__name__


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
