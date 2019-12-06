
import unittest

from dht import route
from dht.route import Tree, KBucket


class TestBinaryTree(unittest.TestCase):

    def test_create(self):
        bucket = KBucket.default()
        leaf = Tree.create_leaf(bucket)
        self.assertIsNotNone(leaf)
        self.assertEqual(bucket, leaf.kbucket)

        (left, right) = KBucket.default().split()
        branch = Tree.create_branch(left, right)
        self.assertIsNotNone(branch)
        self.assertEqual(left, branch.left)
        self.assertEqual(right, branch.right)

    def test_to_branch(self):
        """
        Should convert a leaf tree to a branch tree.
        """
        # assume
        tree = Tree.create_leaf(KBucket.default())

        # act
        (left, right) = tree.kbucket.split()
        tree.to_branch(left, right)

        # assert
        self.assertIsNone(tree.kbucket)
        self.assertIsNotNone(tree.left)
        self.assertIsNotNone(tree.right)
    
    def test_to_branch_error(self):
        """
        Should raise an exception when tree is already a branch.
        """
        self.skipTest('TODO')
