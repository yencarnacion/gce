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

from cinderclient import exceptions as exc

from gceapi.tests.api import utils
from gceapi.tests.api import fake_request


#'attachments': [],
#'snapshot_id': None,
#'snapshot': None,
#'source_volid': None,

FAKE_DISKS = [utils.to_obj({
    "status": "available",
    "volume_type": None,
    "display_name": "fake-disk-1",
    "availability_zone": "nova",
    "created_at": "2013-08-14T12:35:22.000000",
    "display_description": "fake disk from snapshot",
    "metadata": {},
    "snapshot_id": "991cda9c-28bd-420f-8432-f5159def85d6",
    "id": "e922ebbb-2938-4a12-869f-cbc4e26c6600",
    "size": 2,
    "os-vol-tenant-attr:tenant_id": fake_request.PROJECT_ID,
    "os-vol-mig-status-attr:name_id": None,
    "os-vol-mig-status-attr:migstat": None,
    "os-vol-host-attr:host": "grizzly",
}), utils.to_obj({
    "status": "available",
    "volume_type": None,
    "bootable": u"true",
    "volume_image_metadata": {
        "image_id": "60ff30c2-64b6-4a97-9c17-322eebc8bd60",
        "image_name": "fake-image-1"
    },
    "display_name": "fake-disk-2",
    "availability_zone": "nova",
    "created_at": "2013-08-14T12:19:35.000000",
    "display_description": "",
    "metadata": {},
    "snapshot_id": None,
    "id": "64ebe1d9-757f-4074-88d0-2ac790be909d",
    "size": 1,
    "os-vol-tenant-attr:tenant_id": fake_request.PROJECT_ID,
    "os-vol-mig-status-attr:name_id": None,
    "os-vol-mig-status-attr:migstat": None,
    "os-vol-host-attr:host": "grizzly",
}), utils.to_obj({
    "status": "available",
    "volume_type": None,
    "display_name": "fake-disk-3",
    "availability_zone": "nova",
    "created_at": "2013-08-14T11:57:44.000000",
    "display_description": "full description of disk",
    "metadata": {},
    "snapshot_id": None,
    "id": "fc0d5c01-dc3b-450d-aaed-de028bb832b1",
    "size": 3,
    "os-vol-tenant-attr:tenant_id": fake_request.PROJECT_ID,
    "os-vol-mig-status-attr:name_id": None,
    "os-vol-mig-status-attr:migstat": None,
    "os-vol-host-attr:host": "grizzly",
}), utils.to_obj({
    "status": "available",
    "volume_type": None,
    "display_name": "disk-to-delete",
    "availability_zone": "nova",
    "created_at": "2013-08-14T12:10:02.000000",
    "display_description": "full description of disk",
    "metadata": {},
    "snapshot_id": None,
    "id": "a0786ec1-d838-4ad6-a497-87ec0b79161b",
    "size": 3,
    "os-vol-tenant-attr:tenant_id": fake_request.PROJECT_ID,
    "os-vol-mig-status-attr:name_id": None,
    "os-vol-mig-status-attr:migstat": None,
    "os-vol-host-attr:host": "grizzly",
}), utils.to_obj({
    "status": "in-use",
    "instance_uuid": "d0a267df-be69-45cf-9cc3-9f8db99cb767",
    "bootable": u"true",
    "volume_image_metadata": {
        "image_id": "60ff30c2-64b6-4a97-9c17-322eebc8bd60",
        "image_name": "fake-image-1"},
    "display_name": "i1",
    "availability_zone": "nova",
    "created_at": "2013-08-14T18:55:57.000000",
    "display_description": "Persistent boot disk created from "
        "http://127.0.0.1:8777/compute/v1beta15/projects/admin"
        "/global/images/fake-image-1.",
    "volume_type": "None",
    "metadata": {},
    "snapshot_id": None,
    "id": "ab8829ad-eec1-44a2-8068-d7f00c53ee90",
    "size": 1,
    "os-vol-tenant-attr:tenant_id": fake_request.PROJECT_ID,
    "os-vol-mig-status-attr:name_id": None,
    "os-vol-mig-status-attr:migstat": None,
    "os-vol-host-attr:host": "grizzly",
})]

FAKE_SNAPSHOTS = [utils.to_obj({
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
})]

FAKE_NEW_DISKS = {
    "new-disk": {
        "status": "available",
        "volume_type": None,
        "availability_zone": "nova",
        "created_at": "2013-08-14T15:00:22.000000",
        "display_description": "",
        "metadata": {},
        "snapshot_id": None,
        "id": "8af36778-84db-475e-b3c9-da2cc260df4a",
        "size": 1,
        "os-vol-tenant-attr:tenant_id": fake_request.PROJECT_ID,
        "os-vol-mig-status-attr:name_id": None,
        "os-vol-mig-status-attr:migstat": None,
        "os-vol-host-attr:host": "grizzly",
    },
    "new-image-disk": {
        "status": "available",
        "volume_type": None,
        "bootable": u"true",
        "volume_image_metadata": {
            "image_id": "a2459075-d96c-40d5-893e-577ff92e721c",
            "image_name": "fake-image-2"
        },
        "availability_zone": "nova",
        "created_at": "2013-08-14T15:56:00.000000",
        "display_description": "disk created with image",
        "metadata": {},
        "snapshot_id": None,
        "id": "f35151b8-7b81-4e76-b2ab-ecdc14f949d2",
        "size": 1,
        "os-vol-tenant-attr:tenant_id": fake_request.PROJECT_ID,
        "os-vol-mig-status-attr:name_id": None,
        "os-vol-mig-status-attr:migstat": None,
        "os-vol-host-attr:host": "grizzly",
    },
    "new-sn-disk": {
        "status": "creating",
        "volume_type": "None",
        "availability_zone": "nova",
        "created_at": "2013-08-14T16:43:59.000000",
        "display_description": "disk created from snapshot",
        "metadata": {},
        "snapshot_id": "991cda9c-28bd-420f-8432-f5159def85d6",
        "id": "ae2de9eb-32f2-4db7-8ef0-23f0fd0ebf63",
        "size": 1,
        "os-vol-tenant-attr:tenant_id": fake_request.PROJECT_ID,
        "os-vol-mig-status-attr:name_id": None,
        "os-vol-mig-status-attr:migstat": None,
        "os-vol-host-attr:host": "grizzly",
    },
}


class FakeCinderClient(object):
    def __init__(self, version, *args, **kwargs):
        pass

    @property
    def client(self):
        return self

    @property
    def volumes(self):
        class FakeVolumes(object):
            def list(self, detailed=True, search_opts=None):
                result = FAKE_DISKS
                if search_opts:
                    if "display_name" in search_opts:
                        result = [d for d in result
                            if d.display_name == search_opts["display_name"]]
                return result

            def get(self, disk):
                disk_id = utils.get_id(disk)
                for disk in FAKE_DISKS:
                    if disk.id == disk_id:
                        return disk
                raise exc.NotFound()

            def delete(self, volume):
                volume_id = utils.get_id(volume)
                disks = [v for v in FAKE_DISKS if v.id != volume_id]
                #FAKE_DISKS = disks

            def create(self, size, snapshot_id=None, source_volid=None,
                    display_name=None, display_description=None,
                    volume_type=None, user_id=None,
                    project_id=None, availability_zone=None,
                    metadata=None, imageRef=None):
                pass

        return FakeVolumes()

    @property
    def volume_snapshots(self):
        class FakeVolumeSnapshots(object):
            def get(self, snapshot):
                snapshot_id = utils.get_id(snapshot)
                for snapshot in FAKE_SNAPSHOTS:
                    if snapshot.id == snapshot_id:
                        return snapshot
                raise exc.NotFound()

        return FakeVolumeSnapshots()
