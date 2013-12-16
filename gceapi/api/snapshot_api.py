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
from gceapi import exception
#from gceapi import volume


class API(base_api.API):
    """GCE Snapshot API"""

    _status_map = {
        'new': 'CREATING',
        'creating': 'CREATING',
        'available': 'READY',
        'active': 'READY',
        'deleting': 'DELETING',
        'deleted': 'DELETING',
        'error': 'FAILED'}

    def __init__(self, *args, **kwargs):
        super(API, self).__init__(*args, **kwargs)
        #self._volume_service = volume.API()

    def get_item(self, context, name, scope=None):
        snapshots = self._volume_service.get_all_snapshots(context)
        for snapshot in snapshots:
            if snapshot["display_name"] == name:
                return self._prepare_item(context, snapshot)
        raise exception.NotFound

    def get_items(self, context, scope=None):
        snapshots = self._volume_service.get_all_snapshots(context)
        for snapshot in snapshots:
            self._prepare_item(context, snapshot)
        return snapshots

    def delete_item(self, context, name, scope=None):
        snapshot = self.get_item(context, name, scope)
        self._volume_service.delete_snapshot(context, snapshot)

    def add_item(self, context, body, scope=None):
        name = body["name"]
        disk_name = body["disk_name"]
        volume = self._get_disk_by_name(context, disk_name, scope)

        snapshot = self._volume_service.create_snapshot_force(
            context, volume, name, body["description"])

        return self._prepare_item(context, snapshot)

    def _prepare_item(self, context, item):
        item["name"] = item["display_name"]
        try:
            item["disk"] = self._volume_service.get(context, item["volume_id"])
        except:
            pass
        item["status"] = self._status_map.get(item["status"], item["status"])
        return item

    def _get_disk_by_name(self, context, name, scope):
        volumes = self._volume_service.get_all(context)
        for volume in volumes:
            if volume["display_name"] == name:
                return volume
        raise exception.NotFound
