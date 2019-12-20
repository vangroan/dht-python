from abc import ABC
from functools import wraps


def incoming(message_type):
    """
    Decorator for methods that handle messages of the given type.
    """

    def inner(func):
        func.__incoming_message_type = message_type
        return func

    return inner


def outgoing(*message_types):
    """
    Decorator for message types returned by the handler function.

    Usage is optional. For documenting handlers, but currently does not change any behaviour.

    :param message_types: Types that inherit from Message.
    """

    def inner(func):
        func.__incoming_message_type = message_types
        return func

    return inner


class MessageHandlerMeta(type):
    """
    Meta class for message handler types.

    Sets up a table that maps message types to class methods that will handle them.
    """

    def __new__(mcs, classname, bases, attrs):
        handler_map = dict()

        for name in attrs:
            attr = attrs[name]
            if callable(attr):
                if hasattr(attr, '__incoming_message_type'):
                    handler_map[getattr(attr, '__incoming_message_type')] = name

        attrs['_handler_map'] = handler_map

        return super().__new__(mcs, classname, bases, attrs)


class MessageHandler(metaclass=MessageHandlerMeta):
    """
    Base for defining methods that handle incoming message requests, and produces outgoing message responses.
    """

    def dispatch(self, message):
        """
        Calls a handler method based on the type of the given message instance.

        :param message: Message payload instance.
        """
        # noinspection PyUnresolvedReferences
        method_name = self._handler_map.get(type(message))
        if method_name:
            handler = getattr(self, method_name)
            if handler:
                handler(message)

        # TODO: What to do if message is unhandled?
