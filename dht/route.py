from datetime import datetime
from copy import deepcopy


class RoutingTableError(Exception):
    pass


class BinaryTreeError(Exception):
    pass


class NodeId(object):
    """
    Identifier for content and peer nodes.

    A node id is represented by a 160-bit number. For content, an id is the SHA-1 hash of it's bytes.

    Create an id from an existing hex digest:
    >>> NodeId('0x356a192b7913b04c54574d18c28d46e6395428ab')

    Generate a random id, for use in a peer node:
    >>> NodeId.generate()
    """

    __slots__ = ('_data',)

    def __init__(self, data):
        if isinstance(data, str):
            if str.startswith('0x', data):
                # Hex
                self._data = int(data, 16)
            elif str.startswith('0b', data):
                # Binary
                self._data = int(data, 2)
            else:
                # Decimal
                self._data = int(data, 10)
        elif isinstance(data, int):
            self._data = data
        else:
            raise TypeError(
                'node Id data must be an integer or string representation of an integer')

    @staticmethod
    def generate():
        """
        Generates a new random 160-bit ID, and formats it as a hex-digest.
        """
        # TODO: Replace with Crypto safe RNG
        import random

        # -1 because random is inclusive
        return NodeId(random.randint(0, (2 ** 160) - 1))

    @property
    def raw_data(self):
        """
        Integer representation of internal data.

        :return: A big integer.
        """
        return deepcopy(self._data)

    @property
    def hex_digest(self):
        """
        Hex digest representation of internal data.
        """
        return hex(self._data)

    def has_prefix(self, prefix):
        """
        Checks whether the node ID starts with the given prefix.

        The prefix must be supplied as an integer.
        """
        p_len = len(bin(prefix)) - 2  # bit count using binary - '0x'
        i, j = 0, 0
        while i < p_len and j < 160:
            a_bit = prefix >> (p_len - 1 - i) & 1
            b_bit = (self._data >> (159 - j)) & 1
            if a_bit != b_bit:
                return False
            i += 1
            j += 1
        return True

    def nth_bit(self, index):
        """
        Return the n-th bit of this ID, starting from the most significant bit.
        """
        return (self._data >> (160 - 1 - index)) & 0x01

    def __xor__(self, rhs):
        return NodeId(self._data ^ rhs._data)  # pylint: disable=protected-access

    def __repr__(self):
        return "%s('%s')" % (self.__class__.__name__, self.hex_digest)

    def __str__(self):
        return self.hex_digest

    def __eq__(self, rhs):
        if rhs is None:
            return False

        if self._data != rhs._data:  # pylint: disable=protected-access
            return False

        return True


class RoutingTable:

    def __init__(self, owner_id):
        # Routing table must know the identity of its
        # own node, in order to make decisions on whether
        # to split buckets.
        self._owner_id = owner_id

        # Initial state is one k-bucket at the root.
        bucket = KBucket()
        bucket.add(Contact(None, None, owner_id))
        self._root = Tree.create_leaf((0, 2 ** 160), bucket)

        # Maximum number of contacts allowed in a k-bucket.
        self._ksize = 20

        # Maximum number of shared prefix bits allowed to be shared
        # between contacts inside the same bucket.
        self._depth = 5

    def insert(self, address, port, node_id):
        """
        Inserts a contact into the routing table.

        :param address: IP address as string.
        :param port: Port as integer.
        :param node_id: Identifier of the node.
        """
        self._insert(self._root, Contact(address, port, node_id))

    def _insert(self, node, contact, level=0):
        """
        Internal recursive insert method.
        """

        if node.is_leaf:
            if node.kbucket.contains(self._owner_id):
                # Always split when encountering the owner node
                node.split()

                # Handle the node again as a branch
                self._insert(node, contact, level=level)

            elif node.kbucket.contains(contact.node_id):
                # Does the contact exist?
                node.kbucket.get(contact.node_id).touch()

            elif len(node.kbucket) >= self._ksize:
                # k-bucket is full and needs to be split
                node.split()

                # Handle the node again as a branch
                self._insert(node, contact, level=level)

            else:
                node.kbucket.add(contact)
                node.kbucket.sort()

        elif node.is_branch:
            # Check which branch to recurse down
            if node.left.in_range(contact.node_id):
                self._insert(node.left, contact, level=level + 1)
            elif node.right.in_range(contact.node_id):
                self._insert(node.right, contact, level=level + 1)

    def find(self, node_id):
        """
        Searches the routing table for a contact that matches the exact given
        node id.
        """
        return self._find(node_id, self._root)

    def _find(self, node_id, node, level=0):
        if node.is_leaf:
            # Reached leaf
            if node.kbucket.contacts:
                # Return the exact contact
                return node.kbucket.get(node_id)

        elif node.is_branch:
            # Determine down which path we should search
            if node.left.in_range(node_id):
                return self._find(node_id, node.left, level=level + 1)
            elif node.right.in_range(node_id):
                return self._find(node_id, node.right, level=level + 1)

        return None


class KBucket:
    """
    Container for node contacts.

    Leaf node of binary tree.
    """
    __slots__ = ('_contacts',)

    def __init__(self):
        self._contacts = []

    @property
    def depth(self):
        """
        Bucket depth is defined as the count of prefix bits that all contacts
        in the bucket share.
        """
        raise NotImplementedError()

    @property
    def contacts(self):
        return self._contacts

    def contains(self, node_id):
        """
        Returns True if this bucket contains an exact match of the
        given node ID.
        """
        for contact in self._contacts:
            if node_id == contact.node_id:
                return True
        return False

    def add(self, contact):
        contact.touch()
        self._contacts.append(contact)

    def get(self, node_id):
        for contact in self._contacts:
            if contact.node_id == node_id:
                return contact
        return None

    def sort(self):
        """
        Sorts the k-bucket according to contact's last seen timestamp.
        """
        self._contacts = sorted(self._contacts, key=lambda contact: contact.last_seen)

    def __len__(self):
        return len(self._contacts)


class Tree:
    """Binary tree node."""

    __slots__ = ('_low', '_high', '_l', '_r', '_kbucket')

    def __init__(self, id_range, kbucket=None, branches=None):
        (low, high) = id_range
        self._low = min(low, high)
        self._high = max(low, high)

        if branches is not None:
            (left, right) = branches
            self._l = left
            self._r = right
        else:
            self._l = None
            self._r = None

        self._kbucket = kbucket

    @staticmethod
    def create_leaf(id_range, kbucket):
        if id_range is None:
            raise ValueError('id_range is None')

        if kbucket is None:
            raise ValueError('kbucket is None')

        return Tree(id_range, kbucket=kbucket)

    @staticmethod
    def create_branch(id_range, branches):
        if id_range is None:
            raise ValueError('id_range is None')

        if branches is None:
            raise ValueError('branches is None')

        return Tree(id_range, branches=branches)

    def to_branch(self, left, right):
        """
        Changes this leaf node to a branch node.

        The k-bucket contained in this None will be discarded.

        Will throw an exception if this node is already a branch.
        """
        if not self.is_leaf:
            raise RoutingTableError(
                'cannot change binary tree node to branch, already branch')

        self._kbucket = None
        self._l = left
        self._r = right

    @property
    def is_leaf(self):
        """
        Returns True if the tree contains a k-bucket.
        """
        return self._kbucket is not None

    @property
    def is_branch(self):
        """
        Returns True if the tree branches off into two other trees.
        """
        return self._kbucket is None

    @property
    def low(self):
        return self._low

    @property
    def high(self):
        return self._high

    @property
    def left(self):
        """
        Left side tree of this branch.

        Returns None if this tree is a leaf.
        """
        return self._l

    @property
    def right(self):
        """
        Right side tree of this branch.

        Returns None if this tree is a leaf.
        """
        return self._r

    @property
    def kbucket(self):
        """
        Bucket of contacts in this leaf tree.

        Returns None if this tree is a branch.
        """
        return self._kbucket

    def in_range(self, node_id):
        """
        Indicates whether the given node id is in this tree's id range.
        """
        return self._low <= node_id._data < self._high  # pylint: disable=protected-access

    def split(self):
        """
        Splits this leaf into a branch.
        """
        if self.is_branch:
            raise BinaryTreeError('cannot split branch')

        mid = int((self._low + self._high) / 2)
        left = Tree.create_leaf((self._low, mid), KBucket())
        right = Tree.create_leaf((mid, self._high), KBucket())

        # Move contents into the appropriate buckets
        for contact in self.kbucket.contacts:
            if left.in_range(contact.node_id):
                left.kbucket.add(contact)
            elif right.in_range(contact.node_id):
                right.kbucket.add(contact)

        # Contacts have moved
        self.kbucket.contacts.clear()

        self.to_branch(left, right)


class Contact:
    """
    Represents this peer's knowledge of another peer.
    """

    def __init__(self, address, port, node_id):
        self.address = address
        self.port = port
        self.node_id = node_id
        self.last_seen = None
        self.touch()

    def touch(self):
        self.last_seen = datetime.utcnow()
