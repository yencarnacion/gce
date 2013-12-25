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

from gceapi import db
from gceapi import exception


def setStubs(stubs):
    stubs.Set(db, "add_item", fake_add_item)
    stubs.Set(db, "delete_item", fake_delete_item)
    stubs.Set(db, "get_items", fake_get_items)
    stubs.Set(db, "get_item_by_id", fake_get_item_by_id)
    stubs.Set(db, "get_item_by_name", fake_get_item_by_name)


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
]


def fake_add_item(context, kind, data):
    if any(item["kind"] == kind and item["id"] == data["id"] and
           (data.get("name") is None or
            item.get("name") == data.get("name") and data.get)
           for item in ITEMS):
        raise Exception("Duplicate entry")
    return data


def fake_delete_item(context, kind, item_id):
    # TODO(ft): uncomment this when switch to fixtures
#     item = next((item for item in ITEMS
#                  if item["kind"] == kind and item["id"] == item_id), None)
#     if item is None:
#         raise Exception("Item not found")
    pass


def fake_get_items(context, kind):
    return [item for item in ITEMS if item["kind"] == kind]


def fake_get_item_by_id(context, kind, item_id):
    return next((item for item in ITEMS
                 if item["kind"] == kind and item["id"] == item_id), None)


def fake_get_item_by_name(context, kind, name):
    return next((item for item in ITEMS
                 if item["kind"] == kind and item["name"] == name), None)
