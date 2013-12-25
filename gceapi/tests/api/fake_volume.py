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


class FakeVolumeService(object):

    class Singleton:
        def __init__(self):
            self.FakeVolumeService = None

    def __init__(self):
        if FakeVolumeService._instance is None:
            FakeVolumeService._instance = FakeVolumeService.Singleton()

        self._EventHandler_instance = FakeVolumeService._instance

    def create(self, context, size, name, description, snapshot=None,
               image_id=None, volume_type=None, metadata=None,
               availability_zone=None):
        volume = copy.deepcopy(self._new_volume_attributes[name])
        volume["display_name"] = name
        volume["availability_zone"] = availability_zone
        volume["display_description"] = description
        volume["size"] = size
        if snapshot is not None:
            volume["snapshot_id"] = snapshot["id"]
        if image_id is not None:
            volume["volume_image_metadata"] = {
                "image_id": image_id
            }
        self._volumes.append(volume)
        return volume
