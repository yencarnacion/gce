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

import webob

from nova.api.gce import zones
from nova.tests.api.gce import common
from nova.tests.api.openstack import fakes


FAKE_ZONES = ['internal', 'nova'], ['unavailable_zone']

EXPECTED_ZONES = [
  {
    "id": 3924463100986466035,
    "kind": "compute#zone",
    "selfLink": "http://localhost/compute/v1beta15/projects/fake_project"
        "/zones/nova",
    "name": "nova",
    "status": "UP"
  },
  {
    "id": 3660105603433928984,
    "kind": "compute#zone",
    "selfLink": "http://localhost/compute/v1beta15/projects/fake_project"
        "/zones/unavailable_zone",
    "name": "unavailable_zone",
    "status": "DOWN"
  },
]


class ZonesControllerTest(common.GCEControllerTest):
    """Test of the GCE API /zones appliication."""

    def setUp(self):
        """Run before each test."""
        super(ZonesControllerTest, self).setUp()
        self.controller = zones.Controller()

    def test_get_zone_by_invalid_name(self):
        req = fakes.HTTPRequest.blank('/fake_project/zones/fakezone')
        self.assertRaises(webob.exc.HTTPNotFound,
                self.controller.show, req, 'wrongZone')

    def test_get_zone(self):
        response = self.request_gce('/fake_project/zones/nova')
        expected = EXPECTED_ZONES[0]

        self.assertEqual(response.json_body, expected)

    def test_get_zone_list(self):
        response = self.request_gce('/fake_project/zones')
        expected = {
            "kind": "compute#zoneList",
            "id": "projects/fake_project/zones",
            "selfLink": "http://localhost/compute/v1beta15/projects"
                "/fake_project/zones",
            "items": EXPECTED_ZONES
        }

        self.assertEqual(response.json_body, expected)
