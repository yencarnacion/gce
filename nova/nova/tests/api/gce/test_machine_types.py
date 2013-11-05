#    Copyright 2012 Cloudscaling Group, Inc
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

from nova.api.gce import machine_types
import nova.compute.flavors as instance_types
from nova import exception
from nova.tests.api.gce import common

FAKE_FLAVORS = {
        'm1.small': {
            'memory_mb': 2048L,
            'root_gb': 20L,
            'deleted_at': None,
            'name': u'm1.small',
            'deleted': 0L,
            'created_at': "2013-04-25T13:32:45.000000",
            'ephemeral_gb': 0L,
            'updated_at': None,
            'disabled': False,
            'vcpus': 1L,
            'extra_specs': {},
            'swap': 0L,
            'rxtx_factor': 1.0,
            'is_public': True,
            'flavorid': u'2',
            'vcpu_weight': None,
            'id': 5L},
        'm1.large': {
            'memory_mb': 8192L,
            'root_gb': 80L,
            'deleted_at': None,
            'name': u'm1.large',
            'deleted': 0L,
            'created_at': "2013-04-25T13:32:45.000000",
            'ephemeral_gb': 870L,
            'updated_at': None,
            'disabled': False,
            'vcpus': 4L,
            'extra_specs': {},
            'swap': 0L,
            'rxtx_factor': 1.0,
            'is_public': True,
            'flavorid': u'4',
            'vcpu_weight': None,
            'id': 4L}
    }

EXPECTED_FLAVORS = [{
        "kind": "compute#machineType",
        "id": 7739288395178120473,
        "creationTimestamp": "2013-04-25T13:32:45Z",
        "description": "",
        "name": "m1-small",
        "guestCpus": 1,
        "memoryMb": 2048,
        "imageSpaceGb": 20,
        "maximumPersistentDisks": 0,
        "maximumPersistentDisksSizeGb": 0,
        "zone": "http://localhost/compute/v1beta15/projects/fake_project"
            "/zones/nova",
        "selfLink": "http://localhost/compute/v1beta15/projects/fake_project"
            "/zones/nova/machineTypes/m1-small"
        },
        {
        "kind": "compute#machineType",
        "id": 6065497922195565467,
        "creationTimestamp": "2013-04-25T13:32:45Z",
        "description": "",
        "name": "m1-large",
        'scratchDisks': [{"diskGb": 870L}],
        "guestCpus": 4,
        "memoryMb": 8192,
        "imageSpaceGb": 80,
        "maximumPersistentDisks": 0,
        "maximumPersistentDisksSizeGb": 0,
        "zone": "http://localhost/compute/v1beta15/projects/fake_project"
            "/zones/nova",
        "selfLink": "http://localhost/compute/v1beta15/projects/fake_project"
            "/zones/nova/machineTypes/m1-large"
        }]


def fake_get_instance_type_by_name(name):
    try:
        return FAKE_FLAVORS[name]
    except KeyError:
        raise exception.InstanceTypeNotFound(flavor_id=name,
            instance_type_id=0)


def fake_instance_type_get_all(inactive=False, filters=None):
    return FAKE_FLAVORS


class MachineTypesTest(common.GCEControllerTest):
    def setUp(self):
        super(MachineTypesTest, self).setUp()

        self.stubs.Set(instance_types, "get_all_flavors",
                fake_instance_type_get_all)
        self.stubs.Set(instance_types,
                "get_flavor_by_name",
                fake_get_instance_type_by_name)

        self.controller = machine_types.Controller()

    def test_get_machine_type_by_invalid_name(self):
        response = self.request_gce(
            '/fake_project//zones/nova/machineTypes/wrongMachineType')
        self.assertEqual(404, response.status_int)

    def test_get_flavor_by_name(self):
        response = self.request_gce(
            '/fake_project/zones/nova/machineTypes/m1-small')
        expected = EXPECTED_FLAVORS[0]

        self.assertEqual(response.json_body, expected)

    def test_get_flavor_list(self):
        response = self.request_gce('/fake_project/zones/nova/machineTypes')
        expected = {
                "kind": "compute#machineTypeList",
                "id": "projects/fake_project/zones/nova/machineTypes",
                "selfLink": "http://localhost/compute/v1beta15/projects"
                    "/fake_project/zones/nova/machineTypes",
                "items": EXPECTED_FLAVORS
                }

        self.assertEqual(response.json_body, expected)

    def test_get_flavor_aggregated_list(self):
        response = self.request_gce('/fake_project/aggregated/machineTypes')

        expected_flavors2 = copy.deepcopy(EXPECTED_FLAVORS)
        for flavor in expected_flavors2:
            flavor["zone"] = flavor["zone"].replace("nova", "unavailable_zone")
            flavor["selfLink"] = flavor["selfLink"].replace(
                "nova", "unavailable_zone")
            # NOTE(apavlov) fix id due to changed selfLink
            # (gce_api calculate id from selfLink)
            hashed_link = hash(flavor["selfLink"])
            flavor["id"] = hashed_link if hashed_link >= 0 else -hashed_link

        expected = {
            "kind": "compute#machineTypeAggregatedList",
            "id": "projects/fake_project/aggregated/machineTypes",
            "selfLink": "http://localhost/compute/v1beta15/projects"
                "/fake_project/aggregated/machineTypes",
            "items": {
                "zones/nova": {
                    "machineTypes": EXPECTED_FLAVORS
                },
                "zones/unavailable_zone": {
                    "machineTypes": expected_flavors2
                }
            }
        }

        self.assertEqual(response.json_body, expected)
