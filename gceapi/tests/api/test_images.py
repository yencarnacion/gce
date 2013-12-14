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

from gceapi.tests.api import common

FAKE_IMAGE_1 = {
    "kind": "compute#image",
    "selfLink": "http://localhost/compute/v1beta15/projects/"
                "fake_project/global/images/fake-image-1",
    "id": "5721131091780319465",
    "creationTimestamp": "2013-08-01T11:30:25Z",
    "name": "fake-image-1",
    "sourceType": "RAW",
    "rawDisk": {
        "containerType": "TAR",
        "source": "",
    },
    "status": "READY",
}
FAKE_IMAGE_2 = {
    "kind": "compute#image",
    "selfLink": "http://localhost/compute/v1beta15/projects/"
                "fake_project/global/images/fake-image-2",
    "id": "5721131091780319468",
    "creationTimestamp": "2013-08-01T11:30:25Z",
    "name": "fake-image-2",
    "sourceType": "AMI",
    "rawDisk": {
        "containerType": "TAR",
        "source": "",
    },
    "status": "READY",
}
NEW_IMAGE = {
    "kind": "compute#image",
    "selfLink": "http://localhost/compute/v1beta15/projects/"
                "fake_project/global/images/new-image",
    "id": "7252430471608041491",
    "creationTimestamp": "2013-08-02T11:30:25Z",
    "name": "new-image",
    "sourceType": "RAW",
    "rawDisk": {
        "containerType": "TAR",
        "source": "",
    },
    "status": "READY",
}


class ImagesControllerTest(common.GCEControllerTest):
    """
    Test of the GCE API /images application controller w/Glance.
    """

    def setUp(self):
        """Run before each test."""
        super(ImagesControllerTest, self).setUp()

    def test_get_image_list_filtered(self):
        response = self.request_gce("/fake_project/global/images"
                                    "?filter=name+eq+fake-image-2")
        self.assertEqual(200, response.status_int)
        response_body = copy.deepcopy(response.json_body)
        self.assertIn("items", response_body)
        expected_common = {
            "kind": "compute#imageList",
            "selfLink": "http://localhost/compute/v1beta15/projects/"
                        "fake_project/global/images",
            "id": "projects/fake_project/global/images",
        }
        response_images = response_body.pop("items")
        self.assertDictEqual(expected_common, response_body)
        self.assertIn(FAKE_IMAGE_2, response_images)

    def test_get_image_list(self):
        response = self.request_gce('/fake_project/global/images')
        self.assertEqual(200, response.status_int)
        response_body = copy.deepcopy(response.json_body)
        self.assertIn("items", response_body)
        expected_common = {
            "kind": "compute#imageList",
            "selfLink": "http://localhost/compute/v1beta15/projects/"
                        "fake_project/global/images",
            "id": "projects/fake_project/global/images",
        }
        response_images = response_body.pop("items")
        self.assertDictEqual(expected_common, response_body)
        self.assertIn(FAKE_IMAGE_1, response_images)
        self.assertIn(FAKE_IMAGE_2, response_images)

    def test_get_image(self):
        response = self.request_gce("/fake_project/global/images/fake-image-1")
        self.assertEqual(200, response.status_int)
        self.assertDictEqual(FAKE_IMAGE_1, response.json_body)

    def test_get_nonexistent_image(self):
        response = self.request_gce('/fake_project/global/images/fake-image')
        self.assertEqual(404, response.status_int)

    def test_create_image(self):
        self.set_stubs_for_load_tar()
        request_body = {
            'name': 'new-image',
            'rawDisk': {
                'containerType': 'TAR',
                'source': 'http://example.com/image.tar',
            },
            'sourceType': 'RAW',
        }
        response = self.request_gce('/fake_project/global/images',
                                    method="POST",
                                    body=request_body)
        expected = {
            "kind": "compute#operation",
            "id": "0",
            "progress": 100,
            "targetId": "7252430471608041491",
            "name": "stub",
            "operationType": "insert",
            "targetLink": "http://localhost/compute/v1beta15/projects/"
                          "fake_project/global/images/new-image",
            "status": "DONE",
            "selfLink": "http://localhost/compute/v1beta15/projects/"
                        "fake_project/global/operations/stub",
        }
        self.assertEqual(200, response.status_int)
        self.assertDictEqual(expected, response.json_body)

        response = self.request_gce('/fake_project/global/images/new-image')
        self.assertEqual(200, response.status_int)
        self.assertDictEqual(NEW_IMAGE, response.json_body)

    def test_delete_image(self):
        response = self.request_gce(
                '/fake_project/global/images/image-to-delete', method='DELETE')
        expected = {
            "kind": "compute#operation",
            "id": "0",
            "progress": 100,
            "targetId": "6451912522928418272",
            "name": "stub",
            "operationType": "delete",
            "targetLink": "http://localhost/compute/v1beta15/projects/"
                          "fake_project/global/images/image-to-delete",
            "selfLink": "http://localhost/compute/v1beta15/projects/"
                        "fake_project/global/operations/stub",
            "status": "DONE",
        }
        self.assertEqual(200, response.status_int)
        self.assertDictEqual(expected, response.json_body)

        response = self.request_gce(
                '/fake_project/global/images/image-to-delete')
        self.assertEqual(404, response.status_int)

    def test_delete_nonexistent_image(self):
        response = self.request_gce('/fake_project/global/images/fake-image',
                                    method='DELETE')
        self.assertEqual(404, response.status_int)
