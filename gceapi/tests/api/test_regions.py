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
from gceapi.api import regions
from gceapi.tests.api import common


FAKE_REGIONS = ['nova']

EXPECTED_REGIONS = [
  {
    "id": "6643843765891209621",
    "kind": "compute#region",
    "selfLink": "http://localhost/compute/v1beta15/projects/fake_project"
        "/regions/nova",
    "name": "nova",
    "status": "UP",
    "zones": [
      "http://localhost/compute/v1beta15/projects/fake_project"
        "/zones/nova",
      "http://localhost/compute/v1beta15/projects/fake_project"
        "/zones/unavailable_zone"]
  },
]


class RegionsControllerTest(common.GCEControllerTest):
    """
    Test of the GCE API /regions appliication.
    """

    def setUp(self):
        """Run before each test."""
        super(RegionsControllerTest, self).setUp()
        self.controller = regions.Controller()

    def test_get_region_by_invalid_name(self):
        response = self.request_gce('/fake_project/regions/fakeregion')
        self.assertEqual(404, response.status_int)

    def test_get_region(self):
        response = self.request_gce('/fake_project/regions/nova')
        expected = EXPECTED_REGIONS[0]

        self.assertEqual(response.json_body, expected)

    def test_get_region_list_filtered(self):
        response = self.request_gce("/fake_project/regions"
                                    "?filter=name+eq+nova")
        expected = {
            "kind": "compute#regionList",
            "id": "projects/fake_project/regions",
            "selfLink": "http://localhost/compute/v1beta15/projects"
                "/fake_project/regions",
            "items": [EXPECTED_REGIONS[0]]
        }

        self.assertEqual(response.json_body, expected)

    def test_get_region_list(self):
        response = self.request_gce('/fake_project/regions')
        expected = {
            "kind": "compute#regionList",
            "id": "projects/fake_project/regions",
            "selfLink": "http://localhost/compute/v1beta15/projects"
                "/fake_project/regions",
            "items": EXPECTED_REGIONS
        }

        self.assertEqual(response.json_body, expected)
