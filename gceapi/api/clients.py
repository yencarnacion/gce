# vim: tabstop=4 shiftwidth=4 softtabstop=4

#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import eventlet

from oslo.config import cfg
from novaclient import client as novaclient
from novaclient import shell as novashell
from keystoneclient.v2_0 import client as kc
from keystoneclient.v3 import client as kc_v3

from gceapi import exception
from gceapi.openstack.common import importutils
from gceapi.openstack.common import log as logging
from gceapi.openstack.common.gettextutils import _

logger = logging.getLogger(__name__)

CONF = cfg.CONF


try:
    from neutronclient.v2_0 import client as neutronclient
except ImportError:
    neutronclient = None
    logger.info(_('neutronclient not available'))
try:
    from cinderclient import client as cinderclient
except ImportError:
    cinderclient = None
    logger.info(_('cinderclient not available'))


class OpenStackClients(object):
    '''
    Convenience class to create and cache client instances.
    '''
    def __init__(self, context):
        self.context = context
        self._nova = {}
        self._keystone = None
        self._neutron = None
        self._cinder = None

    @property
    def auth_token(self):
        # if there is no auth token in the context
        # attempt to get one using the context username and password
        return self.context.auth_token or self.keystone().auth_token

    def keystone(self):
        if self._keystone:
            return self._keystone

        self._keystone = KeystoneClient(self.context)
        return self._keystone

    def url_for(self, **kwargs):
        return self.keystone().url_for(**kwargs)

    def nova(self, service_type='compute'):
        if service_type in self._nova:
            return self._nova[service_type]

        con = self.context
        if self.auth_token is None:
            logger.error(_("Nova connection failed, no auth_token!"))
            return None

        computeshell = novashell.OpenStackComputeShell()
        extensions = computeshell._discover_extensions("1.1")

        args = {
            'project_id': con.project_id,
            'auth_url': CONF.keystone_gce_url,
            'service_type': service_type,
            'username': None,
            'api_key': None,
            'extensions': extensions,
            'cacert': None,
            'insecure': False
        }

        client = novaclient.Client(1.1, **args)

        management_url = self.url_for(service_type=service_type)
        client.client.auth_token = self.auth_token
        client.client.management_url = management_url

        self._nova[service_type] = client
        return client

    def neutron(self):
        if neutronclient is None:
            return None
        if self._neutron:
            return self._neutron

        if self.auth_token is None:
            logger.error(_("Neutron connection failed, no auth_token!"))
            return None

        args = {
            'auth_url': CONF.keystone_gce_url,
            'service_type': 'network',
            'token': self.auth_token,
            'endpoint_url': self.url_for(service_type='network'),
            'ca_cert': None,
            'insecure': False
        }

        self._neutron = neutronclient.Client(**args)

        return self._neutron

    def cinder(self):
        if cinderclient is None:
            return self.nova('volume')
        if self._cinder:
            return self._cinder

        con = self.context
        if self.auth_token is None:
            logger.error(_("Cinder connection failed, no auth_token!"))
            return None

        args = {
            'service_type': 'volume',
            'auth_url': CONF.keystone_gce_url,
            'project_id': con.project_id,
            'username': None,
            'api_key': None,
            'cacert': None,
            'insecure': False
        }

        self._cinder = cinderclient.Client('1', **args)
        management_url = self.url_for(service_type='volume')
        self._cinder.client.auth_token = self.auth_token
        self._cinder.client.management_url = management_url

        return self._cinder


class ClientBackend(object):
    '''Delay choosing the backend client module until the client's class needs
    to be initialized.
    '''
    def __new__(cls, context):
        return OpenStackClients(context)


Clients = ClientBackend


class KeystoneClient(object):
    """
    Wrap keystone client so we can encapsulate logic used in resources
    Note this is intended to be initialized from a resource on a per-session
    basis, so the session context is passed in on initialization
    Also note that a copy of this is created every resource as self.keystone()
    via the code in engine/client.py, so there should not be any need to
    directly instantiate instances of this class inside resources themselves
    """
    def __init__(self, context):
        self.context = context
        self._client_v2 = None

    @property
    def client_v2(self):
        if not self._client_v2:
            self._client_v2 = self._v2_client_init()
        return self._client_v2

    def _v2_client_init(self):
        if self.context.auth_token is None:
            logger.error(_("Keystone v2 API connection failed, "
                         "no auth_token!"))
            raise exception.NotAuthorized()

        client_v2 = kc.Client(
            token=self.context.auth_token,
            tenant_id=self.context.project_id,
            auth_url=CONF.keystone_gce_url)

        return client_v2

    def url_for(self, **kwargs):
        return self.client_v2.service_catalog.url_for(**kwargs)

    @property
    def auth_token(self):
        return self.client_v2.auth_token
