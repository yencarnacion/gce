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
import inspect
import uuid

from novaclient.client import exceptions as nova_exceptions

from gceapi.tests.api import utils


FAKE_DETAILED_ZONES = [utils.to_obj({
    u'zoneState': {
        u'available': True},
    u'hosts': {
        u'grizzly': {
            u'nova-conductor': {
                u'available': True,
                u'active': True,
                u'updated_at': u'2013-12-24T14:14:47.000000'},
            u'nova-consoleauth': {
                u'available': True,
                u'active': True,
                u'updated_at': u'2013-12-24T14:14:49.000000'},
            u'nova-scheduler': {
                u'available': True,
                u'active': True,
                u'updated_at': u'2013-12-24T14:14:48.000000'},
            u'nova-cert': {
                u'available': True,
                u'active': True,
                u'updated_at': u'2013-12-24T14:14:49.000000'}}},
    u'zoneName': u'internal'
}), utils.to_obj({
    u'zoneState': {
        u'available': True},
    u'hosts': {
        u'grizzly': {
            u'nova-compute': {
                u'available': True,
                u'active': True,
                u'updated_at': u'2013-12-24T14:14:47.000000'}}},
    u'zoneName': u'nova'
})]

FAKE_SIMPLE_ZONES = [utils.to_obj({
    u'zoneState': {
        u'available': True},
    u'hosts': None,
    u'zoneName': u'nova'
})]


FAKE_FLAVORS = [utils.to_obj({
    u'name': u'm1.small',
    u'links': [],
    u'ram': 2048,
    u'OS-FLV-DISABLED:disabled': False,
    u'vcpus': 1,
    u'swap': u'',
    u'os-flavor-access:is_public': True,
    u'rxtx_factor': 1.0,
    u'OS-FLV-EXT-DATA:ephemeral': 0,
    u'disk': 20,
    u'id': u'2'
}), utils.to_obj({
    u'name': u'm1.large',
    u'links': [],
    u'ram': 8192,
    u'OS-FLV-DISABLED:disabled': False,
    u'vcpus': 4,
    u'swap': u'',
    u'os-flavor-access:is_public': True,
    u'rxtx_factor': 1.0,
    u'OS-FLV-EXT-DATA:ephemeral': 870,
    u'disk': 80,
    u'id': u'4'
})]


FAKE_SECURITY_GROUPS = [
    utils.to_obj({
        "rules": [
            {
                "from_port": None,
                "ip_protocol": None,
                "to_port": None,
                "ip_range": {},
                "id": "3f8a140e-8d34-49c5-8cf2-5bec936b6c5c",
            },
            {
                "from_port": None,
                "ip_protocol": None,
                "to_port": None,
                "ip_range": {},
                "id": "9b0006c7-5e58-4b8e-a081-f0381c44bb2f",
            },
        ],
        "project_id": "6678c02984ce4df8b26912db30481637",
        "id": "2cfdbf3a-0564-4b3b-bb85-00eb8d518f0c",
        "name": "default",
        "description": "default",
    }),
    utils.to_obj({
        "rules": [
            {
                "from_port": 223,
                "ip_protocol": "udp",
                "to_port": 322,
                "ip_range": {"cidr": "55.0.0.0/24"},
                "id": "26f6c9e4-d8ca-4a96-b752-b848716f05f5",
            },
            {
                "from_port": -1,
                "ip_protocol": "icmp",
                "to_port": -1,
                "ip_range": {"cidr": "44.0.0.0/24"},
                "id": "4a2f2805-cde0-4515-9910-f2f8e77ba5f7",
            },
            {
                "from_port": 1234,
                "ip_protocol": "tcp",
                "to_port": 1234,
                "ip_range": {"cidr": "44.0.0.0/24"},
                "id": "e137dae4-ea4e-401d-8941-96a207e435b9",
            },
            {
                "from_port": -1,
                "ip_protocol": "icmp",
                "to_port": -1,
                "ip_range": {"cidr": "55.0.0.0/24"},
                "id": "e6a866a8-969a-41d9-b621-964a50f46381",
            },
            {
                "from_port": 223,
                "ip_protocol": "udp",
                "to_port": 322,
                "ip_range": {"cidr": "44.0.0.0/24"},
                "id": "f830670e-f90f-477f-9605-e871640cf8c2",
            },
            {
                "from_port": 1234,
                "ip_protocol": "tcp",
                "to_port": 1234,
                "ip_range": {"cidr": "55.0.0.0/24"},
                "id": "fbd2ada0-c5fc-4047-9558-2fb90874c8b3",
            },
        ],
        "project_id": "6678c02984ce4df8b26912db30481637",
        "id": "a4ab9c5f-f0b5-4952-8e76-6a8ca0d0a402",
        "name": "fake-firewall-1",
        "description": "simple firewall-=#=-private",
    }),
    utils.to_obj({
        "rules": [],
        "project_id": "6678c02984ce4df8b26912db30481637",
        "id": "c3859194-f111-4f24-b93b-095b056f38e2",
        "name": "fake-firewall-2",
        "description": "openstack sg w/o rules",
    }),
    utils.to_obj({
        "rules": [
            {
                "from_port": 1000,
                "ip_protocol": "tcp",
                "to_port": 2000,
                "ip_range": {"cidr": "77.0.0.0/24"},
                "id": "01ecc4c4-41be-4af1-9a64-e2f866176001",
            },
            {
                "from_port": 1000,
                "ip_protocol": "tcp",
                "to_port": 2000,
                "ip_range": {},
                "id": "8709247a-afd8-4673-aac4-e22d8432a31e",
            },
            {
                "from_port": 1000,
                "ip_protocol": "tcp",
                "to_port": 2000,
                "ip_range": {"cidr": "78.0.0.0/24"},
                "id": "d67e8103-b32b-428b-bd20-8337b95456f1",
            },
        ],
        "project_id": "6678c02984ce4df8b26912db30481637",
        "id": "b599598d-41b9-4075-a47e-019ba785c243",
        "name": "fake-firewall-3",
        "description": ("openstack sg with cidr & secgroup rules"
                        "-=#=-private"),
    }),
    utils.to_obj({
        "rules": [
            {
                "from_port": 5678,
                "ip_protocol": "tcp",
                "to_port": 5678,
                "ip_range": {"cidr": "66.0.0.0/24"},
                "id": "0642de5e-3c59-4c1c-8816-be6998c3c8a2",
            },
            {
                "from_port": 1234,
                "ip_protocol": "tcp",
                "to_port": 1234,
                "ip_range": {"cidr": "66.0.0.0/24"},
                "id": "b1a2b159-76e5-4baf-926a-a4ce09098377",
            },
            {
                "from_port": 1234,
                "ip_protocol": "tcp",
                "to_port": 1234,
                "ip_range": {"cidr": "88.0.0.0/24"},
                "id": "f7abbaab-f4fe-49fb-ac7f-bd8c49e60c61",
            },
        ],
        "project_id": "6678c02984ce4df8b26912db30481637",
        "id": "fac84db7-aded-4152-a29e-5db00e052233",
        "name": "fake-firewall-4",
        "description": ("openstack sg too complex to translate into gce "
                        "rules"),
    }),
    utils.to_obj({
        "rules": [
            {
                "from_port": 6666,
                "ip_protocol": "tcp",
                "to_port": 6666,
                "ip_range": {"cidr": "111.0.0.0/24"},
                "id": "634a199e-fb97-41d2-b12f-273c23a1c065"
            },
            {
                "from_port": 5555,
                "ip_protocol": "tcp",
                "to_port": 5555,
                "ip_range": {"cidr": "222.0.0.0/24"},
                "id": "bf34b3b0-29aa-4abf-a686-f29d9fb342d8"
            },
            {
                "from_port": -1,
                "ip_protocol": "icmp",
                "to_port": -1,
                "ip_range": {},
                "id": "fdf5dbe1-e824-46a6-a4d3-d2e37843a6d2"
            },
        ],
        "project_id": "6678c02984ce4df8b26912db30481637",
        "id": "03060521-fe0b-425f-bf33-d5061d58bae9",
        "name": "fake-firewall-5",
        "description": "openstack sg with combined & too complex rules",
    }),
    utils.to_obj({
        "rules": [
            {
                "from_port": 0,
                "ip_protocol": "icmp",
                "to_port": 8,
                "ip_range": {"cidr": "100.0.0.0/24"},
                "id": "ae452a08-af3b-4d6a-b38e-2f4acad63331",
            },
        ],
        "project_id": "6678c02984ce4df8b26912db30481637",
        "id": "d4c41e39-159c-4f96-8176-86c7b177880f",
        "name": "fake-firewall-6",
        "description": "openstack sg with too complex icmp rule",
    }),
    utils.to_obj({
        "rules": [
            {
                "from_port": -1,
                "ip_protocol": "icmp",
                "to_port": -1,
                "ip_range": {"cidr": "110.0.0.0/24"},
                "id": "e2bc37af-529e-4ab3-8f41-358f3f9e62ab",
            },
        ],
        "project_id": "6678c02984ce4df8b26912db30481637",
        "id": "1aaa637b-87f4-4e27-bc86-ff63d30264b2",
        "name": "to-delete-firewall",
        "description": "firewall to delete test-=#=-private",
    }),
]


class FakeClassWithFind(object):
    def list(self):
        pass

    def find(self, **kwargs):
        matches = self.findall(**kwargs)
        num_matches = len(matches)
        if num_matches == 0:
            msg = "No %s matching %s." % (self.__class__.__name__, kwargs)
            raise nova_exceptions.NotFound(404, msg)
        elif num_matches > 1:
            raise nova_exceptions.NoUniqueMatch
        else:
            return matches[0]

    def findall(self, **kwargs):
        found = []
        searches = kwargs.items()

        detailed = True
        list_kwargs = {}

        list_argspec = inspect.getargspec(self.list)
        if 'detailed' in list_argspec.args:
            detailed = ("human_id" not in kwargs and
                        "name" not in kwargs and
                        "display_name" not in kwargs)
            list_kwargs['detailed'] = detailed

        if 'is_public' in list_argspec.args and 'is_public' in kwargs:
            is_public = kwargs['is_public']
            list_kwargs['is_public'] = is_public
            if is_public is None:
                tmp_kwargs = kwargs.copy()
                del tmp_kwargs['is_public']
                searches = tmp_kwargs.items()

        listing = self.list(**list_kwargs)

        for obj in listing:
            try:
                if all(getattr(obj, attr) == value
                        for (attr, value) in searches):
                    if detailed:
                        found.append(obj)
                    else:
                        found.append(self.get(obj.id))
            except AttributeError:
                continue

        return found


class FakeNovaClient(object):
    def __init__(self, version, *args, **kwargs):
        self._security_group = None

    @property
    def client(self):
        return self

    @property
    def availability_zones(self):
        class FakeAvailabilityZones(object):
            def list(self, detailed=True):
                if detailed:
                    return FAKE_DETAILED_ZONES
                return FAKE_SIMPLE_ZONES

        return FakeAvailabilityZones()

    @property
    def flavors(self):
        class FakeFlavors(FakeClassWithFind):
            def list(self, detailed=True, is_public=True):
                return FAKE_FLAVORS

            def get(self, flavor):
                flavor_id = utils.get_id(flavor)
                for flavor in FAKE_FLAVORS:
                    if flavor.id == flavor_id:
                        return flavor
                raise nova_exceptions.NotFound()

        return FakeFlavors()

    @property
    def keypairs(self):
        class FakeKeypairs(object):
            def get(self, keypair):
                raise nova_exceptions.NotFound()

            def create(self, name, public_key=None):
                pass

            def delete(self, key):
                raise nova_exceptions.NotFound()

            def list(self):
                return []

        return FakeKeypairs()

    @property
    def servers(self):
        class FakeServers(object):
            def get(self, server):
                pass

            def list(self, detailed=True, search_opts=None,
                     marker=None, limit=None):
                return []

            def create(self, name, image, flavor, meta=None, files=None,
                       reservation_id=None, min_count=None,
                       max_count=None, security_groups=None, userdata=None,
                       key_name=None, availability_zone=None,
                       block_device_mapping=None, block_device_mapping_v2=None,
                       nics=None, scheduler_hints=None,
                       config_drive=None, disk_config=None, **kwargs):
                pass

            def add_floating_ip(self, server, address, fixed_address=None):
                pass

            def remove_floating_ip(self, server, address):
                pass

            def delete(self, server):
                pass

            def reboot(self, server, reboot_type):
                pass

        return FakeServers()

    @property
    def security_groups(self):
        class FakeSecurityGroups(FakeClassWithFind):
            _secgroups = FAKE_SECURITY_GROUPS

            def list(self):
                return self._secgroups

            def get(self, sg_id):
                secgroup = next((secgroup
                                 for secgroup in self._secgroups
                                 if secgroup.id == sg_id), None)
                if secgroup is None:
                    raise nova_exceptions.NotFound(
                            404, "Security group %s not found" % sg_id)
                return secgroup

            def create(self, name, description):
                secgroup = utils.to_obj({
                    "name": name,
                    "description": description,
                    "rules": [],
                    "project_id": "6678c02984ce4df8b26912db30481637",
                    "id": "5707a6f0-799d-4739-8740-3efc73f122aa",
                })
                self._secgroups = copy.deepcopy(self._secgroups)
                self._secgroups.append(secgroup)
                return secgroup

            def delete(self, security_group):
                pass

            def add_rule(self, sg_id, ip_protocol, from_port, to_port, cidr):
                secgroup = self.get(sg_id)
                rule = {
                    "id": uuid.uuid4(),
                    "ip_protocol": ip_protocol,
                    "from_port": from_port,
                    "to_port": to_port,
                    "ip_range": {"cidr": cidr},
                }
                secgroup.rules.append(rule)

        if self._security_group is None:
            self._security_group = FakeSecurityGroups()
        return self._security_group

    @property
    def security_group_rules(self):
        class FakeSecurityGroupRules(object):
            def __init__(self, nova_client):
                self.security_groups = nova_client.security_groups

            def create(self, sg_id, ip_protocol, from_port, to_port, cidr):
                self.security_groups.add_rule(sg_id, ip_protocol, from_port,
                                              to_port, cidr)

        return FakeSecurityGroupRules(self)


def fake_discover_extensions(self, version):
    return list()
