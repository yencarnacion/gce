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

from nova import exception
from nova.api.gce import instances
from nova.compute import api as compute_api
from nova.tests.api.gce import common
from nova.tests.api.gce import fake_instance

EXPECTED_INSTANCES = [{
    "kind": "compute#instance",
    "id": 3991024138321713624,
    "creationTimestamp": "2013-08-14T13:45:32Z",
    "zone":
        "http://localhost/compute/v1beta15/projects/fake_project/zones/nova",
    "status": "RUNNING",
    "statusMessage": "active",
    "name": "i1",
    "description": "i1",
    "machineType": "http://localhost/compute/v1beta15/projects/fake_project"
        "/zones/nova/machineTypes/m1-tiny",
    "image": "http://localhost/compute/v1beta15/projects/fake_project"
        "/global/images/fake-image-1",
#    "canIpForward": false,
    "networkInterfaces": [{
        "network": "http://localhost/compute/v1beta15/projects/fake_project"
            "/global/networks/private",
        "networkIP": "10.0.1.3",
        "name": "private",
        "accessConfigs": [{
            "kind": "compute#accessConfig",
            "type": "ONE_TO_ONE_NAT",
            "name": "192.168.138.196",
            "natIP": "192.168.138.196"
        }]
    }],
    "disks": [{
        "kind": "compute#attachedDisk",
        "index": 0,
        "type": "PERSISTENT",
        "mode": "READ_WRITE",
        "source": "http://localhost/compute/v1beta15/projects/fake_project"
            "/zones/nova/disks/i1",
        "deviceName": "vdc"
    }],
    "metadata": {
        "kind": "compute#metadata",
    },
    "selfLink": "http://localhost/compute/v1beta15/projects/fake_project"
        "/zones/nova/instances/i1"
}, {
    "kind": "compute#instance",
    "id": 3991024138321713621,
    "creationTimestamp": "2013-08-14T13:46:36Z",
    "zone": "http://localhost/compute/v1beta15/projects/fake_project"
        "/zones/nova",
    "status": "STOPPED",
    "statusMessage": "suspended",
    "name": "i2",
    "description": "i2",
    "machineType": "http://localhost/compute/v1beta15/projects/fake_project"
        "/zones/nova/machineTypes/m1-tiny",
    "image": "http://localhost/compute/v1beta15/projects/fake_project"
        "/global/images/fake-image-1",
#    "canIpForward": false,
    "networkInterfaces": [{
        "network": "http://localhost/compute/v1beta15/projects/fake_project"
            "/global/networks/default",
        "networkIP": "10.100.0.3",
        "name": "default",
        "accessConfigs": []
    }],
    "disks": [],
    "metadata": {
        "kind": "compute#metadata",
    },
    "selfLink": "http://localhost/compute/v1beta15/projects/fake_project"
        "/zones/nova/instances/i2"
}]


def fake_reset_instance(self, context, instance, reset_type):
    if reset_type != 'HARD':
        raise exception.InvalidParameterValue(err=reset_type)


def fake_delete_instance(self, context, instance):
    pass


def fake_create_instance(self, context, flavor,
        image_href, kernel_id=None, ramdisk_id=None,
        min_count=None, max_count=None,
        display_name=None, display_description=None,
        key_name=None, key_data=None, security_group=None,
        availability_zone=None, user_data=None, metadata=None,
        injected_files=None, admin_password=None,
        block_device_mapping=None, access_ip_v4=None,
        access_ip_v6=None, requested_networks=None, config_drive=None,
        auto_disk_config=None, scheduler_hints=None):
    instance = copy.deepcopy(fake_instance.FAKE_INSTANCES[1])
    instance['display_name'] = display_name
    return ([instance], "reservation_id")


class InstancesTest(common.GCEControllerTest):

    def setUp(self):
        super(InstancesTest, self).setUp()

        self.stubs.Set(compute_api.API, 'create', fake_create_instance)
        self.stubs.Set(compute_api.API, 'delete', fake_delete_instance)
        self.stubs.Set(compute_api.API, 'reboot', fake_reset_instance)

        self.controller = instances.Controller()

    def test_get_instance_by_invalid_name(self):
        response = self.request_gce('/fake_project/zones/nova/instances/fake')
        self.assertEqual(404, response.status_int)

    def test_get_instance_by_name(self):
        response = self.request_gce('/fake_project/zones/nova/instances/i1')

        self.assertEqual(200, response.status_int)
        self.assertEqual(response.json_body, EXPECTED_INSTANCES[0])

    def test_get_instance_list(self):
        response = self.request_gce('/fake_project/zones/nova/instances')
        expected = {
                "kind": "compute#instanceList",
                "id": "projects/fake_project/zones/nova/instances",
                "selfLink": "http://localhost/compute/v1beta15/projects"
                    "/fake_project/zones/nova/instances",
                "items": EXPECTED_INSTANCES
                }

        self.assertEqual(response.json_body, expected)

    def test_get_instance_aggregated_list(self):
        response = self.request_gce('/fake_project/aggregated/instances')

        expected = {
            "kind": "compute#instanceAggregatedList",
            "id": "projects/fake_project/aggregated/instances",
            "selfLink": "http://localhost/compute/v1beta15/projects"
                "/fake_project/aggregated/instances",
            "items": {
                "zones/nova": {
                    "instances": EXPECTED_INSTANCES
                },
            }
        }

        self.assertEqual(response.json_body, expected)

    def test_delete_instance_with_invalid_name(self):
        response = self.request_gce("/fake_project/zones/nova"
            "/instances/fake-instance", method="DELETE")
        self.assertEqual(404, response.status_int)

    def test_delete_instance(self):
        response = self.request_gce(
                "/fake_project/zones/nova/instances/i2",
                method="DELETE")
        expected = {
            "status": "DONE",
            "kind": "compute#operation",
            "name": "stub",
            "zone": "nova",
            "targetLink": "http://localhost/compute/v1beta15/projects/"
                          "fake_project/zones/nova/instances/i2",
            "operationType": "delete",
            "id": "0",
            "selfLink": "http://localhost/compute/v1beta15/projects/"
                        "fake_project/zones/nova/operations/stub"
        }
        self.assertEqual(200, response.status_int)
        self.assertDictEqual(expected, response.json_body)

    def test_reset_instance(self):
        response = self.request_gce(
                "/fake_project/zones/nova/instances/i1/reset",
                method="POST")
        expected = {
            "status": "DONE",
            "kind": "compute#operation",
            "name": "stub",
            "zone": "nova",
            "targetLink": "http://localhost/compute/v1beta15/projects/"
                          "fake_project/zones/nova/instances/i1",
            "operationType": "update",
            "id": "0",
            "selfLink": "http://localhost/compute/v1beta15/projects/"
                        "fake_project/zones/nova/operations/stub"
        }
        self.assertEqual(200, response.status_int)
        self.assertDictEqual(expected, response.json_body)

    def test_create_instance(self):
        request_body = {
            "name": "instance3",
            "description": "inst01descr",
            "machineType": "http://localhost/compute/v1beta15/projects/admin"
                "fake_project/zones/nova/m1-small",
            "image": "http://localhost/compute/v1beta15/projects/admin"
                "fake_project/global/fake-image-1",
            'networkInterfaces': [{
                'network': ("http://localhost/compute/v1beta15/projects"
                    "/admin/fake_project/global/private")
            }],
        }
        response = self.request_gce("/fake_project/zones/nova/instances",
                                    method="POST",
                                    body=request_body)
        self.assertEqual(200, response.status_int)
        expected = {
            "status": "DONE",
            "kind": "compute#operation",
            "name": "stub",
            "zone": "nova",
            "targetLink": "http://localhost/compute/v1beta15/projects/"
                          "fake_project/zones/nova/instances/instance3",
            "operationType": "insert",
            "id": "0",
            "selfLink": "http://localhost/compute/v1beta15/projects/"
                        "fake_project/zones/nova/operations/stub"
        }
        self.assertDictEqual(expected, response.json_body)

    def test_add_access_config(self):
        request_body = {
            "name": "192.168.138.196",
            "type": "ONE_TO_ONE_NAT",
            "natIP": "192.168.138.196"
        }
        response = self.request_gce("/fake_project/zones/nova"
            "/instances/i1/addAccessConfig?networkInterface=private",
            method="POST",
            body=request_body)
        expected = {'status': 'DONE',
            "status": "DONE",
            'kind': 'compute#operation',
            'name': 'stub',
            "zone": "nova",
            "targetLink": "http://localhost/compute/v1beta15/projects/"
                          "fake_project/zones/nova/instances/i1",
            "operationType": "insert",
            "id": "0",
            "selfLink": "http://localhost/compute/v1beta15/projects/"
                        "fake_project/zones/nova/operations/stub"
        }
        self.assertEqual(200, response.status_int)
        self.assertDictEqual(expected, response.json_body)

    def test_delete_access_config(self):
        response = self.request_gce("/fake_project/zones/nova/"
            "instances/i2/deleteAccessConfig?access-config=192.168.138.196",
            method="POST")
        expected = {'status': 'DONE',
            "status": "DONE",
            'kind': 'compute#operation',
            'name': 'stub',
            "zone": "nova",
            "targetLink": "http://localhost/compute/v1beta15/projects/"
                          "fake_project/zones/nova/instances/i2",
            "operationType": "delete",
            "id": "0",
            "selfLink": "http://localhost/compute/v1beta15/projects/"
                        "fake_project/zones/nova/operations/stub"
        }
        self.assertEqual(200, response.status_int)
        self.assertDictEqual(expected, response.json_body)
