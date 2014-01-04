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

from gceapi.openstack.common.gettextutils import _
from gceapi import exception
from gceapi.openstack.common import log as logging

from gceapi.api import base_api
from gceapi.api import clients

LOG = logging.getLogger(__name__)


class API(base_api.API):
    """GCE Access config API"""

    KIND = "access_config"
    PERSISTENT_ATTRIBUTES = ["id", "instance_name",
                             "nic", "name", "type", "addr"]
    DEFAULT_ACCESS_CONFIG_TYPE = "ONE_TO_ONE_NAT"
    DEFAULT_ACCESS_CONFIG_NAME = "External NAT"

    def __init__(self, *args, **kwargs):
        super(API, self).__init__(*args, **kwargs)

    def _get_type(self):
        return self.KIND

    def _get_persistent_attributes(self):
        return self.PERSISTENT_ATTRIBUTES

    def _are_api_operations_pending(self):
        return True

    def get_item(self, context, instance_name, name):
        items = self._get_db_items(context)
        items = [i for i in items
                if i["instance_name"] == instance_name and i["name"] == name]
        if len(items) != 1:
            raise exception.NotFound
        return items[0]

    def get_items(self, context, instance_name):
        items = self._get_db_items(context)
        return [i for i in items if i["instance_name"] == instance_name]

    def add_item(self, context, instance_name, **kwargs):
        network_interface = kwargs.get("nic")
        if not network_interface:
            msg = _("Network interface is invalid or empty")
            raise exception.InvalidRequest(msg)

        item_type = kwargs.get("type", self.DEFAULT_ACCESS_CONFIG_TYPE)
        if item_type != self.DEFAULT_ACCESS_CONFIG_TYPE:
            msg = _("Only '%s' type of access config currently supported."
                    % self.DEFAULT_ACCESS_CONFIG_TYPE)
            raise exception.InvalidRequest(msg)

        addr = kwargs.get("addr")

        client = clients.nova(context)
        instances = client.servers.list(search_opts={"name": instance_name})
        if not instances or len(instances) != 1:
            raise exception.NotFound
        instance = instances[0]

        fixed_ip = None
        for network in instance.addresses:
            if network_interface != network:
                continue
            for address in instance.addresses[network]:
                atype = address["OS-EXT-IPS:type"]
                if atype == "floating":
                    msg = _('At most one access config currently supported.')
                    raise exception.InvalidRequest(msg)
                if atype == "fixed":
                    fixed_ip = address["addr"]

        if not fixed_ip:
            msg = _('Network interface not found')
            raise exception.InvalidRequest(msg)

        floating_ips = client.floating_ips.list()
        if addr is None:
            # NOTE(apavlov): try to find unused
            for floating_ip in floating_ips:
                if floating_ip.instance_id is None:
                    addr = floating_ip.ip
                    break
            else:
                msg = _('There is no unused floating ips.')
                raise exception.InvalidRequest(msg)
        else:
            for floating_ip in floating_ips:
                if floating_ip.ip != addr:
                    continue
                if floating_ip.instance_id is None:
                    break
                msg = _("Floating ip '%s' is already associated" % floating_ip)
                raise exception.InvalidRequest(msg)
            else:
                msg = _("There is no such floating ip '%s'." % addr)
                raise exception.InvalidRequest(msg)

        instance.add_floating_ip(addr, fixed_ip)
        kwargs["addr"] = addr

        return self.register_item(context, instance_name, **kwargs)

    def register_item(self, context, instance_name, **kwargs):
        network_interface = kwargs.get("nic")
        if not network_interface:
            msg = _("Network interface is invalid or empty")
            raise exception.InvalidRequest(msg)

        item_type = kwargs.get("type", self.DEFAULT_ACCESS_CONFIG_TYPE)
        if item_type != self.DEFAULT_ACCESS_CONFIG_TYPE:
            msg = _("Only '%s' type of access config currently supported."
                    % self.DEFAULT_ACCESS_CONFIG_TYPE)
            raise exception.InvalidRequest(msg)

        item_name = kwargs.get("name", self.DEFAULT_ACCESS_CONFIG_NAME)
        addr = kwargs.get("addr")
        if not addr:
            msg = _("There is no address to assign.")
            raise exception.InvalidRequest(msg)

        new_item = {
            "id": instance_name + "-" + addr,
            "instance_name": instance_name,
            "nic": network_interface,
            "name": item_name,
            "type": item_type,
            "addr": addr
        }
        new_item = self._add_db_item(context, new_item)
        return new_item

    def delete_item(self, context, instance_name, name):
        client = clients.nova(context)
        instances = client.servers.list(search_opts={"name": instance_name})
        if not instances or len(instances) != 1:
            raise exception.NotFound
        instance = instances[0]

        item = self.get_item(context, instance_name, name)
        floating_ip = item["addr"]
        instance.remove_floating_ip(floating_ip)
        self._delete_db_item(context, item)

    def unregister_item(self, context, instance_name, name):
        item = self.get_item(context, instance_name, name)
        self._delete_db_item(context, item)
