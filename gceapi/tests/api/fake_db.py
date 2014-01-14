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
import fixtures

from gceapi import db


ITEMS = [
    {
        "kind": "network",
        "id": "734b9c83-3a8b-4350-8fbf-d40f571ee163",
        "creationTimestamp": "2013-12-25T09:05:07.396957Z",
        "description": "main network",
    },
    {
        "kind": "route",
        "id": ("734b9c83-3a8b-4350-8fbf-d40f571ee163//"
               "eee5ba4f-c67e-40ec-8595-61b8e2bb715a//"
               "32.44.64.0/24//"
               "10.0.0.32//"
               "custom-route-1"),
        "creationTimestamp": "2013-12-25T09:05:07.396957Z",
        "description": "route for 32.44.64.0/24",
    },
    {
        "kind": "route",
        "id": ("734b9c83-3a8b-4350-8fbf-d40f571ee163//"
               "22be757a-a426-42fb-8e4b-b4c876f49f62//"
               "40.81.234.0/24//"
               "10.0.0.107//"
               "obsolete-route"),
        "creationTimestamp": "2013-12-25T09:05:07.396957Z",
        "description": "route for 40.81.234.0/24",
    },
    {
        "kind": "instance",
        "id": "d6957005-3ce7-4727-91d2-ae37fe5a199a",
        "description": "i1 description",
    },
    {
        "kind": "instance",
        "id": "6472359b-d46b-4629-83a9-d2ec8d99468c",
        "description": "i2 description",
    },
    {
        "kind": "access_config",
        "id": "i1-192.168.138.196",
        "instance_name": "i1",
        "nic": "private",
        "name": "ip for i1",
        "type": "ONE_TO_ONE_NAT",
        "addr": "192.168.138.196"
    },
    {
        "kind": "attached_disk",
        "id": "i1-ab8829ad-eec1-44a2-8068-d7f00c53ee90",
        "instance_name": "i1",
        "name": "christmas-tree",
        "volume_id": "ab8829ad-eec1-44a2-8068-d7f00c53ee90"
    },
    {
        "kind": "image",
        "id": "60ff30c2-64b6-4a97-9c17-322eebc8bd60",
        "description": "christmas-tree",
        "image_ref": "http://fake_url/fake_resource"
    },
    {
        "kind": "firewall",
        "id": "a4ab9c5f-f0b5-4952-8e76-6a8ca0d0a402",
        "creationTimestamp": "2013-12-25T09:01:00.396957Z",
        "network_name": "private"
    },
    {
        "kind": "firewall",
        "id": "b599598d-41b9-4075-a47e-019ba785c243",
        "creationTimestamp": "2013-12-25T09:02:00.396957Z",
        "network_name": "private"
    },
    {
        "kind": "firewall",
        "id": "1aaa637b-87f4-4e27-bc86-ff63d30264b2",
        "creationTimestamp": "2013-12-25T09:03:00.396957Z",
        "network_name": "private"
    }
]


class DBFixture(fixtures.Fixture):
    def __init__(self, stubs):
        super(DBFixture, self).__init__()
        self.stubs = stubs
        self.items = copy.copy(ITEMS)

    def setUp(self):
        super(DBFixture, self).setUp()
        self.stubs.Set(db, "add_item", self.fake_add_item)
        self.stubs.Set(db, "delete_item", self.fake_delete_item)
        self.stubs.Set(db, "get_items", self.fake_get_items)
        self.stubs.Set(db, "get_item_by_id", self.fake_get_item_by_id)
        self.stubs.Set(db, "get_item_by_name", self.fake_get_item_by_name)

    def fake_add_item(self, context, kind, data):
        if any(item["kind"] == kind and item["id"] == data["id"] and
               (data.get("name") is None or
                item.get("name") == data.get("name") and data.get)
               for item in self.items):
            raise Exception("Duplicate entry")
        item = copy.copy(data)
        item["kind"] = kind
        self.items.append(item)
        return data

    def fake_delete_item(self, context, kind, item_id):
        self.items = [item for item in self.items
                      if item["kind"] == kind and item["id"] == item_id]

    def fake_get_items(self, context, kind):
        return [copy.copy(item) for item in self.items
                if item["kind"] == kind]

    def fake_get_item_by_id(self, context, kind, item_id):
        return next((copy.copy(item) for item in self.items
                     if item["kind"] == kind and item["id"] == item_id), None)

    def fake_get_item_by_name(self, context, kind, name):
        return next((copy.copy(item) for item in self.items
                     if item["kind"] == kind and item["name"] == name), None)
