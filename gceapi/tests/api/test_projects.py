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

from keystoneclient.v2_0 import client as keystone_client

from gceapi.api import projects
from gceapi.tests.api import common


class FakeProject(object):
    @property
    def name(self):
        return "fake_project"

    @property
    def description(self):
        return None

    @property
    def id(self):
        return "bf907fe9f01342949e9693ca47e7d856"

    @property
    def enabled(self):
        return True

FAKE_PROJECTS = [FakeProject()]

EXPECTED_PROJECT = {
 "kind": "compute#project",
 "selfLink": "http://localhost/compute/v1beta15/projects/fake_project",
 "id": "504224095749693425",
 "name": "fake_project",
 "description": "",
 "commonInstanceMetadata": {
  "kind": "compute#metadata"
 },
 "quotas": [
#   {
#    "metric": "SNAPSHOTS",
#    "limit": 1000.0,
#    "usage": 0.0
#   },
#   {
#    "metric": "NETWORKS",
#    "limit": 5.0,
#    "usage": 1.0
#   },
#   {
#    "metric": "FIREWALLS",
#    "limit": 100.0,
#    "usage": 2.0
#   },
#   {
#    "metric": "IMAGES",
#    "limit": 100.0,
#    "usage": 0.0
#   },
#   {
#    "metric": "ROUTES",
#    "limit": 100.0,
#    "usage": 2.0
#   },
#   {
#    "metric": "FORWARDING_RULES",
#    "limit": 50.0,
#    "usage": 0.0
#   },
#   {
#    "metric": "TARGET_POOLS",
#    "limit": 50.0,
#    "usage": 0.0
#   },
#   {
#    "metric": "HEALTH_CHECKS",
#    "limit": 50.0,
#    "usage": 0.0
#   }
 ]
}


class FakeKeystoneClient(object):
    @property
    def tenants(self):
        class FakeTenants(object):
            def list(self):
                return FAKE_PROJECTS

        return FakeTenants()


def get_client(**kwargs):
    return FakeKeystoneClient()


class ProjectsTest(common.GCEControllerTest):
    def setUp(self):
        super(ProjectsTest, self).setUp()

        self.stubs.Set(keystone_client, "Client", get_client)

        self.controller = projects.Controller()

    def test_get_project(self):
        response = self.request_gce("/fake_project")
        self.assertDictEqual(response.json_body, EXPECTED_PROJECT)

    def test_set_common_instance_metadata(self):
        expected = {
            "kind": "compute#operation",
            "id": "0",
            "name": "stub",
            "operationType": "setMetadata",
            "targetLink": "http://localhost/compute/v1beta15/projects"
                "/fake_project",
            "targetId": "504224095749693425",
            "status": "DONE",
            "progress": 100,
            "selfLink": "http://localhost/compute/v1beta15/projects"
                "/fake_project/global/operations/stub"
        }

        body = {"items": [], "kind": "compute#metadata"}
        response = self.request_gce("/fake_project/setCommonInstanceMetadata",
                                    method="POST",
                                    body=body)
        self.assertDictEqual(response.json_body, expected)
