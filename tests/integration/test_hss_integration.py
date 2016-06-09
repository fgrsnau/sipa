from flask import url_for

from .test_hss_ldap import SimpleLdapTestBase
from .test_hss_postgres import FrontendFixture, HssPgTestBase


class HssAuthenticatedTestBase(FrontendFixture, HssPgTestBase, SimpleLdapTestBase):
    """The hss test base providing an app and methods for authentication."""
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.uid = list(self.fixtures.keys()).pop()
        self.pw = self.fixtures[self.uid]['userPassword']

    def login(self):
        return self.client.post(
            url_for('generic.login'),
            data={'dormitory': 'hss',
                  'username': self.uid,
                  'password': self.pw}
        )

    def logout(self):
        return self.client.get(
            url_for('generic.logout')
        )


class HssAuthenticationTestCase(HssAuthenticatedTestBase):
    def test_login_successful(self):
        """Test that a login redirects to the usersuite"""
        rv = self.login()
        self.assertRedirects(rv, url_for('usersuite.usersuite'))

    def test_logout_successful(self):
        self.login()
        rv = self.logout()
        if rv.status_code == 401:
            self.fail('Logout not permitted, probably because login failed')
        self.assert_redirects(rv, url_for('generic.index'))


class HssFrontendTestBase(HssAuthenticatedTestBase):
    """A test base for hss integration tests

    This class sets up the ldap and psql backends having an
    initialized app object.

    It needs:

    - AppInitialized (provides TestCase)
    - Ldap fixtures
    - An Ldap fixture loader
    - Psql fixtures
    - Psql fixture loader
    - something providing login

    Preferably, `AppInitialized` is `disjoint` from most things.

    however, some config vars concerning psql and ldap have to be set.

    The main problem probably is that everything TestCase-Related is
    bundled in one giant class `AppInitialized`.
    """
    def setUp(self):
        super().setUp()
        self.login()

    def tearDown(self):
        self.logout()
        super().tearDown()


class HssUsersuiteTestCase(HssFrontendTestBase):
    def test_usersuite_accessible_after_login(self):
        rv_usersuite = self.client.get(url_for('usersuite.usersuite'))
        self.assert200(rv_usersuite)


class HssPasswordChangeTestCase(HssFrontendTestBase):
    def setUp(self):
        super().setUp()
        self.rv = self.client.post(
            url_for('usersuite.usersuite_change_password'),
            data={'username': self.uid, 'password': self.pw},
            follow_redirects=True,
        )
        self.text = "Diese Funktion ist nicht verfügbar.".encode('utf-8')

    def test_password_change_not_disallowed(self):
        self.assertIn(self.text, self.rv.data)
