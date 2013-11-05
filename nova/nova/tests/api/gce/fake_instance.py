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

import datetime

FAKE_INSTANCES = [{
    'vm_state': u'active',
    'availability_zone': None,
    'terminated_at': None,
    'ephemeral_gb': 0L,
    'instance_type_id': 2L,
    'user_data': None,
    'vm_mode': None,
    'deleted_at': None,
    'reservation_id': u'r-un0un40j',
    'id': 76L,
#    'security_groups': [
#        <nova.db.sqlalchemy.models.SecurityGroup object at 0x4bca250>,
#        <nova.db.sqlalchemy.models.SecurityGroup object at 0x4bca590>],
    'disable_terminate': False,
    'user_id': u'0ed9ed7b2004443f802142ecf364738b',
    'uuid': u'd0a267df-be69-45cf-9cc3-9f8db99cb767',
    'default_swap_device': None,
    'info_cache': {
        'network_info': [{
            "ovs_interfaceid": None,
            "network": {
                "bridge": "brqe87020c3-df",
                "subnets": [{
                    "ips": [{
                        "meta": {},
                        "version": 4,
                        "type": "fixed",
                        "floating_ips": [{
                            "meta": {},
                            "version": 4,
                            "type": "floating",
                            "address": "192.168.138.196"
                        }],
                        "address": "10.0.1.3"
                    }],
                    "version": 4,
                    "meta": {"dhcp_server": "10.0.1.2"},
                    "dns": [],
                    "routes": [],
                    "cidr": "10.0.1.0/24",
                    "gateway": {
                        "meta": {},
                        "version": 4,
                        "type": "gateway",
                        "address": "10.0.1.1"
                    }
                }],
                "meta": {
                    "injected": False,
                    "tenant_id": "bf907fe9f01342949e9693ca47e7d856",
                    "should_create_bridge": True
                },
                "id": "734b9c83-3a8b-4350-8fbf-d40f571ee163",
                "label": "private"
            },
            "devname": "tapf378990c-1e",
            "qbh_params": None,
            "meta": {},
            "address": "fa:16:3e:5c:0c:c9",
            "type": "bridge",
            "id": "f378990c-1eee-4305-8745-9090d45c4361",
            "qbg_params": None
        }]
    },
    'hostname': u'i1',
    'launched_on': u'apavlov-VirtualBox',
    'display_description': u'i1',
    'key_data': u'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDho5JqOxmtLsAcHi"\
        "bkBdsqzd0CrQ1TNDb9IDetG+c/XiSaG4Mhr+mXSDWvste9yAtqYojzkK58FN7mV"\
        "f6gAupAKFxuMOfDGuRNEl2JXZYDdiU22DtbMFJUwMH4j21xSqG+Oo51U7BhT9uY"\
        "DaPCD2c4PlpNcEMHiEMb4ZYzOM1WTIIpvQOFBCAtLu+l644snqbn4RvXHfeIWQb"\
        "ab2O9/E0TEnoUHKujk6ASnDue/7brNWtVTlcVBDlhdrgj9PwpuSJGGJcAyGuRgd"\
        "+hALEBWGyXJIJGmNuSyp4+jgAqiahjrkAqw8PiGKzWKVHHITRuEj0/BlsYC3NVh"\
        "y5TBjAxwlib devman@apavlov-VirtualBox',
    'kernel_id': u'',
    'config_drive': u'',
    'power_state': 1L,
    'default_ephemeral_device': None,
    'progress': 0L,
    'project_id': u'bf907fe9f01342949e9693ca47e7d856',
    'launched_at': datetime.datetime(2013, 8, 14, 13, 46, 23),
    'scheduled_at': datetime.datetime(2013, 8, 14, 13, 45, 32),
    'node': u'apavlov-VirtualBox',
    'ramdisk_id': u'',
    'access_ip_v6': None,
    'access_ip_v4': None,
    'deleted': 0L,
    'key_name': u'admin',
    'updated_at': datetime.datetime(2013, 8, 14, 13, 46, 23),
    'host': u'apavlov-VirtualBox',
    'architecture': None,
    'display_name': u'i1',
    'system_metadata': [
        {"deleted": 0, "key": "instance_type_memory_mb", "value": 512},
        {"deleted": 0, "key": "instance_type_swap", "value": 0},
        {"deleted": 0, "key": "instance_type_vcpu_weight", "value": None},
        {"deleted": 0, "key": "instance_type_root_gb", "value": 0},
        {"deleted": 0, "key": "instance_type_id", "value": 2},
        {"deleted": 0, "key": "instance_type_name", "value": "m1.tiny"},
        {"deleted": 0, "key": "instance_type_ephemeral_gb", "value": 0},
        {"deleted": 0, "key": "instance_type_rxtx_factor", "value": 1},
        {"deleted": 0, "key": "instance_type_flavorid", "value": 1},
        {"deleted": 0, "key": "instance_type_vcpus", "value": 1},
        {"deleted": 0, "key": "image_base_image_ref",
            "value": "60ff30c2-64b6-4a97-9c17-322eebc8bd60"},
    ],
    'task_state': None,
    'shutdown_terminate': False,
    'cell_name': None,
    'root_gb': 0L,
    'locked': False,
    'name': 'instance-0000004c',
    'created_at': datetime.datetime(2013, 8, 14, 13, 45, 32),
    'launch_index': 0L,
    'memory_mb': 512L,
    'vcpus': 1L,
    'image_ref': u'60ff30c2-64b6-4a97-9c17-322eebc8bd60',
    'root_device_name': u'/dev/vda',
    'auto_disk_config': None,
    'os_type': None,
    'metadata': []
},
{
    'vm_state': u'suspended',
    'availability_zone': None,
    'terminated_at': None,
    'ephemeral_gb': 0L,
    'instance_type_id': 2L,
    'user_data': None,
    'vm_mode': None,
    'deleted_at': None,
    'reservation_id': u'r-qbz5701v',
    'id': 77L,
#    'security_groups': [
#        <nova.db.sqlalchemy.models.SecurityGroup object at 0x4bca250>],
    'disable_terminate': False,
    'user_id': u'0ed9ed7b2004443f802142ecf364738b',
    'uuid': u'd6957005-3ce7-4727-91d2-ae37fe5a199a',
    'default_swap_device': None,
    'info_cache': {
        "network_info": [{
            "ovs_interfaceid": None,
            "network": {
                "bridge": "brqd4c3fa7f-42",
                 "subnets": [{
                    "ips": [{
                        "meta": {},
                        "version": 4,
                        "type": "fixed",
                        "floating_ips": [],
                        "address": "10.100.0.3"
                    }],
                    "version": 4,
                    "meta": {"dhcp_server": "10.100.0.2"},
                    "dns": [],
                    "routes": [],
                    "cidr": "10.100.0.0/24",
                    "gateway": {
                        "meta": {},
                        "version": 4,
                        "type": "gateway",
                        "address": "10.100.0.1"
                    }
                }],
                "meta": {
                    "injected": False,
                    "tenant_id": "bf907fe9f01342949e9693ca47e7d856",
                    "should_create_bridge": True
                },
                "id": "d4c3fa7f-42a8-4c0a-8841-4a2abb862e5e",
                "label": "default"
            },
            "devname": "tap4b8fb492-ac",
            "qbh_params": None,
            "meta": {},
            "address": "fa:16:3e:c1:f5:38",
            "type": "bridge",
            "id": "4b8fb492-acf5-40ca-9288-dab44f5cf509",
            "qbg_params": None
        }]
    },
    'hostname': u'i2',
    'launched_on': u'apavlov-VirtualBox',
    'display_description': u'i2',
    'key_data': None,
    'kernel_id': u'',
    'config_drive': u'',
    'power_state': 4L,
    'default_ephemeral_device': None,
    'progress': 0L,
    'project_id': u'bf907fe9f01342949e9693ca47e7d856',
    'launched_at': datetime.datetime(2013, 8, 14, 13, 46, 50),
    'scheduled_at': datetime.datetime(2013, 8, 14, 13, 46, 36),
    'node': u'apavlov-VirtualBox',
    'ramdisk_id': u'',
    'access_ip_v6': None,
    'access_ip_v4': None,
    'deleted': 0L,
    'key_name': None,
    'updated_at': datetime.datetime(2013, 8, 14, 13, 47, 11),
    'host': u'apavlov-VirtualBox',
    'architecture': None,
    'display_name': u'i2',
    'system_metadata': [
        {"deleted": 0, "key": "instance_type_memory_mb", "value": 512},
        {"deleted": 0, "key": "instance_type_swap", "value": 0},
        {"deleted": 0, "key": "instance_type_vcpu_weight", "value": None},
        {"deleted": 0, "key": "instance_type_root_gb", "value": 0},
        {"deleted": 0, "key": "instance_type_id", "value": 2},
        {"deleted": 0, "key": "instance_type_name", "value": "m1.tiny"},
        {"deleted": 0, "key": "instance_type_ephemeral_gb", "value": 0},
        {"deleted": 0, "key": "instance_type_rxtx_factor", "value": 1},
        {"deleted": 0, "key": "instance_type_flavorid", "value": 1},
        {"deleted": 0, "key": "instance_type_vcpus", "value": 1},
        {"deleted": 0, "key": "image_base_image_ref",
            "value": "60ff30c2-64b6-4a97-9c17-322eebc8bd60"},
    ],
    'task_state': None,
    'shutdown_terminate': False,
    'cell_name': None,
    'root_gb': 0L,
    'locked': False,
    'name': 'instance-0000004d',
    'created_at': datetime.datetime(2013, 8, 14, 13, 46, 36),
    'launch_index': 0L,
    'memory_mb': 512L,
    'vcpus': 1L,
    'image_ref': u'60ff30c2-64b6-4a97-9c17-322eebc8bd60',
    'root_device_name': u'/dev/vda',
    'auto_disk_config': None,
    'os_type': None,
    'metadata': []
}]


def fake_instance_get_all(self, context, search_opts=None, want_objects=False):
    if search_opts is None or "name" not in search_opts:
        return FAKE_INSTANCES
    name = search_opts["name"]
    return [i for i in FAKE_INSTANCES if i["display_name"] == name]


def fake_block_device_mapping_get_all_by_instance(context, inst_id):
    if inst_id != "d0a267df-be69-45cf-9cc3-9f8db99cb767":
        return []

    return [dict(volume_id="ab8829ad-eec1-44a2-8068-d7f00c53ee90",
                 device_name="vdc")]
