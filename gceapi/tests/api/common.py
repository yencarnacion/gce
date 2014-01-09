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

import copy
import uuid

from cinderclient import client as cinderclient
from glanceclient import client as glanceclient
from keystoneclient.v2_0 import client as kc
from neutronclient.v2_0 import client as neutronclient
from novaclient import client as novaclient
from novaclient import shell as novashell
from oslo.config import cfg

import gceapi.api
from gceapi.openstack.common import timeutils
from gceapi import test
from gceapi.tests.api import fake_cinder_client
from gceapi.tests.api import fake_db
from gceapi.tests.api import fake_glance_client
from gceapi.tests.api import fake_keystone_client
from gceapi.tests.api import fake_neutron_client
from gceapi.tests.api import fake_nova_client
from gceapi.tests.api import fake_request


COMMON_OPERATION = {
    u'kind': u'compute#operation',
    u'id': u'2898918100885047175',
    u'name': u'operation-735d48a5-284e-4fb4-a10c-a465ac0b8888',
    u'selfLink': u'http://localhost/compute/v1beta15/projects/'
                'fake_project/global/operations/'
                'operation-735d48a5-284e-4fb4-a10c-a465ac0b8888',
    u'user': u'fake_user',
    u'insertTime': u'2013-12-27T08:46:34.684354Z',
    u'startTime': u'2013-12-27T08:46:34.684354Z',
}

COMMON_FINISHED_OPERATION = {
    u'progress': 100,
    u'status': u'DONE',
    u'endTime': u'2013-12-27T08:46:34.684354Z',
}
COMMON_FINISHED_OPERATION.update(COMMON_OPERATION)

COMMON_PENDING_OPERATION = {
    u'progress': 0,
    u'status': u'RUNNING',
}
COMMON_PENDING_OPERATION.update(COMMON_OPERATION)

REGION_OPERATION_SPECIFIC = {
    u'id': u'1085621292163955072',
    u'selfLink': u'http://localhost/compute/v1beta15/projects/'
                 'fake_project/regions/nova/operations/'
                 'operation-735d48a5-284e-4fb4-a10c-a465ac0b8888',
    u'region': u'http://localhost/compute/v1beta15/projects/'
               'fake_project/regions/nova',
}

COMMON_REGION_FINISHED_OPERATION = copy.copy(COMMON_FINISHED_OPERATION)
COMMON_REGION_FINISHED_OPERATION.update(REGION_OPERATION_SPECIFIC)

ZONE_OPERATION_SPECIFIC = {
    u'id': u'1422079331329525920',
    u'selfLink': u'http://localhost/compute/v1beta15/projects/'
                 'fake_project/zones/nova/operations/'
                 'operation-735d48a5-284e-4fb4-a10c-a465ac0b8888',
    u'zone': u'http://localhost/compute/v1beta15/projects/'
             'fake_project/zones/nova',
}

COMMON_ZONE_PENDING_OPERATION = copy.copy(COMMON_PENDING_OPERATION)
COMMON_ZONE_PENDING_OPERATION.update(ZONE_OPERATION_SPECIFIC)


class GCEControllerTest(test.TestCase):

    _APIRouter = None

    def setUp(self):
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
        self.stubs.Set(
                uuid, "uuid4",
                lambda: uuid.UUID("735d48a5-284e-4fb4-a10c-a465ac0b8888"))
        # NOTE(ft): we cannot stub datetime.utcnow,
        # so we stub conversion from datetime to string
        self.stubs.Set(timeutils, "isotime",
                       lambda x, y: "2013-12-27T08:46:34.684354Z")

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
