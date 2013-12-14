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

from gceapi import exception
from gceapi.openstack.common import timeutils


class FakeImageService(object):

    _allowed_filter_fields = set(["name"])

    def __init__(self):
        timestamp = timeutils.parse_isotime('2013-08-01T11:30:25')
        self._images = [
            {
                'id': '60ff30c2-64b6-4a97-9c17-322eebc8bd60',
                'name': 'fake-image-1',
                'created_at': timestamp,
                'updated_at': timestamp,
                'deleted_at': None,
                'deleted': False,
                'status': 'active',
                'is_public': False,
                'container_format': 'raw',
                'disk_format': 'raw',
                'size': '1',
            },
            {
                'id': 'a2459075-d96c-40d5-893e-577ff92e721c',
                'name': 'fake-image-2',
                'created_at': timestamp,
                'updated_at': timestamp,
                'deleted_at': None,
                'deleted': False,
                'status': 'active',
                'is_public': True,
                'container_format': 'ami',
                'disk_format': 'ami',
                'size': '2',
             },
             {
                'id': '0aa076e2-def4-43d1-ae81-c77a9f9279e6',
                'name': 'image-to-delete',
                'created_at': timestamp,
                'updated_at': timestamp,
                'deleted_at': None,
                'deleted': False,
                'status': 'active',
                'is_public': True,
                'container_format': 'ami',
                'disk_format': 'ami',
                'size': '2',
             },
        ]
        self._new_image_attributes = {
            "new-image": {
                "id": "6a8fd89a-e636-48a4-8095-5510eab696c4",
                "created_at": timeutils.parse_isotime("2013-08-02T11:30:25")
            },
        }

    def detail(self, context, **kwargs):
        filters = {field_name: filter_value for field_name, filter_value
                   in kwargs.get("filters", {}).iteritems()
                   if field_name in self._allowed_filter_fields}

        def check_image(image):
            for field_name, filter_value in filters.iteritems():
                if image.get(field_name) != filter_value:
                    return False
            return True

        return [copy.deepcopy(image) for image in self._images
                if check_image(image)]

    def show(self, context, image_id):
        for image in self._images:
            if image['id'] == str(image_id):
                return copy.deepcopy(image)
        raise exception.ImageNotFound(image_id=image_id)

    def create(self, context, metadata, data=None):
        image = copy.deepcopy(metadata)
        image.update(self._new_image_attributes[image["name"]])
        image["updated_at"] = image["created_at"]
        image.update({
            "deleted_at": False,
            "deleted": False,
            "status": "active",
        })
        self._images.append(image)
        return copy.deepcopy(image)

    def delete(self, context, image_id):
        image_index = 0
        for image in self._images:
            if image["id"] != image_id:
                image_index += 1
                continue
            del self._images[image_index]
            return True
        raise exception.ImageNotFound(image_id=image_id)
