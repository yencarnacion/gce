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

from gceapi.api import projects
from gceapi.tests.api import common


EXPECTED_PROJECT = {
    "kind": "compute#project",
    "selfLink": "http://localhost/compute/v1beta15/projects/fake_project",
    "id": "504224095749693425",
    "name": "fake_project",
    "description": "",
    "commonInstanceMetadata": {
        "kind": "compute#metadata"
    },
    "quotas": [{
        "metric": "CPU",
        "limit": 17.0,
        "usage": 1.0
    },
    {
        "metric": "INSTANCES",
        "limit": 10.0,
        "usage": 4.0
    },
    {
        "usage": 2.0,
        "metric": "DISKS_TOTAL_GB",
        "limit": 1000.0
    },
    {
        "usage": 1.0,
        "metric": "SNAPSHOTS",
        "limit": 10.0
    },
    {
        "usage": 1.0,
        "metric": "DISKS",
        "limit": 10.0
    },
    {
        "usage": 2.0,
        "metric": "FIREWALLS",
        "limit": 10.0
    },
    {
        "usage": 1.0,
        "metric": "STATIC_ADDRESSES",
        "limit": 50.0
    },
    {
        "usage": 2.0,
        "metric": "NETWORKS",
        "limit": 10.0
    }
]}


class ProjectsTest(common.GCEControllerTest):
    def setUp(self):
        super(ProjectsTest, self).setUp()
        self.controller = projects.Controller()

    def test_get_project(self):
        response = self.request_gce("/fake_project")
        self.assertDictEqual(response.json_body, EXPECTED_PROJECT)

    def test_set_common_instance_metadata(self):
        expected = {
            "operationType": "setMetadata",
            "targetId": "504224095749693425",
            "targetLink": "http://localhost/compute/v1beta15/projects"
                "/fake_project",
        }
        expected.update(common.COMMON_FINISHED_OPERATION)
        body = {"items": [], "kind": "compute#metadata"}
        response = self.request_gce("/fake_project/setCommonInstanceMetadata",
                                    method="POST",
                                    body=body)
        self.assertDictEqual(response.json_body, expected)
