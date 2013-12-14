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

import webob

from nova.api.gce import common as gce_common
from nova.api.gce import instance_api
from nova.api.gce import wsgi as gce_wsgi
from nova.api.gce import zone_api
from nova.compute import instance_types
from nova import exception


class Controller(gce_common.Controller):
    """GCE Instance controller"""

    def __init__(self, *args, **kwargs):
        super(Controller, self).__init__(scope_api=zone_api.API(),
                                         *args, **kwargs)
        self._api = instance_api.API()

    def _get_type(self):
        return "instance"

    def format_item(self, request, instance, scope):
        machineTypeName = str(
            instance_types.extract_instance_type(instance)['name']
                .replace(".", "-"))
        result_dict = {
            "creationTimestamp": self._format_date(instance['created_at']),
            "status": instance['status'],
            # NOTE(apavlov): real openstack status
            "statusMessage": instance['vm_state'],
            "name": instance['display_name'],
            "description": instance['display_description'],
            "machineType": self._qualify(request,
                "machineTypes", machineTypeName, scope),
            "networkInterfaces": [],
            "disks": [],
            "metadata": {
                "kind": "compute#metadata",
            },
        }

        for i in instance.get("metadata", []):
            result_dict["metadata"]["items"].append(
                {"key": i["key"], "value": i["value"]})

        cached_nwinfo = instance["cached_nwinfo"]
        if cached_nwinfo:
            for network_info in cached_nwinfo:
                for subnet in network_info['network']['subnets']:
                    for fixed_ip in subnet['ips']:
                        result_dict["networkInterfaces"].append({
                            "network": self._qualify(request,
                                "networks", network_info['network']['label'],
                                gce_common.Scope.create_global()),
                            "networkIP": fixed_ip['address'],
                            "name": network_info['network']['label'],
                            "accessConfigs": [{
                                "kind": "compute#accessConfig",
                                "name": "External NAT",
                                "type": "ONE_TO_ONE_NAT",
                                "natIP": ip['address']
                            } for ip in fixed_ip['floating_ips']]
                        })

        attached_disks = instance["attached_disks"]
        disk_index = 0
        for disk in attached_disks:
            volume = disk["volume"]
            google_disk = {
                "kind": "compute#attachedDisk",
                "index": disk_index,
                "type": "PERSISTENT",
                "mode": "READ_WRITE",
                "source": self._qualify(request,
                    "disks", volume['display_name'], scope),
                "deviceName": disk['device_name'],
            }
            if disk['device_name'] == "vda":
                google_disk["boot"] = True,
            result_dict["disks"].append(google_disk)
            disk_index += 1

        return self._format_item(request, result_dict, scope)

    def reset_instance(self, req, scope_id, id):
        context = self._get_context(req)
        scope = self._get_scope(req, scope_id)

        try:
            self._api.reset_instance(context, scope, id)
        except (exception.NotFound, KeyError, IndexError):
            msg = _("Instance %s could not be found" % id)
            raise webob.exc.HTTPNotFound(explanation=msg)

        return self._format_operation(req, id, "reset", scope)

    def add_access_config(self, req, body, scope_id, id):
        context = self._get_context(req)
        scope = self._get_scope(req, scope_id)
        self._api.add_access_config(context, body, id, scope,
            req.params.get('networkInterface'))

        return self._format_operation(req, id, "addAccessConfig", scope)

    def delete_access_config(self, req, scope_id, id):
        context = self._get_context(req)
        scope = self._get_scope(req, scope_id)
        self._api.delete_access_config(context, id, scope,
           req.params.get('networkInterface'),
           req.params.get('accessConfig'))

        return self._format_operation(req, id, "deleteAccessConfig", scope)


def create_resource():
    return gce_wsgi.GCEResource(Controller())
