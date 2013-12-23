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

from gceapi.api import base_api
from gceapi.api import clients
from gceapi.api import image_api
from gceapi.api import utils
from gceapi import exception


GB = 1024 ** 3


class API(base_api.API):
    """GCE Disk API"""

    KIND = "disk"
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

    def _get_type(self):
        return self.KIND

    def get_item(self, context, name, scope=None):
        client = clients.Clients(context).cinder()
        volumes = client.volumes.list(search_opts={"display_name": name})
        volumes = [utils.todict(item) for item in volumes]
        volumes = self._filter_volumes_by_zone(volumes, scope)
        for volume in volumes:
            if volume["display_name"] == name:
                return self._prepare_item(client, volume)
        raise exception.NotFound

    def get_item_by_id(self, context, item_id):
        return self._volume_service.get(context, item_id)

    def get_items(self, context, scope=None):
        client = clients.Clients(context).cinder()
        volumes = [utils.todict(item) for item in client.volumes.list()]
        volumes = self._filter_volumes_by_zone(volumes, scope)
        for volume in volumes:
            self._prepare_item(client, volume)
        return volumes

    def get_scopes(self, context, item):
        return [item["availability_zone"]]

    def _prepare_item(self, client, item):
        snapshot = None
        snapshot_id = item["snapshot_id"]
        if snapshot_id:
            snapshot = utils.todict(client.volume_snapshots.get(snapshot_id))
        item["snapshot"] = snapshot
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
        client = clients.Clients(context).cinder().volumes
        volumes = client.list(search_opts={"display_name": name})
        if not volumes or len(volumes) != 1:
            raise exception.NotFound
        client.delete(volumes[0])

    def add_item(self, context, name, body, scope=None):
        sizeGb = int(body['sizeGb']) if 'sizeGb' in body else None

        snapshot_uri = body.get("sourceSnapshot")
        image_uri = body.get("sourceImage")
        snapshot_id = None
        image_id = None

        client = clients.Clients(context).cinder()
        if snapshot_uri:
            snapshot_name = utils._extract_name_from_url(snapshot_uri)
            snapshots = client.volume_snapshots.list(
                search_opts={"display_name": snapshot_name})
            if not snapshots or len(snapshots) != 1:
                raise exception.NotFound
            snapshot_id = snapshots[0].id
        elif image_uri:
            image_name = utils._extract_name_from_url(image_uri)
            image = image_api.API().get_item(context, image_name, scope)
            image_id = image['id']
            # Cinder API doesn't get size from image, so we do this
            image_size_in_gb = (int(image['size']) + GB - 1) / GB
            if not sizeGb or sizeGb < image_size_in_gb:
                sizeGb = image_size_in_gb

        volume = client.volumes.create(
            sizeGb, snapshot_id=snapshot_id,
            display_name=body.get('name'),
            display_description=body.get('description'),
            imageRef=image_id,
            availability_zone=scope.get_name())

        return self._prepare_item(context, utils.todict(volume))
