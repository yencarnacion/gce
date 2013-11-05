#    Copyright 2012 Cloudscaling Group, Inc
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

import webob

from nova.openstack.common.gettextutils import _
from nova import exception
from nova.compute import flavors as flavors
from nova.api.gce import wsgi as gce_wsgi
from nova.api.gce import common as gce_common

from nova.api.gce import instance_api


class Controller(gce_common.Controller):
    """GCE Instance controller"""

    def __init__(self, *args, **kwargs):
        super(Controller, self).__init__(*args, **kwargs)
        self._api = instance_api.API()

    def _get_type(self):
        return "instance"

    def basic(self, request, instance, zone_id):
        machineTypeName = str(
            flavors.extract_flavor(instance)['name']
                .replace(".", "-"))
        result_dict = {
            "creationTimestamp": self._format_date(instance['created_at']),
            "status": instance['status'],
            # NOTE(apavlov): real openstack status
            "statusMessage": instance['vm_state'],
            "name": instance['display_name'],
            "description": instance['display_description'],
            "machineType": self._qualify(
                request, "machineTypes", machineTypeName, zone_id),
            "networkInterfaces": [],
            "disks": [],
            "metadata": {
                "kind": "compute#metadata",
            },
        }

        if 'image' in instance:
            result_dict["image"] = self._qualify(
                request, "images", instance['image'], None)

        for i in instance.get("metadata", []):
            result_dict["metadata"]["items"].append(
                {"key": i["key"], "value": i["value"]})

        cached_nwinfo = instance["cached_nwinfo"]
        if cached_nwinfo:
            for network_info in cached_nwinfo:
                for subnet in network_info['network']['subnets']:
                    for fixed_ip in subnet['ips']:
                        result_dict["networkInterfaces"].append({
                            "network": self._qualify(
                                request, "networks",
                                network_info['network']['label'], None),
                            "networkIP": fixed_ip['address'],
                            "name": network_info['network']['label'],
                            "accessConfigs": [{
                                "kind": "compute#accessConfig",
                                "name": ip['address'],
                                "type": "ONE_TO_ONE_NAT",
                                "natIP": ip['address']
                            } for ip in fixed_ip['floating_ips']]
                        })

        attached_disks = instance["attached_disks"]
        disk_index = 0
        for disk in attached_disks:
            volume = disk.get("volume", None)
            if volume is None:
                continue
            volume = disk["volume"]
            google_disk = {
                "kind": "compute#attachedDisk",
                "index": disk_index,
                "type": "PERSISTENT",
                "mode": "READ_WRITE",
                "source": self._qualify(
                    request, "disks", volume['display_name'], zone_id),
                "deviceName": disk['device_name'],
            }
            if disk['device_name'] == "vda":
                google_disk["boot"] = True,
            result_dict["disks"].append(google_disk)
            disk_index += 1

        return self._format_item(request,
                                 result_dict,
                                 instance["id"],
                                 zone_id
                                 )

    def reset_instance(self, req, zone_id, id):
        context = req.environ['nova.context']

        try:
            self._api.reset_instance(context, zone_id, id)
        except (exception.NotFound, KeyError, IndexError):
            msg = _("Instance %s could not be found" % id)
            raise webob.exc.HTTPNotFound(explanation=msg)

        return self._format_operation(req, id, "update", zone_id)

    def add_access_config(self, req, body, zone_id, id):
        context = req.environ['nova.context']
        self._api.add_access_config(
            context, body, id, zone_id, req.params.get('networkInterface'))

        return self._format_operation(req, id, "insert", zone_id)

    def delete_access_config(self, req, zone_id, id):
        context = req.environ['nova.context']
        self._api.delete_access_config(context, id, zone_id,
           req.params.get('networkInterface'),
           req.params.get('accessConfig'))

        return self._format_operation(req, id, "delete", zone_id)


def create_resource():
    return gce_wsgi.GCEResource(Controller())
