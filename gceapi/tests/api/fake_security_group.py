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

from gceapi import exception


class FakeSecurityGroupService(object):

    _secgroups = [
        {
            "rules": [
                {
                    "from_port": None,
                    "protocol": None,
                    "to_port": None,
                    "parent_group_id": "2cfdbf3a-0564-4b3b-bb85-00eb8d518f0c",
                    "cidr": None,
                    "group_id": "2cfdbf3a-0564-4b3b-bb85-00eb8d518f0c",
                    "id": "3f8a140e-8d34-49c5-8cf2-5bec936b6c5c",
                },
                {
                    "from_port": None,
                    "protocol": None,
                    "to_port": None,
                    "parent_group_id": "2cfdbf3a-0564-4b3b-bb85-00eb8d518f0c",
                    "cidr": None,
                    "group_id": "2cfdbf3a-0564-4b3b-bb85-00eb8d518f0c",
                    "id": "9b0006c7-5e58-4b8e-a081-f0381c44bb2f",
                },
            ],
            "project_id": "6678c02984ce4df8b26912db30481637",
            "id": "2cfdbf3a-0564-4b3b-bb85-00eb8d518f0c",
            "name": "default",
            "description": "default",
        },
        {
            "rules": [
                {
                    "from_port": 223,
                    "protocol": "udp",
                    "to_port": 322,
                    "parent_group_id": "a4ab9c5f-f0b5-4952-8e76-6a8ca0d0a402",
                    "cidr": "55.0.0.0/24",
                    "group_id": None,
                    "id": "26f6c9e4-d8ca-4a96-b752-b848716f05f5",
                },
                {
                    "from_port": -1,
                    "protocol": "icmp",
                    "to_port": -1,
                    "parent_group_id": "a4ab9c5f-f0b5-4952-8e76-6a8ca0d0a402",
                    "cidr": "44.0.0.0/24",
                    "group_id": None,
                    "id": "4a2f2805-cde0-4515-9910-f2f8e77ba5f7",
                },
                {
                    "from_port": 1234,
                    "protocol": "tcp",
                    "to_port": 1234,
                    "parent_group_id": "a4ab9c5f-f0b5-4952-8e76-6a8ca0d0a402",
                    "cidr": "44.0.0.0/24",
                    "group_id": None,
                    "id": "e137dae4-ea4e-401d-8941-96a207e435b9",
                },
                {
                    "from_port": -1,
                    "protocol": "icmp",
                    "to_port": -1,
                    "parent_group_id": "a4ab9c5f-f0b5-4952-8e76-6a8ca0d0a402",
                    "cidr": "55.0.0.0/24",
                    "group_id": None,
                    "id": "e6a866a8-969a-41d9-b621-964a50f46381",
                },
                {
                    "from_port": 223,
                    "protocol": "udp",
                    "to_port": 322,
                    "parent_group_id": "a4ab9c5f-f0b5-4952-8e76-6a8ca0d0a402",
                    "cidr": "44.0.0.0/24",
                    "group_id": None,
                    "id": "f830670e-f90f-477f-9605-e871640cf8c2",
                },
                {
                    "from_port": 1234,
                    "protocol": "tcp",
                    "to_port": 1234,
                    "parent_group_id": "a4ab9c5f-f0b5-4952-8e76-6a8ca0d0a402",
                    "cidr": "55.0.0.0/24",
                    "group_id": None,
                    "id": "fbd2ada0-c5fc-4047-9558-2fb90874c8b3",
                },
            ],
            "project_id": "6678c02984ce4df8b26912db30481637",
            "id": "a4ab9c5f-f0b5-4952-8e76-6a8ca0d0a402",
            "name": "fake-firewall-1",
            "description": "simple firewall-=#=-private",
        },
        {
            "rules": [],
            "project_id": "6678c02984ce4df8b26912db30481637",
            "id": "c3859194-f111-4f24-b93b-095b056f38e2",
            "name": "fake-firewall-2",
            "description": "openstack sg w/o rules",
        },
        {
            "rules": [
                {
                    "from_port": 1000,
                    "protocol": "tcp",
                    "to_port": 2000,
                    "parent_group_id": "b599598d-41b9-4075-a47e-019ba785c243",
                    "cidr": "77.0.0.0/24",
                    "group_id": None,
                    "id": "01ecc4c4-41be-4af1-9a64-e2f866176001",
                },
                {
                    "from_port": 1000,
                    "protocol": "tcp",
                    "to_port": 2000,
                    "parent_group_id": "b599598d-41b9-4075-a47e-019ba785c243",
                    "cidr": None,
                    "group_id": "a4ab9c5f-f0b5-4952-8e76-6a8ca0d0a402",
                    "id": "8709247a-afd8-4673-aac4-e22d8432a31e",
                },
                {
                    "from_port": 1000,
                    "protocol": "tcp",
                    "to_port": 2000,
                    "parent_group_id": "b599598d-41b9-4075-a47e-019ba785c243",
                    "cidr": "78.0.0.0/24",
                    "group_id": None,
                    "id": "d67e8103-b32b-428b-bd20-8337b95456f1",
                },
            ],
            "project_id": "6678c02984ce4df8b26912db30481637",
            "id": "b599598d-41b9-4075-a47e-019ba785c243",
            "name": "fake-firewall-3",
            "description": ("openstack sg with cidr & secgroup rules"
                            "-=#=-private"),
        },
        {
            "rules": [
                {
                    "from_port": 5678,
                    "protocol": "tcp",
                    "to_port": 5678,
                    "parent_group_id": "fac84db7-aded-4152-a29e-5db00e052233",
                    "cidr": "66.0.0.0/24",
                    "group_id": None,
                    "id": "0642de5e-3c59-4c1c-8816-be6998c3c8a2",
                },
                {
                    "from_port": 1234,
                    "protocol": "tcp",
                    "to_port": 1234,
                    "parent_group_id": "fac84db7-aded-4152-a29e-5db00e052233",
                    "cidr": "66.0.0.0/24",
                    "group_id": None,
                    "id": "b1a2b159-76e5-4baf-926a-a4ce09098377",
                },
                {
                    "from_port": 1234,
                    "protocol": "tcp",
                    "to_port": 1234,
                    "parent_group_id": "fac84db7-aded-4152-a29e-5db00e052233",
                    "cidr": "88.0.0.0/24",
                    "group_id": None,
                    "id": "f7abbaab-f4fe-49fb-ac7f-bd8c49e60c61",
                },
            ],
            "project_id": "6678c02984ce4df8b26912db30481637",
            "id": "fac84db7-aded-4152-a29e-5db00e052233",
            "name": "fake-firewall-4",
            "description": ("openstack sg too complex to translate into gce "
                            "rules"),
        },
        {
            "rules": [
                {
                    "from_port": 6666,
                    "protocol": "tcp",
                    "to_port": 6666,
                    "parent_group_id": "03060521-fe0b-425f-bf33-d5061d58bae9",
                    "cidr": "111.0.0.0/24",
                    "group_id": None,
                    "id": "634a199e-fb97-41d2-b12f-273c23a1c065"
                },
                {
                    "from_port": 5555,
                    "protocol": "tcp",
                    "to_port": 5555,
                    "parent_group_id": "03060521-fe0b-425f-bf33-d5061d58bae9",
                    "cidr": "222.0.0.0/24",
                    "group_id": None,
                    "id": "bf34b3b0-29aa-4abf-a686-f29d9fb342d8"
                },
                {
                    "from_port": -1,
                    "protocol": "icmp",
                    "to_port": -1,
                    "parent_group_id": "03060521-fe0b-425f-bf33-d5061d58bae9",
                    "cidr": None,
                    "group_id": "a4ab9c5f-f0b5-4952-8e76-6a8ca0d0a402",
                    "id": "fdf5dbe1-e824-46a6-a4d3-d2e37843a6d2"
                },
            ],
            "project_id": "6678c02984ce4df8b26912db30481637",
            "id": "03060521-fe0b-425f-bf33-d5061d58bae9",
            "name": "fake-firewall-5",
            "description": "openstack sg with combined & too complex rules",
        },
        {
            "rules": [
                {
                    "from_port": 0,
                    "protocol": "icmp",
                    "to_port": 8,
                    "parent_group_id": "d4c41e39-159c-4f96-8176-86c7b177880f",
                    "cidr": "100.0.0.0/24",
                    "group_id": None,
                    "id": "ae452a08-af3b-4d6a-b38e-2f4acad63331",
                },
            ],
            "project_id": "6678c02984ce4df8b26912db30481637",
            "id": "d4c41e39-159c-4f96-8176-86c7b177880f",
            "name": "fake-firewall-6",
            "description": "openstack sg with too complex icmp rule",
        },
        {
            "rules": [
                {
                    "from_port": -1,
                    "protocol": "icmp",
                    "to_port": -1,
                    "parent_group_id": "1aaa637b-87f4-4e27-bc86-ff63d30264b2",
                    "cidr": "110.0.0.0/24",
                    "group_id": None,
                    "id": "e2bc37af-529e-4ab3-8f41-358f3f9e62ab",
                },
            ],
            "project_id": "6678c02984ce4df8b26912db30481637",
            "id": "1aaa637b-87f4-4e27-bc86-ff63d30264b2",
            "name": "to-delete-firewall",
            "description": "firewall to delete test-=#=-private",
        },
    ]
    _new_secgroup_attributes = {
        "new-firewall": {
            "rules": [],
            "project_id": "6678c02984ce4df8b26912db30481637",
            "id": "5707a6f0-799d-4739-8740-3efc73f122aa",
        },
    }

    def list(self, context, names=None, ids=None, project=None,
             search_opts=None):
        return [copy.deepcopy(secgroup)
                for secgroup in self._secgroups
                if (secgroup["name"] in names if names is not None else True)]

    def create_security_group(self, context, name, description):
        secgroup = {"name": name, "description": description}
        secgroup.update(self._new_secgroup_attributes[name])
        self._secgroups.append(secgroup)
        return secgroup

    def add_rules(self, context, id, name, vals):
        secgroup = next(sg for sg in self._secgroups if sg["id"] == id)
        if secgroup is None:
            raise exception.Invalid()
        for rule in vals:
            if ("from_port" not in rule or
                    "to_port" not in rule or
                    "protocol" not in rule or
                    rule["protocol"] not in ["icmp", "tcp", "udp"] or
                    "cidr" not in rule or
                    "parent_group_id" not in rule or
                    rule["parent_group_id"] != id):
                raise exception.Invalid()
            rule = copy.deepcopy(rule)
            rule["id"] = uuid.uuid4()
            rule["group_id"] = None
            secgroup["rules"].append(rule)
        return rule

    def destroy(self, context, security_group):
        sg_index = 0
        sg_id = security_group["id"]
        for sg in self._secgroups:
            if sg["id"] != sg_id:
                sg_index += 1
                continue
            del self._secgroups[sg_index]
            return True
        raise exception.Invalid()

    def add_to_instance(self, context, instance, security_group_name):
        pass

    def remove_from_instance(self, context, instance, security_group_name):
        pass
