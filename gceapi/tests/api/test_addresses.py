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

from gceapi.api import addresses
from gceapi.tests.api import common

EXPECTED_ADDRESSES = [{
    "kind": "compute#address",
    "id": "7878386898874730669",
    "creationTimestamp": "",
    "status": "IN USE",
    "region": "http://localhost/compute/v1beta15/projects/"
        "fake_project/regions/nova",
    "name": "ip-172-24-4-227",
    "description": "",
    "address": "172.24.4.227",
    "selfLink": "http://localhost/compute/v1beta15/projects/"
        "fake_project/regions/nova/addresses/ip-172-24-4-227",
    "users": ["http://localhost/compute/v1beta15/projects/"
        "fake_project/zones/nova/instances/i1"]
}]


class AddressesTest(common.GCEControllerTest):

    def setUp(self):
        super(AddressesTest, self).setUp()
        self.controller = addresses.Controller()

    def test_get_address_by_invalid_name(self):
        response = self.request_gce("/fake_project/regions/"
                                    "nova/addresses/fake")
        self.assertEqual(404, response.status_int)

    def test_get_address_by_name(self):
        response = self.request_gce("/fake_project/regions/"
                                    "nova/addresses/ip-172-24-4-227")

        self.assertEqual(200, response.status_int)
        self.assertEqual(response.json_body, EXPECTED_ADDRESSES[0])

    def test_get_address_list_filtered(self):
        response = self.request_gce("/fake_project/regions/nova/addresses"
                                    "?filter=name+eq+ip-172-24-4-227")
        expected = {
                "kind": "compute#addressList",
                "id": "projects/fake_project/regions/nova/addresses",
                "selfLink": "http://localhost/compute/v1beta15/projects"
                    "/fake_project/regions/nova/addresses",
                "items": [EXPECTED_ADDRESSES[0]]
                }

        self.assertEqual(response.json_body, expected)

    def test_get_address_list(self):
        response = self.request_gce("/fake_project/regions/nova/addresses")
        expected = {
                "kind": "compute#addressList",
                "id": "projects/fake_project/regions/nova/addresses",
                "selfLink": "http://localhost/compute/v1beta15/projects"
                    "/fake_project/regions/nova/addresses",
                "items": EXPECTED_ADDRESSES
                }

        self.assertEqual(response.json_body, expected)

    def test_get_address_aggregated_list_filtered(self):
        response = self.request_gce("/fake_project/aggregated/addresses"
                                    "?filter=name+eq+ip-172-24-4-227")

        expected = {
            "kind": "compute#addressAggregatedList",
            "id": "projects/fake_project/aggregated/addresses",
            "selfLink": "http://localhost/compute/v1beta15/projects"
                "/fake_project/aggregated/addresses",
            "items": {
                "regions/nova": {
                    "addresses": [EXPECTED_ADDRESSES[0]]
                },
            }
        }

        self.assertEqual(response.json_body, expected)

    def test_get_address_aggregated_list(self):
        response = self.request_gce("/fake_project/aggregated/addresses")

        expected = {
            "kind": "compute#addressAggregatedList",
            "id": "projects/fake_project/aggregated/addresses",
            "selfLink": "http://localhost/compute/v1beta15/projects"
                "/fake_project/aggregated/addresses",
            "items": {
                "regions/nova": {
                    "addresses": EXPECTED_ADDRESSES
                },
            }
        }

        self.assertEqual(response.json_body, expected)

    def test_delete_address_with_invalid_name(self):
        response = self.request_gce("/fake_project/regions/nova"
            "/addresses/fake-address", method="DELETE")
        self.assertEqual(404, response.status_int)

    def test_delete_address(self):
        response = self.request_gce(
                "/fake_project/regions/nova/addresses/ip-172-24-4-227",
                method="DELETE")
        expected = {
            "status": "DONE",
            "kind": "compute#operation",
            "name": "stub",
            "region": "http://localhost/compute/v1beta15/projects/"
                "fake_project/regions/nova",
            "targetLink": "http://localhost/compute/v1beta15/projects/"
                "fake_project/regions/nova/addresses/ip-172-24-4-227",
            "operationType": "delete",
            "id": "0",
            "progress": 100,
            "targetId": "7878386898874730669",
            "selfLink": "http://localhost/compute/v1beta15/projects/"
                "fake_project/regions/nova/operations/stub"
        }
        self.assertEqual(200, response.status_int)
        self.assertDictEqual(expected, response.json_body)

    def test_create_address(self):
        request_body = {
            "name": "fake-address",
        }
        response = self.request_gce("/fake_project/regions/nova/addresses",
                                    method="POST",
                                    body=request_body)
        self.assertEqual(200, response.status_int)
        expected = {
            "status": "DONE",
            "kind": "compute#operation",
            "name": "stub",
            "region": "http://localhost/compute/v1beta15/projects/"
                "fake_project/regions/nova",
            "targetLink": "http://localhost/compute/v1beta15/projects/"
                "fake_project/regions/nova/addresses/ip-10-20-30-40",
            "operationType": "insert",
            "id": "0",
            "progress": 100,
            "targetId": "3196393817195045231",
            "selfLink": "http://localhost/compute/v1beta15/projects/"
                        "fake_project/regions/nova/operations/stub"
        }
        self.assertDictEqual(expected, response.json_body)
