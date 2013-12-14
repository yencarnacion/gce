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

import os.path

from nova.api.gce import base_api
from nova.api.gce import image_api
from nova import exception
from nova import volume


GB = 1048576 * 1024


class API(base_api.API):
    """GCE Disk API"""

    _status_map = {
            "creating": "CREATING",
            "downloading": "CREATING",
            "available": "READY",
            "attaching": "READY",
            "in-use": "READY",
            # "deleting": "",
            "error": "FAILED",
            # "error_deleting": "",
            "backing-up": "READY",
            "restoring-backup": "READY",
            # "error_restoring": ""
    }

    def __init__(self, *args, **kwargs):
        super(API, self).__init__(*args, **kwargs)
        self._volume_service = volume.API()

    def get_item(self, context, name, scope=None):
        volumes = self._volume_service.get_all(context)
        volumes = self._filter_volumes_by_zone(volumes, scope)
        for volume in volumes:
            if volume["display_name"] == name:
                return self._prepare_item(context, volume)
        raise exception.NotFound

    def get_item_by_id(self, context, item_id):
        return self._volume_service.get(context, item_id)

    def get_items(self, context, scope=None):
        volumes = self._volume_service.get_all(context)
        volumes = self._filter_volumes_by_zone(volumes, scope)
        for volume in volumes:
            self._prepare_item(context, volume)
        return volumes

    def get_scopes(self, context, item):
        return [item["availability_zone"]]

    def _prepare_item(self, context, item):
        snapshot = None
        snapshot_id = item["snapshot_id"]
        if snapshot_id:
            snapshot = self._get_snapshot(context, snapshot_id)
        item["snapshot"] = snapshot
        metadata = item.get("volume_image_metadata")
        if metadata:
            image_id = metadata.get("image_id")
            if image_id:
                item["image"] = image_api.API().get_item_by_id(context,
                                                               image_id)
        item["status"] = self._status_map.get(item["status"], item["status"])
        item["name"] = item["display_name"]
        return item

    def _filter_volumes_by_zone(self, volumes, scope):
        if scope is None:
            return volumes
        return filter(
            lambda volume: volume["availability_zone"] == scope.get_name(),
            volumes)

    def delete_item(self, context, name, scope=None):
        volume = self.get_item(context, name, scope)
        self._volume_service.delete(context, volume)

    def add_item(self, context, name, body, scope=None):
        sizeGb = int(body['sizeGb']) if 'sizeGb' in body else None

        snapshot_uri = body.get("sourceSnapshot")
        image_uri = body.get("sourceImage")
        snapshot = None
        image_id = None

        if snapshot_uri:
            snapshot = self._get_snapshot_by_url(context, snapshot_uri)
        elif image_uri:
            image_name = os.path.basename(image_uri)
            if image_name:
                image = image_api.API().get_item(context, image_name, scope)
                image_id = image['id']
                # Cinder API doesn't get size from image, so we do this
                image_size_in_gb = (int(image['size']) + GB - 1) / GB
                if not sizeGb or sizeGb < image_size_in_gb:
                    sizeGb = image_size_in_gb

        volume = self._volume_service.create(context,
            sizeGb,
            body.get('name'),
            body.get('description'),
            snapshot=snapshot,
            image_id=image_id,
            availability_zone=scope.get_name())

        return self._prepare_item(context, volume)

    def _get_snapshot(self, context, snapshot_id):
        return self._volume_service.get_snapshot(context, snapshot_id)

    def _get_image_by_url(self, context, url):
        source_name = os.path.basename(url)
        return image_api.API().get_item(context, source_name)

    def _get_snapshot_by_url(self, context, url):
        snapshot_name = os.path.basename(url)
        snapshots = self._volume_service.get_all_snapshots(context)
        for snapshot in snapshots:
            if snapshot["display_name"] == snapshot_name:
                return snapshot
        raise exception.NotFound
