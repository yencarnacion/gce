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

import os.path
import StringIO
import tarfile
import urllib2
from oslo.config import cfg

import mox

from gceapi import test
import gceapi.api
import gceapi.tests.api.fake_image as fake_image
import gceapi.tests.api.fake_instance as fake_instance
import gceapi.tests.api.fake_network as fake_network
import gceapi.tests.api.fake_project as fake_project
import gceapi.tests.api.fake_request as fake_request
import gceapi.tests.api.fake_security_group as fake_security_group
import gceapi.tests.api.fake_volume as fake_volume
import gceapi.tests.api.fake_zone as fake_zone


class GCEControllerTest(test.TestCase):

    _APIRouter = None

    def setUp(self):
        cfg.CONF.set_override('network_api_class', 'neutron')
        super(GCEControllerTest, self).setUp()
        self.maxDiff = None
        fake_image_service = fake_image.FakeImageService()
        self.stubs.Set(nova.image.glance, 'get_default_image_service',
           lambda: fake_image_service)
        self.stubs.Set(nova.network.quantumv2, "get_client",
           fake_network.fake_quantum_get_client)
        self.stubs.Set(nova.network.security_group.openstack_driver,
           "get_openstack_security_group_driver",
           fake_security_group.FakeSecurityGroupService)
        self.stubs.Set(nova.volume, "API", fake_volume.FakeVolumeService)
        self.stubs.Set(nova.availability_zones, "get_host_availability_zone",
           fake_zone.get_host_availability_zone)
        self.stubs.Set(nova.availability_zones, "get_availability_zones",
           fake_zone.get_availability_zones)
        self.stubs.Set(compute_api.API, 'get_all',
            fake_instance.fake_instance_get_all)
        self.stubs.Set(db, 'block_device_mapping_get_all_by_instance',
            fake_instance.fake_block_device_mapping_get_all_by_instance)
        self.stubs.Set(compute_api, "KeypairAPI", fake_project.FakeKeypairAPI)
        self.stubs.Set(network, "API", fake_network.FakeNetworkAPI)

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
            self._APIRouter = nova.api.gce.APIRouter()
        return self._APIRouter

    def set_stubs_for_load_tar(self):
        def blank(*args, **kwargs):
            return StringIO.StringIO('')

        def fake_tar_file(*args, **kwargs):

            class Tar(object):

                def next(self):
                    member = mox.Mox()
                    member.name = 'img_name'
                    return member

                def extract(self, member, dir):
                    f = open(os.path.join(dir, member.name), 'w')
                    f.write('extract\n')
                    f.close()

                def close(self):
                    pass

            return Tar()

        self.stubs.Set(urllib2, 'urlopen', blank)
        self.stubs.Set(tarfile, 'open', fake_tar_file)
