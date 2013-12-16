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

import copy
import os.path

from gceapi.api import base_api
from gceapi.api import network_api
from gceapi import exception
#from nova.network.security_group import openstack_driver
from gceapi.openstack.common import log as logging


DESCRIPTION_NETWORK_SEPARATOR = "-=#=-"
PROTOCOL_MAP = {
    '1': 'icmp',
    '6': 'tcp',
    '17': 'udp',
}
LOG = logging.getLogger(__name__)


class API(base_api.API):
    """GCE Firewall API"""

    def __init__(self, *args, **kwargs):
        super(API, self).__init__(*args, **kwargs)
        #self._secgroup_service = (openstack_driver.
        #    get_openstack_security_group_driver())
        net_api = network_api.API()
        net_api._register_callback(
            base_api._callback_reasons.pre_delete,
            self.delete_network_firewalls)

    def get_item(self, context, name, scope=None):
        firewall = self._secgroup_service.list(
               context, project=context.project_id, names=[name])[0]
        return self._prepare_item(firewall)

    def get_items(self, context, scope=None):
        firewalls = self._secgroup_service.list(
                context, project=context.project_id)
        return [self._prepare_item(firewall)
                for firewall in firewalls]

    def add_item(self, context, name, body, scope=None):
        network = self._get_network_by_url(context, body['network'])
        self._check_rules(body)
        group_description = "".join([body.get("description", ""),
                                     DESCRIPTION_NETWORK_SEPARATOR,
                                     network["name"]])
        group_ref = self._secgroup_service.create_security_group(
            context, body['name'], group_description)
        try:
            rules = self._convert_to_secgroup_rules(group_ref['id'], body)
            self._secgroup_service.add_rules(
                    context, group_ref['id'], group_ref['name'], rules)
        except Exception:
            self._secgroup_service.destroy(context, group_ref)
            raise
        self._process_callbacks(
            context, base_api._callback_reasons.post_add, group_ref)
        return self._prepare_item(group_ref)

    def delete_item(self, context, name, scope=None):
        firewall = self.get_item(context, name)
        self._process_callbacks(
            context, base_api._callback_reasons.pre_delete, firewall)
        self._secgroup_service.destroy(context, firewall)

    def _prepare_item(self, firewall):
        # NOTE(ft): OpenStack security groups are more powerful than
        # gce firewalls so when we cannot completely convert secgroup
        # we add prefixes to firewall description
        # [*] - cidr rules too complex to convert
        # [+] - non-cidr rules presents

        non_cidr_rule_exists = False
        too_complex_for_gce = False

        # NOTE(ft): group OpenStack rules by cidr and proto
        # cidr group must be comparable object
        def _ports_to_str(rule):
            if rule['from_port'] == rule['to_port']:
                return str(rule['from_port'])
            else:
                return "%s-%s" % (rule['from_port'], rule['to_port'])

        grouped_rules = {}
        for rule in firewall['rules']:
            if not rule['cidr']:
                non_cidr_rule_exists = True
                continue
            cidr = rule["cidr"]
            proto = rule['protocol']
            cidr_group = grouped_rules.setdefault(cidr, {})
            proto_ports = cidr_group.setdefault(proto, set())
            proto_ports.add(_ports_to_str(rule))

        # NOTE(ft): compare cidr grups to understand
        # whether OpenStack rules are too complex or not
        common_rules = None
        for cidr in grouped_rules:
            if common_rules:
                if common_rules != grouped_rules[cidr]:
                    too_complex_for_gce = True
                    break
            else:
                common_rules = grouped_rules[cidr]

        # NOTE(ft): check icmp rules:
        # if per icmp type rule present then rules are too complex
        if not too_complex_for_gce and common_rules and "icmp" in common_rules:
            icmp_rules = common_rules["icmp"]
            if len(icmp_rules) == 1:
                icmp_rule = icmp_rules.pop()
                if icmp_rule != "-1":
                    too_complex_for_gce = True
            else:
                too_complex_for_gce = True

        # NOTE(ft): build gce rules if possible
        def _build_gce_port_rule(proto, rules):
            gce_rule = {"IPProtocol": proto}
            if proto != "icmp":
                gce_rule["ports"] = rules
            return gce_rule

        sourceRanges = []
        allowed = []
        if not too_complex_for_gce:
            sourceRanges = [cidr for cidr in grouped_rules] or ["0.0.0.0/0"]
            if common_rules:
                allowed = [_build_gce_port_rule(proto, common_rules[proto])
                           for proto in common_rules]
        firewall["sourceRanges"] = sourceRanges
        firewall["allowed"] = allowed

        # NOTE(ft): add prefixes to description
        description = firewall.get("description")
        prefixes = []
        if too_complex_for_gce:
            prefixes.append("[*]")
        if non_cidr_rule_exists:
            prefixes.append("[+]")
        if prefixes:
            if description is not None:
                prefixes.append(description)
            description = "".join(prefixes)
            firewall["description"] = description

        firewall["network_name"] = self.get_firewall_network_name(firewall)
        return firewall

    def _get_network_by_url(self, context, url):
        network_name = os.path.basename(url)
        return network_api.API().get_item(context, network_name)

    def _check_rules(self, firewall):
        if not firewall.get('sourceRanges') or firewall.get('sourceTags'):
            msg = _("Not 'sourceRange' neither 'sourceTags' is provided")
            raise exception.InvalidRequest(msg)
        for allowed in firewall.get('allowed', []):
            proto = allowed.get('IPProtocol')
            proto = PROTOCOL_MAP.get(proto, proto)
            if not proto or proto not in PROTOCOL_MAP.values():
                msg = _("Invlaid protocol")
                raise exception.InvalidRequest(msg)
            if proto == 'icmp' and allowed.get('ports'):
                msg = _("Invalid options for icmp protocol")
                raise exception.InvalidRequest(msg)

    def _convert_to_secgroup_rules(self, group_id, firewall):
        rules = []
        for source_range in firewall['sourceRanges']:
            for allowed in firewall.get('allowed', []):
                proto = allowed['IPProtocol']
                proto = PROTOCOL_MAP.get(proto, proto)
                rule = {
                    "protocol": proto,
                    "cidr": source_range,
                    "parent_group_id": group_id,
                }
                if proto == "icmp":
                    rule["from_port"] = -1
                    rule["to_port"] = -1
                    rules.append(rule)
                else:
                    for port in allowed.get('ports', []):
                        if "-" in port:
                            from_port, to_port = port.split("-")
                        else:
                            from_port = to_port = port
                        rule["from_port"] = from_port
                        rule["to_port"] = to_port
                        rules.append(copy.copy(rule))
        return rules

    # TODO(ft): implement common safe method
    # to run add/remove with exception logging
    def add_security_group_to_instances(self, context, group, instances):
        for instance in instances:
            try:
                self._secgroup_service.add_to_instance(
                        context, instance, group["id"])
            except exception.InstanceNotRunning:
                LOG.warning(("Failed to add not running "
                             "instance (%s) to security group (%s)"),
                            instance["uuid"], group["name"])
            except Exception:
                LOG.exception(("Failed to add instance "
                               "(%s) to security group (%s)"),
                              instance["uuid"], group["name"])

    def remove_security_group_from_instances(self, context, secgroup,
                                             instances):
        for instance in instances:
            try:
                self._secgroup_service.remove_from_instance(
                        context, instance, secgroup['id'])
            except Exception:
                LOG.exception(("Failed to remove securiy group (%s) "
                               "from instance (%s)"),
                              secgroup["name"], instance["uuid"])

    def get_firewall_network_name(self, firewall):
        description = firewall.get("description")
        desc_parts = description.split(DESCRIPTION_NETWORK_SEPARATOR)
        return desc_parts[1] if len(desc_parts) > 1 else None

    def get_firewall_network(self, context, firewall):
        network_name = self.get_firewall_network_name(firewall)
        return (network_api.API().get_item(context, network_name)
                if network_name else None)

    def get_network_firewalls(self, context, network_name):
        secgroups = self._secgroup_service.list(
                context, project=context.project_id)
        return [f for f in secgroups
                if self.get_firewall_network_name(f) == network_name]

    def delete_network_firewalls(self, context, network):
        network_name = network["name"]
        for secgroup in self.get_network_firewalls(context, network_name):
            try:
                self._secgroup_service.destroy(context, secgroup)
            except Exception:
                LOG.exception(("Failed to delete security group (%s) while"
                               "delete network (%s))"),
                              secgroup["name"], network_name)
