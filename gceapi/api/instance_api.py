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

from gceapi import exception
from gceapi.openstack.common import log as logging

from gceapi.api import access_config_api
from gceapi.api import base_api
from gceapi.api import clients
from gceapi.api import disk_api
from gceapi.api import firewall_api
from gceapi.api import machine_type_api
from gceapi.api import network_api
from gceapi.api import operation_api
from gceapi.api import project_api
from gceapi.api import utils

LOG = logging.getLogger(__name__)


class API(base_api.API):
    """GCE Instance API"""

    KIND = "instance"
    PERSISTENT_ATTRIBUTES = ["id", "description"]

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
        operation_api.API().register_deferred_operation_method(
                "instance-add",
                self.add_item,
                self.get_add_item_progress)
        operation_api.API().register_deferred_operation_method(
                "instance-delete",
                self.delete_item,
                self.get_delete_item_progress)
        operation_api.API().register_deferred_operation_method(
                "instance-reset",
                self.reset_instance,
                self.get_reset_instance_progress)

    def _get_type(self):
        return self.KIND

    def _get_persistent_attributes(self):
        return self.PERSISTENT_ATTRIBUTES

    def get_item(self, context, name, scope=None):
        return self.search_items(context, {"name": name}, scope)[0]

    def get_items(self, context, scope=None):
        return self.search_items(context, None, scope)

    def get_scopes(self, context, item):
        return [("zone", item["OS-EXT-AZ:availability_zone"])]

    def search_items(self, context, search_opts, scope):
        client = clients.nova(context)
        instances = client.servers.list(search_opts=search_opts)

        filtered_instances = []
        for instance in instances:
            iscope = getattr(instance, "OS-EXT-AZ:availability_zone")
            if scope is not None and scope.get_name() != iscope:
                continue

            instance = utils.to_dict(instance)
            instance = self._prepare_instance(client, context, instance)
            db_instance = self._get_db_item_by_id(context, instance["id"])
            self._prepare_item(instance, db_instance)
            filtered_instances.append(instance)

        if len(filtered_instances) == len(instances) and not search_opts:
            gce_instances = self._get_db_items_dict(context)
            self._purge_db(context, filtered_instances, gce_instances)

        return filtered_instances

    def _prepare_instance(self, client, context, instance):
        instance["statusMessage"] = instance["status"]
        instance["status"] = self._status_map.get(
            instance["status"].lower(), instance["status"])
        instance["flavor"]["name"] = machine_type_api.API().get_item_by_id(
            context, instance["flavor"]["id"])["name"]

        cinder_client = clients.cinder(context)
        volumes = instance["os-extended-volumes:volumes_attached"]
        instance["volumes"] = [
            utils.to_dict(cinder_client.volumes.get(v["id"])) for v in volumes]

        acs = access_config_api.API().get_items(context, instance["name"])
        acs = {ac["addr"]: ac for ac in acs}
        for network in instance["addresses"]:
            for address in instance["addresses"][network]:
                if address["OS-EXT-IPS:type"] == "floating":
                    ac = acs.pop(address["addr"], None)
                    if not ac:
                        ac = access_config_api.API().register_item(context,
                            instance["name"],
                            addr=address["addr"], nic=network)
                    address["name"] = ac["name"]
                    address["type"] = ac["type"]

        for ac in acs:
            ac = access_config_api.API().unregister_item(context,
                instance["name"], acs[ac]["name"])

        return instance

    def _can_delete_network(self, context, network):
        client = clients.nova(context)
        instances = client.servers.list(search_opts=None)
        for instance in instances:
            if network["name"] in instance.networks:
                raise exception.NetworkInUse(network_id=network["id"])

    def _get_instances_with_network(self, context, network, scope):
        affected_instances = []
        client = clients.nova(context)
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
        # TODO(ft): implement common safe method
        # to run add/remove with exception logging
        for instance in affected_instances:
            try:
                instance.add_security_group(secgroup["name"])
            except Exception:
                LOG.exception(("Failed to add instance "
                               "(%s) to security group (%s)"),
                              instance.id, secgroup["name"])

    def _remove_secgroup_from_instances(self, context, secgroup, **kwargs):
        network = firewall_api.API().get_firewall_network(context, secgroup)
        if not network:
            return
        affected_instances = self._get_instances_with_network(
                context, network, kwargs.get("scope"))
        # TODO(ft): implement common safe method
        # to run add/remove with exception logging
        for instance in affected_instances:
            try:
                instance.remove_security_group(secgroup["name"])
            except Exception:
                LOG.exception(("Failed to remove securiy group (%s) "
                               "from instance (%s)"),
                              secgroup["name"], instance.id)

    def reset_instance(self, context, scope, name):
        client = clients.nova(context)
        instances = client.servers.list(search_opts={"name": name})
        if not instances or len(instances) != 1:
            raise exception.NotFound
        instance = instances[0]
        instance.reboot("HARD")
        instance = utils.to_dict(instance)
        instance = self._prepare_instance(client, context, instance)
        return instance

    def delete_item(self, context, name, scope=None):
        client = clients.nova(context)
        instances = client.servers.list(search_opts={"name": name})
        if not instances or len(instances) != 1:
            raise exception.NotFound
        instance = instances[0]
        instance.delete()
        instance = utils.to_dict(instance)
        instance = self._prepare_instance(client, context, instance)
        self._delete_db_item(context, instance)

        acs = access_config_api.API().get_items(context, instance["name"])
        for ac in acs:
            ac = access_config_api.API().unregister_item(context,
                instance["name"], ac["name"])

        return instance

    def add_item(self, context, name, body, scope=None):
        name = body['name']
        client = clients.nova(context)

        flavor_name = utils._extract_name_from_url(body['machineType'])
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
            volume_name = utils._extract_name_from_url(disk["source"])
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
            net_name = utils._extract_name_from_url(net_iface["network"])

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

        instance = utils.to_dict(client.servers.get(instance.id))
        instance = self._prepare_instance(client, context, instance)
        instance["description"] = body.get("description", "")
        instance = self._add_db_item(context, instance)

        for net_iface in body['networkInterfaces']:
            ac = net_iface.get("accessConfigs")
            if not ac:
                continue
            if len(ac) > 1:
                msg = _('At most one access config currently supported.')
                raise exception.InvalidRequest(msg)
            # NOTE(apavlov): only one access config(floating ip) is supported
            ac = ac[0]
            net_name = utils._extract_name_from_url(net_iface["network"])
            access_config_api.API().add_item(context, instance["name"],
                name=ac.get("name"), type=ac.get("type"),
                addr=ac.get("natIP"), nic=net_name)

        return instance

    def get_add_item_progress(self, context, name, instance_id, scope):
        client = clients.nova(context)
        instances = client.servers.list(search_opts={"id": instance_id})
        if (len(instances) == 0 or
                instances[0].status not in ["building"]):
            return {"progress": 100}

    def get_delete_item_progress(self, context, name, instance_id, scope):
        client = clients.nova(context)
        instances = client.servers.list(search_opts={"id": instance_id})
        if len(instances) == 0:
            return {"progress": 100}

    def get_reset_instance_progress(self, context, name, instance_id, scope):
        client = clients.nova(context)
        instances = client.servers.list(search_opts={"id": instance_id})
        if (len(instances) == 0 or
                instances[0].status not in ["stopped", "paused", "suspended"]):
            return {"progress": 100}
