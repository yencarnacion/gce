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

    _volumes = [
        {
            "status": "available",
            "volume_type_id": None,
            "display_name": "fake-disk-1",
            "attach_time": "",
            "availability_zone": "nova",
            "created_at": "2013-08-14T12:35:22.000000",
            "attach_status": "detached",
            "display_description": "fake disk from snapshot",
            "volume_metadata": [],
            "snapshot_id": "991cda9c-28bd-420f-8432-f5159def85d6",
            "mountpoint": "",
            "id": "e922ebbb-2938-4a12-869f-cbc4e26c6600",
            "size": 2,
        },
        {
            "status": "available",
            "volume_type_id": None,
            "volume_image_metadata": {
                "kernel_id": "57dfd985-4561-4a9e-8e23-262e2e2b097e",
                "image_id": "60ff30c2-64b6-4a97-9c17-322eebc8bd60",
                "ramdisk_id": "869f61a4-7ceb-4a21-8f35-23d8257911e5",
                "image_name": "fake-image-1"
            },
            "display_name": "fake-disk-2",
            "attach_time": "",
            "availability_zone": "nova",
            "created_at": "2013-08-14T12:19:35.000000",
            "attach_status": "detached",
            "display_description": "",
            "volume_metadata": [],
            "snapshot_id": None,
            "mountpoint": "",
            "id": "64ebe1d9-757f-4074-88d0-2ac790be909d",
            "size": 1,
        },
        {
            "status": "available",
            "volume_type_id": None,
            "display_name": "fake-disk-3",
            "attach_time": "",
            "availability_zone": "nova",
            "created_at": "2013-08-14T11:57:44.000000",
            "attach_status": "detached",
            "display_description": "full description of disk",
            "volume_metadata": [],
            "snapshot_id": None,
            "mountpoint": "",
            "id": "fc0d5c01-dc3b-450d-aaed-de028bb832b1",
            "size": 3,
        },
        {
            "status": "available",
            "volume_type_id": None,
            "display_name": "disk-to-delete",
            "attach_time": "",
            "availability_zone": "nova",
            "created_at": "2013-08-14T12:10:02.000000",
            "attach_status": "detached",
            "display_description": "full description of disk",
            "volume_metadata": [],
            "snapshot_id": None,
            "mountpoint": "",
            "id": "a0786ec1-d838-4ad6-a497-87ec0b79161b",
            "size": 3,
        },
        {
            "status": "in-use",
            "instance_uuid": "d0a267df-be69-45cf-9cc3-9f8db99cb767",
            "volume_image_metadata": {
                "image_id": "60ff30c2-64b6-4a97-9c17-322eebc8bd60",
                "image_name": "fake-image-1"},
            "display_name": "i1",
            "attach_time": "",
            "availability_zone": "nova",
            "created_at": "2013-08-14T18:55:57.000000",
            "attach_status": "attached",
            "display_description": "Persistent boot disk created from "
                "http://127.0.0.1:8777/compute/v1beta15/projects/admin"
                "/global/images/fake-image-1.",
            "volume_type_id": "None",
            "volume_metadata": [],
            "snapshot_id": None,
            "mountpoint": "vdc",
            "id": "ab8829ad-eec1-44a2-8068-d7f00c53ee90",
            "size": 1
        }
    ]
    _snapshots = [
        {
            "status": "available",
            "display_name": "fake-snapshot",
            "created_at": "2013-08-14T12:32:28.000000",
            "display_description": "full description of snapshot 1",
            "volume_size": 2,
            "volume_id": "fc0d5c01-dc3b-450d-aaed-de028bb832b1",
            "progress": "100%",
            "project_id": "f0dcd67240544bc6903766a025c6e2b9",
            "id": "991cda9c-28bd-420f-8432-f5159def85d6",
            "size": 2,
        }
    ]
    _new_volume_attributes = {
        "new-disk": {
            "status": "available",
            "volume_type_id": None,
            "attach_time": "",
            "availability_zone": "nova",
            "created_at": "2013-08-14T15:00:22.000000",
            "attach_status": "detached",
            "display_description": "",
            "volume_metadata": [],
            "snapshot_id": None,
            "mountpoint": "",
            "id": "8af36778-84db-475e-b3c9-da2cc260df4a",
            "size": 1,
        },
        "new-image-disk": {
            "status": "available",
            "volume_type_id": None,
            "volume_image_metadata": {
                "kernel_id": "57dfd985-4561-4a9e-8e23-262e2e2b097e",
                "image_id": "a2459075-d96c-40d5-893e-577ff92e721c",
                "ramdisk_id": "869f61a4-7ceb-4a21-8f35-23d8257911e5",
                "image_name": "fake-image-2"
            },
            "attach_time": "",
            "availability_zone": "nova",
            "created_at": "2013-08-14T15:56:00.000000",
            "attach_status": "detached",
            "display_description": "disk created with image",
            "volume_metadata": [],
            "snapshot_id": None,
            "mountpoint": "",
            "id": "f35151b8-7b81-4e76-b2ab-ecdc14f949d2",
            "size": 1,
        },
        "new-sn-disk": {
            "status": "creating",
            "volume_type_id": "None",
            "attach_time": "",
            "availability_zone": "nova",
            "created_at": "2013-08-14T16:43:59.000000",
            "attach_status": "detached",
            "display_description": "disk created from snapshot",
            "volume_metadata": [],
            "snapshot_id": "991cda9c-28bd-420f-8432-f5159def85d6",
            "mountpoint": "",
            "id": "ae2de9eb-32f2-4db7-8ef0-23f0fd0ebf63",
            "size": 1,
        },
    }
    _instance = None

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

    def delete(self, context, volume):
        self._volumes = [v for v in self._volumes if v["id"] != volume["id"]]

    def get(self, context, volume_id):
        for volume in self._volumes:
            if volume['id'] == str(volume_id):
                return copy.deepcopy(volume)
        raise exception.VolumeNotFound(volume_id=volume_id)

    def get_all(self, context):
        return copy.deepcopy(self._volumes)

    def get_snapshot(self, context, snapshot_id):
        for snapshot in self._snapshots:
            if snapshot['id'] == str(snapshot_id):
                return copy.deepcopy(snapshot)
        raise exception.SnapshotNotFound(snapshot_id=snapshot_id)

    def get_all_snapshots(self, context):
        return self._snapshots

    def delete_snapshot(self, context, snapshot):
        self.get_snapshot(context, snapshot["id"])

    def create_snapshot_force(self, context, volume, name, description):
        return self._snapshots[0]
