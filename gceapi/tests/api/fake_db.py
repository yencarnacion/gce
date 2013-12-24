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


def setStubs(stubs):
#     stubs.Set(db, 'get_all_gce_routes',
#               fake_get_all_gce_routes)
#     stubs.Set(db, 'get_gce_route_synonyms_count',
#               fake_get_gce_route_synonyms_count)
#     stubs.Set(db, 'add_gce_route',
#               fake_add_gce_route)
#     stubs.Set(db, 'delete_gce_route',
#               fake_delete_gce_route)
    pass


def fake_get_all_gce_routes(context):
    return [
        {
            "id": 1,
            "network_id": "734b9c83-3a8b-4350-8fbf-d40f571ee163",
            "port_id": "eee5ba4f-c67e-40ec-8595-61b8e2bb715a",
            "name": "custom-route-1",
            "destination": "32.44.64.0/24",
            "nexthop": "10.0.0.32",
            "description": "route for 32.44.64.0/24",
        },
        {
            "id": 2,
            "network_id": "734b9c83-3a8b-4350-8fbf-d40f571ee163",
            "port_id": "22be757a-a426-42fb-8e4b-b4c876f49f62",
            "name": "obsolete-route",
            "destination": "40.81.234.0/24",
            "nexthop": "10.0.0.107",
            "description": "route for 40.81.234.0/24",
        },
    ]


def fake_get_gce_route_synonyms_count(context, network_id,
                                      destination, nexthop):
    return len([r for r in fake_get_all_gce_routes(context)
               if (r["network_id"] == network_id and
                   r["destination"] == destination and
                   r["nexthop"] == nexthop)])


def fake_add_gce_route(context, route):
    route["id"] = 111
    if "port_id" not in route:
        route["port_id"] = None
    if "description" not in route:
        route["description"] = None
    if "nexthop" not in route:
        route["nexthop"] = None
    return route


def fake_delete_gce_route(context, name_id):
    pass
