import unittest
from src.permissions import check_permission


class TestPermissions(unittest.TestCase):
    def test_valid_permission(self):
        self.assertTrue(check_permission('Mod', 'Kick'))

    def test_invalid_permission(self):
        self.assertFalse(check_permission('Member', 'Kick'))

    def test_command_not_found(self):
        self.assertFalse(check_permission('Admin', 'NonexistentCommand'))

    def test_valid_permission_multiple_roles(self):
        self.assertTrue(check_permission('Admin', 'Sudo'))

    def test_invalid_permission_case_insensitive(self):
        self.assertFalse(check_permission('member', 'KICK'))

    def test_invalid_role(self):
        self.assertFalse(check_permission('InvalidRole', 'AnyCommand'))


if __name__ == '__main__':
    unittest.main()
