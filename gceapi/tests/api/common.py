#    Copyright 2013 Cloudscaling Group, Inc
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

from oslo.config import cfg
from glanceclient import client as glanceclient
from keystoneclient.v2_0 import client as kc
from novaclient import client as novaclient
from novaclient import shell as novashell
from neutronclient.v2_0 import client as neutronclient
from cinderclient import client as cinderclient

from gceapi.tests.api import fake_keystone_client
from gceapi.tests.api import fake_nova_client
from gceapi.tests.api import fake_glance_client
from gceapi.tests.api import fake_cinder_client
from gceapi.tests.api import fake_neutron_client
from gceapi.tests.api import fake_request

from gceapi import test
import gceapi.api
import gceapi.tests.api.fake_db as fake_db


class GCEControllerTest(test.TestCase):

    _APIRouter = None

    def setUp(self):
        cfg.CONF.set_override('network_api', 'neutron')
        super(GCEControllerTest, self).setUp()
        self.maxDiff = None

        self.stubs.Set(kc, 'Client', fake_keystone_client.FakeKeystoneClient)
        self.stubs.Set(neutronclient, "Client",
           fake_neutron_client.FakeNeutronClient)
        self.stubs.Set(glanceclient, "Client",
           fake_glance_client.FakeGlanceClient)
        self.stubs.Set(cinderclient, "Client",
           fake_cinder_client.FakeCinderClient)
        self.stubs.Set(novashell.OpenStackComputeShell, '_discover_extensions',
                       fake_nova_client.fake_discover_extensions)
        self.stubs.Set(novaclient, 'Client', fake_nova_client.FakeNovaClient)
        self.db_fixture = self.useFixture(fake_db.DBFixture(self.stubs))

    def request_gce(self, url, method="GET", body=None):
        fake_req = fake_request.HTTPRequest.blank(url, method=method,
                                                  has_body=body is not None)
        fake_req.json = body
        return fake_req.get_response(self._get_api_router())

    def assertDictInListBySelfLink(self, expected, container, msg=None):
        for member in container:
            if expected["selfLink"] != member["selfLink"]:
                continue
            self.assertDictEqual(expected, member)
            return
        standardMsg = ('Dictionary id %s not found in dictionary list %s'
                % (member["selfLink"], map(lambda x: x["selfLink"],
                                           container)))
        self.fail(self._formatMessage(msg, standardMsg))

    def _get_api_router(self):
        if not self._APIRouter:
            self._APIRouter = gceapi.api.APIRouter()
        return self._APIRouter
