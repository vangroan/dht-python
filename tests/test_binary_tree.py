
import unittest

from dht import route
from dht.route import Tree, KBucket


class TestBinaryTree(unittest.TestCase):

    def test_create(self):
        """
        Should create trees as either leaves or branches.
        """
        bucket = KBucket()
        leaf = Tree.create_leaf((0, 2**160), bucket)
        self.assertIsNotNone(leaf)
        self.assertEqual(bucket, leaf.kbucket)

        (a, b) = (KBucket(), KBucket())
        (left, right) = (Tree.create_leaf((0, 2**80), a), Tree.create_leaf((2**80, 2**160), b))
        branch = Tree.create_branch((0, 2**160), (left, right))
        self.assertIsNotNone(branch)
        self.assertEqual(left, branch.left)
        self.assertEqual(left.kbucket, a)
        self.assertEqual(right, branch.right)
        self.assertEqual(right.kbucket, b)

    def test_to_branch(self):
        """
        Should convert a leaf tree to a branch tree.
        """
        # assume
        tree = Tree.create_leaf((0, 2**160), KBucket())

        # act
        tree.split()

        # assert
        self.assertIsNone(tree.kbucket)
        self.assertIsNotNone(tree.left)
        self.assertIsNotNone(tree.right)

    def test_to_branch_error(self):
        """
        Should raise an exception when tree is already a branch.
        """
        self.skipTest('TODO')
