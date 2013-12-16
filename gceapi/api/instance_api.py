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

import time

from nova import context as nova_context
from nova import db
from nova import exception
from nova import network
from nova.compute import api as compute_api
from nova.compute import vm_states
from nova.compute import utils as compute_utils
from nova.openstack.common import log as logging

from gceapi.api import base_api
from gceapi.api import disk_api
from gceapi.api import firewall_api
from gceapi.api import machine_type_api
from gceapi.api import network_api
from gceapi.api import project_api
from gceapi.api import zone_api

LOG = logging.getLogger(__name__)


class API(base_api.API):
    """GCE Instance API"""

    # Instance status. One of the following values:
    # \"PROVISIONING\", \"STAGING\", \"RUNNING\",
    # \"STOPPING\", \"STOPPED\", \"TERMINATED\" (output only).
    _status_map = {
        None: 'TERMINATED',
        vm_states.ACTIVE: 'RUNNING',
        vm_states.BUILDING: 'PROVISIONING',
        vm_states.DELETED: 'TERMINATED',
        vm_states.SOFT_DELETED: 'TERMINATED',
        vm_states.STOPPED: 'STOPPED',
        vm_states.PAUSED: 'STOPPED',
        vm_states.SUSPENDED: 'STOPPED',
        vm_states.RESCUED: 'STOPPED',
        vm_states.RESIZED: 'STOPPED',
        'error': 'TERMINATED'
    }

    def __init__(self, *args, **kwargs):
        super(API, self).__init__(*args, **kwargs)
        self._compute_api = compute_api.API()
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
        return [zone_api.API().get_item_by_host(context, item["host"])]

    def search_items(self, context, search_opts, scope):
        search_opts = search_opts or {}
        search_opts['deleted'] = False
        if context.project_id:
            search_opts['project_id'] = context.project_id
        else:
            search_opts['user_id'] = context.user_id
        instances = self._compute_api.get_all(context, search_opts=search_opts)

        filtered_instances = []
        for instance in instances:
            if (scope is None
            or scope.get_name() in self.get_scopes(context, instance)):
                instance = self._prepare_instance(context, instance)
                filtered_instances.append(instance)

        return filtered_instances

    def _prepare_instance(self, context, instance):
        instance["name"] = instance["display_name"]
        instance["status"] = self._status_map.get(
            instance["vm_state"], instance["vm_state"])

        instance["cached_nwinfo"] = \
            compute_utils.get_nw_info_for_instance(instance)

        attached_disks = db.block_device_mapping_get_all_by_instance(
            nova_context.get_admin_context(), instance['uuid'])
        for disk in attached_disks:
            disk["volume"] = disk_api.API().get_item_by_id(
                context, disk["volume_id"])
        instance["attached_disks"] = attached_disks

        return instance

    def _can_delete_network(self, context, network):
        instances = self.search_items(context, None, None)
        for instance in instances:
            cached_info = instance["cached_nwinfo"]
            inst_network = cached_info.legacy()
            for net, dummy in inst_network:
                network_id = net.get('id')
                if network_id == network["id"]:
                    raise exception.NetworkInUse(network_id=network_id)

    def _get_instances_with_network(self, context, network, scope):
        affected_instances = []
        network_id = network['id']
        instances = self.get_items(context, scope)
        for instance in instances:
            cached_nwinfo = compute_utils.get_nw_info_for_instance(instance)
            if cached_nwinfo:
                for network_info in cached_nwinfo:
                    if network_id == network_info['network']['id']:
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
        instance = self.search_items(context, {"name": name}, scope)[0]
        self._compute_api.reboot(context, instance, 'HARD')

    def delete_item(self, context, name, scope=None):
        instance = self.search_items(context, {"name": name}, scope)[0]
        self._compute_api.delete(context, instance)

    def add_item(self, context, name, body, scope=None):
        name = body['name']

        networks_names = []
        for net_iface in body['networkInterfaces']:
            networks_names.append(net_iface['network'].split('/')[-1])

        networks = []
        #NOTE(ft) 'default' security group contains output rules
        #but output rules doesn't configurable by GCE API
        #all outgoing traffic permitted
        #so we support this behaviour
        groups_names = set(['default'])
        for net_name in networks_names:
            network_settings = network_api.API().get_item(
                context, net_name, scope)
            networks.append(network_api.API().format_network(network_settings))
            for sg in firewall_api.API().get_network_firewalls(
                    context, net_name):
                groups_names.add(sg["name"])
        groups_names = list(groups_names)

        description = body.get('description')

        try:
            metadatas = body['metadata']['items']
        except KeyError:
            metadatas = []
        instance_metadata = dict([(x['key'], x['value']) for x in metadatas])
        ssh_keys = instance_metadata.pop('sshKeys', None)
        if ssh_keys is not None:
            key_name, key_data = ssh_keys.split('\n')[0].split(":")
        else:
            key_name, key_data = project_api.API() \
                .get_gce_user_keypair(context)

        image_id = None
        instance_disks = body.get('disks', [])
        disks = []
        for disk in instance_disks:
            device_name = disk["deviceName"]
            volume_name = disk["source"].split("/")[-1]
            try:
                # NOTE(apavlov): waiting for 15 seconds
                #     while image will be downloaded and unpacked
                # TODO(apavlov): find some way to wait on some event
                for _ in xrange(15):
                    volume = disk_api.API().get_item(
                        context, volume_name, scope)
                    if not volume:
                        continue
                    volume_status = volume['status']
                    if volume_status == 'READY' or 'FAILED' in volume_status:
                        break
                    time.sleep(1)

                disks.append({
                    "volume_id": volume['id'],
                    "device_name": device_name,
                    "volume_size": "",
                    "delete_on_termination": 0})
                if disk['boot'] and 'volume_image_metadata' in volume:
                    image_id = volume['volume_image_metadata']['image_id']
            except exception.VolumeNotFound:
                pass

        flavor_name = body['machineType'].split('/')[-1].replace("-", ".")
        instance_type = machine_type_api.API() \
            .get_item(context, flavor_name, scope)

        self._compute_api.create(
            context,
            instance_type,
            image_id,
            display_name=name,
            display_description=description,
            min_count=1,
            max_count=1,
            metadata=instance_metadata,
            security_group=groups_names,
            key_name=key_name,
            key_data=key_data,
            requested_networks=networks,
            block_device_mapping=disks)

        return self.search_items(context, {"name": name}, scope)[0]

    def add_access_config(self, context,
                          body, item_id, scope, network_interface):

        address = body.get('natIP')

        instance = self.search_items(context, {"name": item_id}, scope)[0]

        cached_nwinfo = compute_utils.get_nw_info_for_instance(instance)
        if not cached_nwinfo:
            msg = _('No nw_info cache associated with instance')
            raise exception.InvalidRequest(msg)

        port_to_be_associated = None
        for network_info in cached_nwinfo:
            if network_info['network']['label'] == network_interface:
                subnets = network_info['network']['subnets']
                if len(subnets) == 0:
                    msg = _('No fixed ips associated to instance')
                    raise exception.InvalidRequest(msg)
                if len(subnets) > 1:
                    msg = _('multiple subnets exist, using the first: %s')
                    LOG.warning(msg, subnets[0]['cidr'])
                fixed_ips = subnets[0]['ips']
                if len(fixed_ips) == 0:
                    msg = _('No fixed ips associated to instance')
                    raise exception.InvalidRequest(msg)
                if len(fixed_ips) > 1:
                    msg = _('multiple fixed_ips exist, using the first: %s')
                    LOG.warning(msg, fixed_ips[0]['address'])
                port_to_be_associated = fixed_ips[0]['address']
                break
        else:
            msg = _('Network interface not found')
            raise exception.InvalidRequest(msg)

        floating_ips = network.API().get_floating_ips_by_project(context)
        if address is None:
            # try to find unused
            for floating_ip in floating_ips:
                if floating_ip['fixed_ip_id'] is None:
                    address = floating_ip['address']
                    break
            else:
                msg = _('There is no unused floating ips.')
                raise exception.InvalidRequest(msg)
        else:
            for floating_ip in floating_ips:
                if floating_ip['address'] != address:
                    continue

                if floating_ip['fixed_ip_id'] is None:
                    break

                msg = _("Floating ip '%s' is already associated" % address)
                raise exception.InvalidRequest(msg)
            else:
                msg = _("There is no such floating ip '%s'." % address)
                raise exception.InvalidRequest(msg)

        network.API().associate_floating_ip(context, instance,
            floating_address=address,
            fixed_address=port_to_be_associated)

    def delete_access_config(self, context, item_id, scope,
                             network_interface, address):

        instance = self.search_items(context, {"name": item_id}, scope)[0]

        try:
            floating_ip = network.API() \
                .get_floating_ip_by_address(context, address)
        except exception.FloatingIpNotFoundForAddress:
            msg = _("floating ip not found")
            raise exception.NotFound(explanation=msg)

        # NOTE(apavlov) we don`t test that address belongs to network_interface

        if (floating_ip['instance'] is None
            or floating_ip['instance']['uuid'] != instance['uuid']):
                msg = _("floating ip doesn`t belong to this instance")
                raise exception.InvalidRequest(message=msg)

        network.API().disassociate_floating_ip(context, instance, address)
