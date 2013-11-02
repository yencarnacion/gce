# vim: tabstop=4 shiftwidth=4 softtabstop=4
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

import json

from tempest.common.rest_client import RestClient


class NetworkClientJSON(RestClient):

    """
    Tempest REST client for Neutron. Uses v2 of the Neutron API, since the
    V1 API has been removed from the code base.

    Implements create, delete, update, list and show for the basic Neutron
    abstractions (networks, sub-networks, routers, ports and floating IP):

    Implements add/remove interface to router using subnet ID / port ID

    It also implements list, show, update and reset for OpenStack Networking
    quotas
    """

    def __init__(self, config, username, password, auth_url, tenant_name=None):
        super(NetworkClientJSON, self).__init__(config, username, password,
                                                auth_url, tenant_name)
        self.service = self.config.network.catalog_type
        self.version = '2.0'
        self.uri_prefix = "v%s" % (self.version)

    def list_networks(self):
        uri = '%s/networks' % (self.uri_prefix)
        resp, body = self.get(uri, self.headers)
        body = json.loads(body)
        return resp, body

    def create_network(self, name, **kwargs):
        post_body = {'network': kwargs}
        post_body['network']['name'] = name
        body = json.dumps(post_body)
        uri = '%s/networks' % (self.uri_prefix)
        resp, body = self.post(uri, headers=self.headers, body=body)
        body = json.loads(body)
        return resp, body

    def create_bulk_network(self, count, names):
        network_list = list()
        for i in range(count):
            network_list.append({'name': names[i]})
        post_body = {'networks': network_list}
        body = json.dumps(post_body)
        uri = '%s/networks' % (self.uri_prefix)
        resp, body = self.post(uri, headers=self.headers, body=body)
        body = json.loads(body)
        return resp, body

    def show_network(self, uuid):
        uri = '%s/networks/%s' % (self.uri_prefix, uuid)
        resp, body = self.get(uri, self.headers)
        body = json.loads(body)
        return resp, body

    def delete_network(self, uuid):
        uri = '%s/networks/%s' % (self.uri_prefix, uuid)
        resp, body = self.delete(uri, self.headers)
        return resp, body

    def create_subnet(self, net_uuid, cidr, ip_version=4, **kwargs):
        post_body = {'subnet': kwargs}
        post_body['subnet']['ip_version'] = ip_version
        post_body['subnet']['network_id'] = net_uuid
        post_body['subnet']['cidr'] = cidr
        body = json.dumps(post_body)
        uri = '%s/subnets' % (self.uri_prefix)
        resp, body = self.post(uri, headers=self.headers, body=body)
        body = json.loads(body)
        return resp, body

    def delete_subnet(self, uuid):
        uri = '%s/subnets/%s' % (self.uri_prefix, uuid)
        resp, body = self.delete(uri, self.headers)
        return resp, body

    def list_subnets(self):
        uri = '%s/subnets' % (self.uri_prefix)
        resp, body = self.get(uri, self.headers)
        body = json.loads(body)
        return resp, body

    def show_subnet(self, uuid):
        uri = '%s/subnets/%s' % (self.uri_prefix, uuid)
        resp, body = self.get(uri, self.headers)
        body = json.loads(body)
        return resp, body

    def create_port(self, network_id, **kwargs):
        post_body = {
            'port': {
                'network_id': network_id,
            }
        }
        for key, val in kwargs.items():
            post_body['port'][key] = val
        body = json.dumps(post_body)
        uri = '%s/ports' % (self.uri_prefix)
        resp, body = self.post(uri, headers=self.headers, body=body)
        body = json.loads(body)
        return resp, body

    def delete_port(self, port_id):
        uri = '%s/ports/%s' % (self.uri_prefix, port_id)
        resp, body = self.delete(uri, self.headers)
        return resp, body

    def list_ports(self, **filters):
        uri = '%s/ports' % (self.uri_prefix)
        filter_items = ["%s=%s" % (k, v) for (k, v) in filters.iteritems()]
        querystring = "&".join(filter_items)
        if querystring:
            uri = "%s?%s" % (uri, querystring)
        resp, body = self.get(uri, self.headers)
        body = json.loads(body)
        return resp, body

    def show_port(self, port_id):
        uri = '%s/ports/%s' % (self.uri_prefix, port_id)
        resp, body = self.get(uri, self.headers)
        body = json.loads(body)
        return resp, body

    def update_quotas(self, tenant_id, **kwargs):
        put_body = {'quota': kwargs}
        body = json.dumps(put_body)
        uri = '%s/quotas/%s' % (self.uri_prefix, tenant_id)
        resp, body = self.put(uri, body, self.headers)
        body = json.loads(body)
        return resp, body['quota']

    def show_quotas(self, tenant_id):
        uri = '%s/quotas/%s' % (self.uri_prefix, tenant_id)
        resp, body = self.get(uri, self.headers)
        body = json.loads(body)
        return resp, body['quota']

    def reset_quotas(self, tenant_id):
        uri = '%s/quotas/%s' % (self.uri_prefix, tenant_id)
        resp, body = self.delete(uri, self.headers)
        return resp, body

    def list_quotas(self):
        uri = '%s/quotas' % (self.uri_prefix)
        resp, body = self.get(uri, self.headers)
        body = json.loads(body)
        return resp, body['quotas']

    def update_subnet(self, subnet_id, new_name):
        put_body = {
            'subnet': {
                'name': new_name,
            }
        }
        body = json.dumps(put_body)
        uri = '%s/subnets/%s' % (self.uri_prefix, subnet_id)
        resp, body = self.put(uri, body=body, headers=self.headers)
        body = json.loads(body)
        return resp, body

    def update_port(self, port_id, new_name):
        put_body = {
            'port': {
                'name': new_name,
            }
        }
        body = json.dumps(put_body)
        uri = '%s/ports/%s' % (self.uri_prefix, port_id)
        resp, body = self.put(uri, body=body, headers=self.headers)
        body = json.loads(body)
        return resp, body

    def update_network(self, network_id, new_name):
        put_body = {
            "network": {
                "name": new_name,
            }
        }
        body = json.dumps(put_body)
        uri = '%s/networks/%s' % (self.uri_prefix, network_id)
        resp, body = self.put(uri, body=body, headers=self.headers)
        body = json.loads(body)
        return resp, body

    def list_routers(self):
        uri = '%s/routers' % (self.uri_prefix)
        resp, body = self.get(uri, self.headers)
        body = json.loads(body)
        return resp, body

    def create_router(self, name, admin_state_up=True, **kwargs):
        post_body = {'router': kwargs}
        post_body['router']['name'] = name
        post_body['router']['admin_state_up'] = admin_state_up
        body = json.dumps(post_body)
        uri = '%s/routers' % (self.uri_prefix)
        resp, body = self.post(uri, headers=self.headers, body=body)
        body = json.loads(body)
        return resp, body

    def delete_router(self, router_id):
        uri = '%s/routers/%s' % (self.uri_prefix, router_id)
        resp, body = self.delete(uri, self.headers)
        return resp, body

    def show_router(self, router_id):
        uri = '%s/routers/%s' % (self.uri_prefix, router_id)
        resp, body = self.get(uri, self.headers)
        body = json.loads(body)
        return resp, body

    def _update_router(self, router_id, set_enable_snat, **kwargs):
        uri = '%s/routers/%s' % (self.uri_prefix, router_id)
        resp, body = self.get(uri, self.headers)
        body = json.loads(body)
        update_body = {}
        update_body['name'] = kwargs.get('name', body['router']['name'])
        update_body['admin_state_up'] = kwargs.get(
            'admin_state_up', body['router']['admin_state_up'])
        cur_gw_info = body['router']['external_gateway_info']
        if cur_gw_info and not set_enable_snat:
            cur_gw_info.pop('enable_snat', None)
        update_body['external_gateway_info'] = kwargs.get(
            'external_gateway_info', body['router']['external_gateway_info'])
        update_body = dict(router=update_body)
        update_body = json.dumps(update_body)
        resp, body = self.put(uri, update_body, self.headers)
        body = json.loads(body)
        return resp, body

    def update_router(self, router_id, **kwargs):
        """Update a router leaving enable_snat to its default value."""
        # If external_gateway_info contains enable_snat the request will fail
        # with 404 unless executed with admin client, and therefore we instruct
        # _update_router to not set this attribute
        # NOTE(salv-orlando): The above applies as long as Neutron's default
        # policy is to restrict enable_snat usage to admins only.
        return self._update_router(router_id, set_enable_snat=False, **kwargs)

    def update_router_with_snat_gw_info(self, router_id, **kwargs):
        """Update a router passing also the enable_snat attribute.

        This method must be execute with admin credentials, otherwise the API
        call will return a 404 error.
        """
        return self._update_router(router_id, set_enable_snat=True, **kwargs)

    def add_router_interface_with_subnet_id(self, router_id, subnet_id):
        uri = '%s/routers/%s/add_router_interface' % (self.uri_prefix,
              router_id)
        update_body = {"subnet_id": subnet_id}
        update_body = json.dumps(update_body)
        resp, body = self.put(uri, update_body, self.headers)
        body = json.loads(body)
        return resp, body

    def add_router_interface_with_port_id(self, router_id, port_id):
        uri = '%s/routers/%s/add_router_interface' % (self.uri_prefix,
              router_id)
        update_body = {"port_id": port_id}
        update_body = json.dumps(update_body)
        resp, body = self.put(uri, update_body, self.headers)
        body = json.loads(body)
        return resp, body

    def remove_router_interface_with_subnet_id(self, router_id, subnet_id):
        uri = '%s/routers/%s/remove_router_interface' % (self.uri_prefix,
              router_id)
        update_body = {"subnet_id": subnet_id}
        update_body = json.dumps(update_body)
        resp, body = self.put(uri, update_body, self.headers)
        body = json.loads(body)
        return resp, body

    def remove_router_interface_with_port_id(self, router_id, port_id):
        uri = '%s/routers/%s/remove_router_interface' % (self.uri_prefix,
              router_id)
        update_body = {"port_id": port_id}
        update_body = json.dumps(update_body)
        resp, body = self.put(uri, update_body, self.headers)
        body = json.loads(body)
        return resp, body

    def create_floating_ip(self, ext_network_id, **kwargs):
        post_body = {
            'floatingip': kwargs}
        post_body['floatingip']['floating_network_id'] = ext_network_id
        body = json.dumps(post_body)
        uri = '%s/floatingips' % (self.uri_prefix)
        resp, body = self.post(uri, headers=self.headers, body=body)
        body = json.loads(body)
        return resp, body

    def list_security_groups(self):
        uri = '%s/security-groups' % (self.uri_prefix)
        resp, body = self.get(uri, self.headers)
        body = json.loads(body)
        return resp, body

    def delete_security_group(self, secgroup_id):
        uri = '%s/security-groups/%s' % (self.uri_prefix, secgroup_id)
        resp, body = self.delete(uri, self.headers)
        return resp, body

    def create_security_group(self, name, **kwargs):
        post_body = {
            'security_group': {
                'name': name,
            }
        }
        for key, value in kwargs.iteritems():
            post_body['security_group'][str(key)] = value
        body = json.dumps(post_body)
        uri = '%s/security-groups' % (self.uri_prefix)
        resp, body = self.post(uri, headers=self.headers, body=body)
        body = json.loads(body)
        return resp, body

    def show_floating_ip(self, floating_ip_id):
        uri = '%s/floatingips/%s' % (self.uri_prefix, floating_ip_id)
        resp, body = self.get(uri, self.headers)
        body = json.loads(body)
        return resp, body

    def show_security_group(self, secgroup_id):
        uri = '%s/security-groups/%s' % (self.uri_prefix, secgroup_id)
        resp, body = self.get(uri, self.headers)
        body = json.loads(body)
        return resp, body

    def list_floating_ips(self):
        uri = '%s/floatingips' % (self.uri_prefix)
        resp, body = self.get(uri, self.headers)
        body = json.loads(body)
        return resp, body

    def list_security_group_rules(self):
        uri = '%s/security-group-rules' % (self.uri_prefix)
        resp, body = self.get(uri, self.headers)
        body = json.loads(body)
        return resp, body

    def delete_floating_ip(self, floating_ip_id):
        uri = '%s/floatingips/%s' % (self.uri_prefix, floating_ip_id)
        resp, body = self.delete(uri, self.headers)
        return resp, body

    def update_floating_ip(self, floating_ip_id, **kwargs):
        post_body = {
            'floatingip': kwargs}
        body = json.dumps(post_body)
        uri = '%s/floatingips/%s' % (self.uri_prefix, floating_ip_id)
        resp, body = self.put(uri, headers=self.headers, body=body)
        body = json.loads(body)
        return resp, body

    def create_security_group_rule(self, secgroup_id,
                                   direction='ingress', **kwargs):
        post_body = {
            'security_group_rule': {
                'direction': direction,
                'security_group_id': secgroup_id
            }
        }
        for key, value in kwargs.iteritems():
            post_body['security_group_rule'][str(key)] = value
        body = json.dumps(post_body)
        uri = '%s/security-group-rules' % (self.uri_prefix)
        resp, body = self.post(uri, headers=self.headers, body=body)
        body = json.loads(body)
        return resp, body

    def create_bulk_subnet(self, subnet_list):
        post_body = {'subnets': subnet_list}
        body = json.dumps(post_body)
        uri = '%s/subnets' % (self.uri_prefix)
        resp, body = self.post(uri, headers=self.headers, body=body)
        body = json.loads(body)
        return resp, body

    def delete_security_group_rule(self, rule_id):
        uri = '%s/security-group-rules/%s' % (self.uri_prefix, rule_id)
        resp, body = self.delete(uri, self.headers)
        return resp, body

    def show_security_group_rule(self, rule_id):
        uri = '%s/security-group-rules/%s' % (self.uri_prefix, rule_id)
        resp, body = self.get(uri, self.headers)
        body = json.loads(body)
        return resp, body

    def create_bulk_port(self, port_list):
        post_body = {'ports': port_list}
        body = json.dumps(post_body)
        uri = '%s/ports' % (self.uri_prefix)
        resp, body = self.post(uri, headers=self.headers, body=body)
        body = json.loads(body)
        return resp, body

    def list_vips(self):
        uri = '%s/lb/vips' % (self.uri_prefix)
        resp, body = self.get(uri, self.headers)
        body = json.loads(body)
        return resp, body

    def create_vip(self, name, protocol, protocol_port, subnet_id, pool_id):
        post_body = {
            "vip": {
                "protocol": protocol,
                "name": name,
                "subnet_id": subnet_id,
                "pool_id": pool_id,
                "protocol_port": protocol_port
            }
        }
        body = json.dumps(post_body)
        uri = '%s/lb/vips' % (self.uri_prefix)
        resp, body = self.post(uri, headers=self.headers, body=body)
        body = json.loads(body)
        return resp, body

    def create_pool(self, name, lb_method, protocol, subnet_id):
        post_body = {
            "pool": {
                "protocol": protocol,
                "name": name,
                "subnet_id": subnet_id,
                "lb_method": lb_method
            }
        }
        body = json.dumps(post_body)
        uri = '%s/lb/pools' % (self.uri_prefix)
        resp, body = self.post(uri, headers=self.headers, body=body)
        body = json.loads(body)
        return resp, body

    def show_vip(self, uuid):
        uri = '%s/lb/vips/%s' % (self.uri_prefix, uuid)
        resp, body = self.get(uri, self.headers)
        body = json.loads(body)
        return resp, body

    def delete_vip(self, uuid):
        uri = '%s/lb/vips/%s' % (self.uri_prefix, uuid)
        resp, body = self.delete(uri, self.headers)
        return resp, body

    def delete_pool(self, uuid):
        uri = '%s/lb/pools/%s' % (self.uri_prefix, uuid)
        resp, body = self.delete(uri, self.headers)
        return resp, body

    def update_vip(self, vip_id, new_name):
        put_body = {
            "vip": {
                "name": new_name,
            }
        }
        body = json.dumps(put_body)
        uri = '%s/lb/vips/%s' % (self.uri_prefix, vip_id)
        resp, body = self.put(uri, body=body, headers=self.headers)
        body = json.loads(body)
        return resp, body

    def update_pool(self, pool_id, new_name):
        put_body = {
            "pool": {
                "name": new_name,
            }
        }
        body = json.dumps(put_body)
        uri = '%s/lb/pools/%s' % (self.uri_prefix, pool_id)
        resp, body = self.put(uri, body=body, headers=self.headers)
        body = json.loads(body)
        return resp, body

    def list_pools(self):
        uri = '%s/lb/pools' % (self.uri_prefix)
        resp, body = self.get(uri, self.headers)
        body = json.loads(body)
        return resp, body

    def show_pool(self, uuid):
        uri = '%s/lb/pools/%s' % (self.uri_prefix, uuid)
        resp, body = self.get(uri, self.headers)
        body = json.loads(body)
        return resp, body

    def list_members(self):
        uri = '%s/lb/members' % (self.uri_prefix)
        resp, body = self.get(uri, self.headers)
        body = json.loads(body)
        return resp, body

    def create_member(self, address, protocol_port, pool_id):
        post_body = {
            "member": {
                "protocol_port": protocol_port,
                "pool_id": pool_id,
                "address": address
            }
        }
        body = json.dumps(post_body)
        uri = '%s/lb/members' % (self.uri_prefix)
        resp, body = self.post(uri, headers=self.headers, body=body)
        body = json.loads(body)
        return resp, body

    def show_member(self, uuid):
        uri = '%s/lb/members/%s' % (self.uri_prefix, uuid)
        resp, body = self.get(uri, self.headers)
        body = json.loads(body)
        return resp, body

    def delete_member(self, uuid):
        uri = '%s/lb/members/%s' % (self.uri_prefix, uuid)
        resp, body = self.delete(uri, self.headers)
        return resp, body

    def update_member(self, admin_state_up, member_id):
        put_body = {
            "member": {
                "admin_state_up": admin_state_up
            }
        }
        body = json.dumps(put_body)
        uri = '%s/lb/members/%s' % (self.uri_prefix, member_id)
        resp, body = self.put(uri, body=body, headers=self.headers)
        body = json.loads(body)
        return resp, body

    def list_health_monitors(self):
        uri = '%s/lb/health_monitors' % (self.uri_prefix)
        resp, body = self.get(uri, self.headers)
        body = json.loads(body)
        return resp, body

    def create_health_monitor(self, delay, max_retries, Type, timeout):
        post_body = {
            "health_monitor": {
                "delay": delay,
                "max_retries": max_retries,
                "type": Type,
                "timeout": timeout
            }
        }
        body = json.dumps(post_body)
        uri = '%s/lb/health_monitors' % (self.uri_prefix)
        resp, body = self.post(uri, headers=self.headers, body=body)
        body = json.loads(body)
        return resp, body

    def show_health_monitor(self, uuid):
        uri = '%s/lb/health_monitors/%s' % (self.uri_prefix, uuid)
        resp, body = self.get(uri, self.headers)
        body = json.loads(body)
        return resp, body

    def delete_health_monitor(self, uuid):
        uri = '%s/lb/health_monitors/%s' % (self.uri_prefix, uuid)
        resp, body = self.delete(uri, self.headers)
        return resp, body

    def update_health_monitor(self, admin_state_up, uuid):
        put_body = {
            "health_monitor": {
                "admin_state_up": admin_state_up
            }
        }
        body = json.dumps(put_body)
        uri = '%s/lb/health_monitors/%s' % (self.uri_prefix, uuid)
        resp, body = self.put(uri, body=body, headers=self.headers)
        body = json.loads(body)
        return resp, body

    def associate_health_monitor_with_pool(self, health_monitor_id,
                                           pool_id):
        post_body = {
            "health_monitor": {
                "id": health_monitor_id,
            }
        }
        body = json.dumps(post_body)
        uri = '%s/lb/pools/%s/health_monitors' % (self.uri_prefix,
                                                  pool_id)
        resp, body = self.post(uri, headers=self.headers, body=body)
        body = json.loads(body)
        return resp, body

    def disassociate_health_monitor_with_pool(self, health_monitor_id,
                                              pool_id):
        uri = '%s/lb/pools/%s/health_monitors/%s' % (self.uri_prefix, pool_id,
                                                     health_monitor_id)
        resp, body = self.delete(uri, headers=self.headers)
        return resp, body

    def list_extensions(self):
        uri = '%s/extensions' % (self.uri_prefix)
        resp, body = self.get(uri, self.headers)
        body = json.loads(body)
        return resp, body

    def show_extension_details(self, ext_alias):
        uri = '%s/extensions/%s' % (self.uri_prefix, ext_alias)
        resp, body = self.get(uri, headers=self.headers)
        body = json.loads(body)
        return resp, body

    def list_vpn_services(self):
        uri = '%s/vpn/vpnservices' % (self.uri_prefix)
        resp, body = self.get(uri, self.headers)
        body = json.loads(body)
        return resp, body

    def create_vpn_service(self, subnet_id, router_id, **kwargs):
        post_body = {
            "vpnservice": {
                "subnet_id": subnet_id,
                "router_id": router_id
            }
        }
        for key, val in kwargs.items():
            post_body['vpnservice'][key] = val
        body = json.dumps(post_body)
        uri = '%s/vpn/vpnservices' % (self.uri_prefix)
        resp, body = self.post(uri, headers=self.headers, body=body)
        body = json.loads(body)
        return resp, body

    def show_vpn_service(self, uuid):
        uri = '%s/vpn/vpnservices/%s' % (self.uri_prefix, uuid)
        resp, body = self.get(uri, self.headers)
        body = json.loads(body)
        return resp, body

    def delete_vpn_service(self, uuid):
        uri = '%s/vpn/vpnservices/%s' % (self.uri_prefix, uuid)
        resp, body = self.delete(uri, self.headers)
        return resp, body

    def update_vpn_service(self, uuid, description):
        put_body = {
            "vpnservice": {
                "description": description
            }
        }
        body = json.dumps(put_body)
        uri = '%s/vpn/vpnservices/%s' % (self.uri_prefix, uuid)
        resp, body = self.put(uri, body=body, headers=self.headers)
        body = json.loads(body)
        return resp, body

    def list_router_interfaces(self, uuid):
        uri = '%s/ports?device_id=%s' % (self.uri_prefix, uuid)
        resp, body = self.get(uri, self.headers)
        body = json.loads(body)
        return resp, body
