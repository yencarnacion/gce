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

from gceapi.api import common as gce_common
from gceapi.api import instance_api
from gceapi.api import wsgi as gce_wsgi
from gceapi import exception

from gceapi.openstack.common import log as logging
from gceapi.openstack.common import timeutils

logger = logging.getLogger(__name__)


class Controller(gce_common.Controller):
    """GCE Instance controller"""

    def __init__(self, *args, **kwargs):
        super(Controller, self).__init__(instance_api.API(),
                                         *args, **kwargs)

    def format_item(self, request, instance, scope):
        result_dict = {
            "creationTimestamp": self._format_date(instance["created"]),
            "status": instance["status"],
            "statusMessage": instance["statusMessage"],
            "name": instance["name"],
            "machineType": self._qualify(request,
                "machineTypes", instance["flavor"]["name"], scope),
            "networkInterfaces": [],
            "disks": [],
            "metadata": {
                "kind": "compute#metadata",
                "items": list(),
            },
        }

        description = instance.get("description", "")
        if description:
            result_dict["description"] = description

        metadata = instance.get("metadata", {})
        for i in metadata:
            result_dict["metadata"]["items"].append(
                {"key": i, "value": metadata[i]})

        for network in instance["addresses"]:
            ni = dict()
            ni["network"] = self._qualify(request,
                "networks", network,
                gce_common.Scope.create_global())
            # NOTE(apavlov): The name of the network interface, generated by
            # the server. For network devices, these are eth0, eth1, etc.
            # But we provide name of network here because Openstack doesn`t
            # have device name.
            ni["name"] = network
            ni["accessConfigs"] = []
            for address in instance["addresses"][network]:
                atype = address["OS-EXT-IPS:type"]
                if atype == "fixed" and "networkIP" not in ni:
                    ni["networkIP"] = address["addr"]
                    continue
                if atype == "floating":
                    ni["accessConfigs"].append({
                        "kind": "compute#accessConfig",
                        "name": address["name"],
                        "type": address["type"],
                        "natIP": address["addr"]
                    })
                    continue
                logger.warn(_("Unexpected address for instance '%(i)' in "
                    "network '%(n)", {"i": instance["name"], "n": network}))
            result_dict["networkInterfaces"].append(ni)

        disk_index = 0
        for volume in instance["volumes"]:
            readonly = volume.get("metadata", {}).get("readonly", "False")
            google_disk = {
                "kind": "compute#attachedDisk",
                "index": disk_index,
                "type": "PERSISTENT",
                "mode": "READ_ONLY" if readonly == "True" else "READ_WRITE",
                "source": self._qualify(request,
                    "disks", volume["display_name"], scope),
                "deviceName": volume["attachments"][0]["device"],
                "boot": True if volume["bootable"] == "true" else False
            }
            result_dict["disks"].append(google_disk)
            disk_index += 1

        return self._format_item(request, result_dict, scope)

    def reset_instance(self, req, scope_id, id):
        context = self._get_context(req)
        scope = self._get_scope(req, scope_id)
        start_time = timeutils.isotime(None, True)

        try:
            self._api.reset_instance(context, scope, id)
        except (exception.NotFound, KeyError, IndexError):
            msg = _("Instance %s could not be found" % id)
            raise webob.exc.HTTPNotFound(explanation=msg)

        return self._create_operation(req, "reset", scope,
                                      start_time, id)

    def add_access_config(self, req, body, scope_id, id):
        context = self._get_context(req)
        scope = self._get_scope(req, scope_id)
        start_time = timeutils.isotime(None, True)
        self._api.add_access_config(context, body, id, scope,
            req.params.get('networkInterface'))

        return self._create_operation(req, "addAccessConfig", scope,
                                      start_time, id)

    def delete_access_config(self, req, scope_id, id):
        context = self._get_context(req)
        scope = self._get_scope(req, scope_id)
        start_time = timeutils.isotime(None, True)
        self._api.delete_access_config(context, id, scope,
           req.params.get('networkInterface'),
           req.params.get('accessConfig'))

        return self._create_operation(req, "deleteAccessConfig", scope,
                                      start_time, id)


def create_resource():
    return gce_wsgi.GCEResource(Controller())
