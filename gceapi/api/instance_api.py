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

import string

from gceapi.openstack.common.gettextutils import _
from gceapi import exception
from gceapi.openstack.common import log as logging

from gceapi.api import base_api
from gceapi.api import clients
from gceapi.api import disk_api
from gceapi.api import firewall_api
from gceapi.api import machine_type_api
from gceapi.api import network_api
from gceapi.api import project_api
from gceapi.api import utils

LOG = logging.getLogger(__name__)


class API(base_api.API):
    """GCE Instance API"""

    DEFAULT_ACCESS_CONFIG_NAME = "External NAT"
    DEFAULT_ACCESS_CONFIG_TYPE = "ONE_TO_ONE_NAT"

    # NOTE(apavlov): Instance status. One of the following values:
    # \"PROVISIONING\", \"STAGING\", \"RUNNING\",
    # \"STOPPING\", \"STOPPED\", \"TERMINATED\" (output only).
    _status_map = {
        None: 'TERMINATED',
        "active": 'RUNNING',
        "building": 'PROVISIONING',
        "deleted": 'TERMINATED',
        "soft-delete": 'TERMINATED',
        "stopped": 'STOPPED',
        "paused": 'STOPPED',
        "suspended": 'STOPPED',
        "rescued": 'STOPPED',
        "resized": 'STOPPED',
        'error': 'TERMINATED'
    }

    def __init__(self, *args, **kwargs):
        super(API, self).__init__(*args, **kwargs)
        network_api.API()._register_callback(
            base_api._callback_reasons.check_delete,
            self._can_delete_network)
        firewall_api.API()._register_callback(
            base_api._callback_reasons.post_add,
            self._add_secgroup_to_instances)
        firewall_api.API()._register_callback(
            base_api._callback_reasons.pre_delete,
            self._remove_secgroup_from_instances)

    def get_item(self, context, name, scope=None):
        return self.search_items(context, {"name": name}, scope)[0]

    def get_items(self, context, scope=None):
        return self.search_items(context, None, scope)

    def get_scopes(self, context, item):
        return [item["OS-EXT-AZ:availability_zone"]]

    def search_items(self, context, search_opts, scope):
        client = clients.Clients(context).nova()
        instances = client.servers.list(search_opts=search_opts)
        filtered_instances = []
        for instance in instances:
            iscope = getattr(instance, "OS-EXT-AZ:availability_zone")
            if (scope is None
            or scope.get_name() == iscope):
                instance = utils.todict(instance)
                instance = self._prepare_instance(client, context, instance)
                filtered_instances.append(instance)

        return filtered_instances

    def _prepare_instance(self, client, context, instance):
        instance["status"] = self._status_map.get(
            instance["status"].lower(), instance["status"])
        instance["flavor"]["name"] = machine_type_api.API().get_item_by_id(
            context, instance["flavor"]["id"])["name"]

        cinder_client = clients.Clients(context).cinder()
        volumes = instance["os-extended-volumes:volumes_attached"]
        instance["volumes"] = [
            utils.todict(cinder_client.volumes.get(v["id"])) for v in volumes]

        for network in instance["addresses"]:
            for address in instance["addresses"][network]:
                if address["OS-EXT-IPS:type"] == "floating":
                    address["name"] = self.DEFAULT_ACCESS_CONFIG_NAME
                    address["type"] = self.DEFAULT_ACCESS_CONFIG_TYPE

        return instance

    def _can_delete_network(self, context, network):
        client = clients.Clients(context).nova()
        instances = client.servers.list(search_opts=None)
        for instance in instances:
            if network["name"] in instance.networks:
                raise exception.NetworkInUse(network_id=network["id"])

    def _get_instances_with_network(self, context, network, scope):
        affected_instances = []
        client = clients.Clients(context).nova()
        instances = client.servers.list(search_opts=None)
        for instance in instances:
            if network["name"] in instance.networks:
                affected_instances.append(instance)
        return affected_instances

    def _add_secgroup_to_instances(self, context, secgroup, **kwargs):
        network = firewall_api.API().get_firewall_network(context, secgroup)
        if not network:
            return
        affected_instances = self._get_instances_with_network(
                context, network, kwargs.get("scope"))
        firewall_api.API().add_security_group_to_instances(context, secgroup,
                                                            affected_instances)

    def _remove_secgroup_from_instances(self, context, secgroup, **kwargs):
        network = firewall_api.API().get_firewall_network(context, secgroup)
        if not network:
            return
        affected_instances = self._get_instances_with_network(
                context, network, kwargs.get("scope"))
        firewall_api.API().remove_security_group_from_instances(
                context, secgroup, affected_instances)

    def reset_instance(self, context, scope, name):
        client = clients.Clients(context).nova()
        instances = client.servers.list(search_opts={"name": name})
        if not instances or len(instances) != 1:
            raise exception.NotFound
        instances[0].reboot("HARD")

    def delete_item(self, context, name, scope=None):
        client = clients.Clients(context).nova()
        instances = client.servers.list(search_opts={"name": name})
        if not instances or len(instances) != 1:
            raise exception.NotFound
        instances[0].delete()

    def add_item(self, context, name, body, scope=None):
        name = body['name']
        # TODO(apavlov): store description somewhere
        #description = body.get('description')
        client = clients.Clients(context).nova()

        # TODO(apavlov): use extract_name_from_url method
        flavor_name = body['machineType'].split('/')[-1]
        flavor_id = machine_type_api.API().get_item(
            context, flavor_name, scope)["id"]

        try:
            metadatas = body['metadata']['items']
        except KeyError:
            metadatas = []
        instance_metadata = dict([(x['key'], x['value']) for x in metadatas])

        ssh_keys = instance_metadata.pop('sshKeys', None)
        if ssh_keys is not None:
            key_name = ssh_keys.split('\n')[0].split(":")[0]
        else:
            key_name = project_api.API().get_gce_user_keypair_name(context)

        disks = body.get('disks', [])
        disks.sort(None, lambda x: x.get("boot", False), True)
        bdm = dict()
        diskDevice = 0
        for disk in disks:
            # TODO(apavlov): store disk["deviceName"] in DB
            device_name = "vd" + string.ascii_lowercase[diskDevice]
            # TODO(apavlov): use extract_name_from_url method
            volume_name = disk["source"].split("/")[-1]
            volume = disk_api.API().get_item(context, volume_name, scope)
            bdm[device_name] = volume['id']
            diskDevice += 1

        nics = []
        #NOTE(ft) 'default' security group contains output rules
        #but output rules doesn't configurable by GCE API
        #all outgoing traffic permitted
        #so we support this behaviour
        groups_names = set(['default'])
        for net_iface in body['networkInterfaces']:
            # TODO(apavlov): use extract_name_from_url method
            net_name = net_iface["network"].split("/")[-1]

            # TODO(apavlov): parse net_iface["accessConfigs"] and do it
            # it can exists in three ways:
            # None
            # [{"name": "External NAT", "type": "ONE_TO_ONE_NAT"}]
            # as two plus "natIP": "173.255.118.146"

            network = network_api.API().get_item(context, net_name, None)
            nics.append({"net-id": network["id"]})
            for sg in firewall_api.API().get_network_firewalls(
                    context, net_name):
                groups_names.add(sg["name"])
        groups_names = list(groups_names)

        instance = client.servers.create(name, None, flavor_id,
            meta=instance_metadata, min_count=1, max_count=1,
            security_groups=groups_names, key_name=key_name,
            availability_zone=scope.get_name(), block_device_mapping=bdm,
            nics=nics)

        instance = instance = client.servers.get(instance.id)
        return self._prepare_instance(client, context, utils.todict(instance))

    def add_access_config(self, context,
                          body, item_id, scope, network_interface):
        if body["type"] != self.DEFAULT_ACCESS_CONFIG_TYPE:
            msg = _("Only '%s' type of access config currently supported."
                    % self.DEFAULT_ACCESS_CONFIG_TYPE)
            raise exception.InvalidRequest(msg)

        # TODO(apavlov): we should store body["name"] for later usage.
        # waiting for db...
        if body["name"] != self.DEFAULT_ACCESS_CONFIG_NAME:
            msg = _('Only default name of access config currently supported.')
            raise exception.InvalidRequest(msg)

        input_ip = body.get('natIP')

        client = clients.Clients(context).nova()
        instances = client.servers.list(search_opts={"name": item_id})
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
        if input_ip is None:
            # try to find unused
            for floating_ip in floating_ips:
                if floating_ip.instance_id is None:
                    input_ip = floating_ip.ip
                    break
            else:
                msg = _('There is no unused floating ips.')
                raise exception.InvalidRequest(msg)
        else:
            for floating_ip in floating_ips:
                if floating_ip.ip != input_ip:
                    continue
                if floating_ip.instance_id is None:
                    break
                msg = _("Floating ip '%s' is already associated" % floating_ip)
                raise exception.InvalidRequest(msg)
            else:
                msg = _("There is no such floating ip '%s'." % input_ip)
                raise exception.InvalidRequest(msg)

        instance.add_floating_ip(input_ip, fixed_ip)

    def delete_access_config(self, context, item_id, scope,
                             network_interface, accessConfig):
        client = clients.Clients(context).nova()
        instances = client.servers.list(search_opts={"name": item_id})
        if not instances or len(instances) != 1:
            raise exception.NotFound
        instance = instances[0]

        # TODO(apavlov): we should find accessConfig(its a given name at
        # creation) and remove specific address. waiting for db...
        # now we can delete by address only
        # floating_ip = db.find_resource("floating_ip", accessConfig)
        # and next will be removed
        floating_ip = None
        if accessConfig != self.DEFAULT_ACCESS_CONFIG_NAME:
            msg = _('Only default name of access config currently supported.')
            raise exception.InvalidRequest(msg)
        for network in instance.addresses:
            if network_interface != network:
                continue
            for address in instance.addresses[network]:
                if address["OS-EXT-IPS:type"] == "floating":
                    floating_ip = address["addr"]

        if floating_ip is None:
            msg = _("There is no such floating ip '%s'." % floating_ip)
            raise exception.InvalidRequest(msg)

        instance.remove_floating_ip(floating_ip)
