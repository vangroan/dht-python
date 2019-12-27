"""
Common message classes.
"""

from abc import abstractmethod, ABC
from collections import OrderedDict
from copy import deepcopy
from datetime import datetime
from itertools import islice
from uuid import uuid4, UUID

from dht.route import NodeId


# TODO: Remember endianess

# =============================================================================
# Fields


class MessageField(ABC):
    # TODO: Validation abstract method
    # TODO: Explicit field order

    @property
    @abstractmethod
    def default_value(self):
        raise NotImplementedError()

    @abstractmethod
    def marshal(self, val):
        raise NotImplementedError()

    @abstractmethod
    def unmarshal(self, data):
        raise NotImplementedError()


class Integer(MessageField):
    # TODO: Validate type

    def __init__(self, default=0):
        self._default_value = default

    @property
    def default_value(self):
        return self._default_value

    def marshal(self, val):
        return val.to_bytes(4, 'big')

    def unmarshal(self, data):
        return int.from_bytes(data[:4], 'big'), 4


class NodeIdField(MessageField):

    def __init__(self, default_value=NodeId.empty()):
        self._default_value = default_value

    @property
    def default_value(self):
        return self._default_value

    def marshal(self, val):
        """
        Marshals node id to a 160-bit worth of bytes.
        """
        if val is None:
            # TODO: Properly handle optional fields
            return bytes(20)
        return val.raw_data.to_bytes(20, 'big')

    def unmarshal(self, data):
        inner = int.from_bytes(data[:20], 'big')
        if inner == 0:
            # TODO: Properly handle optional fields
            return None, 20
        return NodeId(inner), 20


class GuidField(MessageField):
    def __init__(self, default_value=uuid4):
        """
        :type default_value: Optional[UUID]
        """
        self._default_value = default_value
        if default_value:
            self._default_value = default_value

    @property
    def default_value(self):
        return self._default_value

    def marshal(self, val):
        if val is None:
            # TODO: Properly handle optional fields
            return bytes(16)
        return val.bytes

    def unmarshal(self, data):
        return UUID(bytes=data[:16]), 16


class DateTimeField(MessageField):
    def __init__(self, default_value=datetime.min):
        self._default_value = default_value

    @property
    def default_value(self):
        return self._default_value

    def marshal(self, val):
        unix_time = int(val.timestamp())
        return unix_time.to_bytes(8, 'big')

    def unmarshal(self, data):
        unix_time = int.from_bytes(bytes=data[:8], byteorder='big')
        return datetime.fromtimestamp(float(unix_time)), 8


# =============================================================================
# Messages

class MessageDeclareError(Exception):
    """
    Error raised during the meta- or abstract class processing of a message type, during
    module declaration.
    """
    pass


class MessageCreateError(Exception):
    """
    Error raised when a Message instance cannot be created.
    """
    pass


class MessageMeta(type):
    """
    Meta class for message types.

    Implements some of the magic that make marshalling and unmarshalling ergonomic. Class level
    fields on concrete message types are collected into an ordered collection.

    Classes that inherit from Message are stored in a registry that can be used as
    a lookup, from the value in `__message__` to the class.
    """
    _message_types = dict()

    def __new__(mcs, clsname, bases, attrs):
        # Attributes dictionary is cleared after class is declared later.
        message_enum = None

        # Validate that message enum is provided.
        if clsname != 'Message':
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


class Message(object, metaclass=MessageMeta):
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
        try:
            # object constructor takes no arguments
            instance = super().__new__(cls)

            fields = cls.__fields__
            for field_name in fields:
                field = fields[field_name]

                # Allow for lazy defaults via lambdas
                if callable(field.default_value):
                    default_value = field.default_value()
                else:
                    default_value = field.default_value

                setattr(instance, field_name, kwargs.get(field_name, default_value))

            instance._header = MessageHeader()

            # Assign message type id to header so it will be included when marshalled.
            instance._header._sender_node_id = getattr(cls, '__message__', 0)

            return instance
        except Exception as ex:
            raise MessageCreateError("failed to create message instance") from ex

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
        """
        Outputs the message as bytes.
        """
        fields = self.__class__.__fields__
        buf = []

        # Message enum
        enum_field = Integer()
        buf.extend(enum_field.marshal(self.__class__.__message__))

        # Fields
        for field_name in fields:
            field = fields[field_name]

            # Allow for lazy defaults via lambdas
            if callable(field.default_value):
                default_value = field.default_value()
            else:
                default_value = field.default_value

            val = getattr(self, field_name, default_value)
            buf.extend(field.marshal(val))
        data = bytes(buf)
        return data

    @classmethod
    def unmarshal(cls, data):
        """
        Accepts bytes containing a marshalled message, and returns an instance of this message class.
        """
        fields = cls.__fields__
        values = {}

        # Fields
        i = 0
        for field_name in fields:
            field = fields[field_name]
            (val, size) = field.unmarshal(data[i:])
            values[field_name] = val
            i += size

        # noinspection PyArgumentList
        return cls(**values)

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

    @classmethod
    def extract_message_type(cls, data):
        """
        Given a bytes containing a marshalled message, determine the concrete message class and return the type.

        :param data: Bytes containing marshalled message.
        :return: Concrete message type from type registry, None if not found.
        """
        # message type is at beginning of byte array
        enum_bytes = data[:4]
        message_enum = int.from_bytes(enum_bytes, 'big')
        return MessageMeta.message_types().get(message_enum, None)

    def respond(self, response_cls, *args, **kwargs):
        """
        Creates an instance of the given message class, and configures it to be the
        response leg of this message.

        Raises an exception when the given class is not an instance of Message.
        """
        if not issubclass(response_cls, Message):
            raise MessageCreateError("given class does not inherit from %s" % Message.__name__)

        instance = response_cls(*args, **kwargs)
        # noinspection PyProtectedMember
        instance._header._request_guid = self._header._guid

        return instance

    def __repr__(self):
        """
        Developer readable representation of the class.
        """
        buf = [self.__class__.__name__, "("]
        fields = self.__class__.__fields__

        field_buf = []
        for field_name in fields:
            if hasattr(self, field_name):
                field_buf.append("{}={}".format(field_name, getattr(self, field_name)))

        buf.append(", ".join(field_buf))
        buf.append(")")

        return "".join(buf)


class MessageHeader(object):
    """
    Common meta data at the beginning of a message.
    """
    __fields__ = {
        'message_type_id': Integer(),
        'guid': GuidField(),
        'request_guid': GuidField(default_value=None),
        'version': Integer(),
        'created_on': DateTimeField(),
        'sender_node_id': NodeIdField(default_value=None),
    }

    def __init__(self):
        # Importantly the type id is at the front of the message, so it can be
        # used to determine the class of message contained in the byte data.
        self._message_type_id = 0

        # Global identifier used to match requests to responses.
        self._guid = uuid4()

        # None for requests. For responses, global identifier of
        # request this message is responding to.
        self._request_guid = None

        # Protocol version for this message.
        self._version = 1

        # UTC timestamp of when this message was first created by it's sender.
        self._created_on = datetime.utcnow()

        # TODO: Senders must identify themselves
        self._sender_node_id = None

    @property
    def guid(self):
        return deepcopy(self._guid)

    @property
    def request_guid(self):
        return self._request_guid

    def marshal(self):
        buf = bytearray()

        for field_name in self.__fields__:
            n = '_%s' % field_name
            field = self.__fields__[field_name]
            instance_field = getattr(self, n)

            if getattr(self, n) is None:
                buf.extend(field.marshal(field.default_value))
            else:
                buf.extend(field.marshal(instance_field))

        return bytes(buf)

    @classmethod
    def unmarshal(cls, data):
        instance = cls()

        i = 0
        for field_name in cls.__fields__:
            n = '_%s' % field_name
            field = cls.__fields__[field_name]

            val, offset = field.unmarshal(data[i:])
            i += offset

            setattr(instance, n, val)

        return instance
