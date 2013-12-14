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


FAKE_NETWORKS = {'networks':
                 [
                  {u'status': u'ACTIVE',
                   u'subnets': [u'cd84a13b-6246-424f-9dd2-04c324ed4da0'],
                   u'name': u'private',
                   u'provider:physical_network': None,
                   u'admin_state_up': True,
                   u'tenant_id': u'4a5cc7d8893544a9babb3b890227d75e',
                   u'provider:network_type': u'local',
                   u'router:external': False,
                   u'shared': False,
                   u'id': u'734b9c83-3a8b-4350-8fbf-d40f571ee163',
                   u'provider:segmentation_id': None},
                  {u'status': u'ACTIVE',
                   u'subnets': [u'7a2800b8-0e66-4271-b26c-6af01dcba66f'],
                   u'name': u'public',
                   u'provider:physical_network': None,
                   u'admin_state_up': True,
                   u'tenant_id': u'4a5cc7d8893544a9babb3b890227d75e',
                   u'provider:network_type': u'local',
                   u'router:external': True,
                   u'shared': False,
                   u'id': u'7aa33661-33ba-4291-a2c7-44bfd59884c1',
                   u'provider:segmentation_id': None},
                  {u'status': u'ACTIVE',
                   u'subnets': [],
                   u'name': u'public',
                   u'provider:physical_network': None,
                   u'admin_state_up': True,
                   u'tenant_id': u'ae7d3f067c3c4243bb0c6ea0fa8fb6e4',
                   u'provider:network_type': u'local',
                   u'router:external': True,
                   u'shared': False,
                   u'id': u'439fa4f9-cdd7-4ee2-b3cf-5e764cf644af',
                   u'provider:segmentation_id': None},
                  ]}

FAKE_SUBNETS = [
                {u'subnet':
                 {u'name': u'',
                  u'enable_dhcp': True,
                  u'network_id': u'734b9c83-3a8b-4350-8fbf-d40f571ee163',
                  u'tenant_id': u'4a5cc7d8893544a9babb3b890227d75e',
                  u'dns_nameservers': [],
                  u'allocation_pools': [
                                        {u'start': u'10.0.0.2',
                                         u'end': u'10.0.0.254'}
                                       ],
                  u'host_routes': [],
                  u'ip_version': 4,
                  u'gateway_ip': u'10.0.0.1',
                  u'cidr': u'10.0.0.0/24',
                  u'id': u'cd84a13b-6246-424f-9dd2-04c324ed4da0'}
                },
                {u'subnet':
                 {u'name': u'',
                  u'enable_dhcp': False,
                  u'network_id': u'7aa33661-33ba-4291-a2c7-44bfd59884c1',
                  u'tenant_id': u'ae7d3f067c3c4243bb0c6ea0fa8fb6e4',
                  u'dns_nameservers': [],
                  u'allocation_pools': [
                                        {u'start': u'172.24.4.226',
                                         u'end': u'172.24.4.238'}
                                        ],
                  u'host_routes': [],
                  u'ip_version': 4,
                  u'gateway_ip': u'172.24.4.225',
                  u'cidr': u'172.24.4.224/28',
                  u'id': u'7a2800b8-0e66-4271-b26c-6af01dcba66f'}
                 }
                ]


class FakeQuantumClient(object):

    def list_networks(self, **search_opts):
        name_filter = search_opts.get("name")
        if name_filter is not None:
            for network in FAKE_NETWORKS["networks"]:
                if network["name"] == name_filter:
                    return {"networks": [network]}
            return {"networks": []}
        else:
            return FAKE_NETWORKS

    def show_subnet(self, subnet_id):
        for subnet in FAKE_SUBNETS:
            if subnet["subnet"]["id"] == subnet_id:
                return subnet
        return None

    def create_network(self, body):
        return {u'network':
                {u'status': u'ACTIVE',
                 u'subnets': [],
                 u'name': body["network"]["name"],
                 u'provider:physical_network': None,
                 u'admin_state_up': True,
                 u'tenant_id': u'4a5cc7d8893544a9babb3b890227d75e',
                 u'provider:network_type': u'local',
                 u'router:external': False,
                 u'shared': False,
                 u'id': u'f1b1bc03-9955-4fd8-bdf9-d2ec7d2777e7',
                 u'provider:segmentation_id': None}}

    def create_subnet(self, body):
        return {u'subnet':
                {u'name': u'',
                 u'enable_dhcp': True,
                 u'network_id': u'f1b1bc03-9955-4fd8-bdf9-d2ec7d2777e7',
                 u'tenant_id': u'4a5cc7d8893544a9babb3b890227d75e',
                 u'dns_nameservers': [],
                 u'allocation_pools': [
                                       {u'start': u'10.100.0.2',
                                        u'end': u'10.100.0.254'}
                                       ],
                 u'host_routes': [],
                 u'ip_version': 4,
                 u'gateway_ip': u'10.100.0.1',
                 u'cidr': u'10.100.0.0/24',
                 u'id': u'9d550616-b294-4897-9eb4-7f998aa7a74e'}}

    def delete_network(self, network_id):
        pass

    def list_routers(self, retrieve_all=True, **_params):
        return {"routers": []}

    def list_ports(self, *args, **kwargs):
        return {"ports": []}

    def list_floatingips(self):
        return {"floatingips": [{
            u"fixed_ip_address": u"192.168.138.196",
            u"floating_ip_address": u"172.24.4.227",
            u"floating_network_id": u"7aa33661-33ba-4291-a2c7-44bfd59884c1",
            u"id": u"81c45d28-3699-4116-bacd-7488996c5293",
            u"port_id": u"8984b23b-f945-4b1e-8eb0-7e735285c0cc",
            u"router_id": u"59e96d7b-749d-433e-b592-a55ba94b935e",
            u"tenant_id": u"4a5cc7d8893544a9babb3b890227d75e"}]}

    def create_floatingip(self, body=None):
        return {"floatingip": {"floating_ip_address": "10.20.30.40"}}

    def delete_floatingip(self, floatingip):
        pass


class FakeNetworkAPI(object):

    def get_floating_ips_by_project(self, context):
        return [{
            'fixed_ip_id': None,
            'fixed_ip': {'address': None},
            'instance': None,
            'address': u'192.168.138.196',
            'project_id': u'bf907fe9f01342949e9693ca47e7d856',
            'id': u'f4fafe68-77f2-410b-9f89-8bfb6ffdb4f1',
            'pool': u'public'
        }]

    def associate_floating_ip(self, context, instance,
                              floating_address, fixed_address):
        pass

    def get_floating_ip_by_address(self, context, address):
        return {
            'fixed_ip_id': u'f378990c-1eee-4305-8745-9090d45c4361',
            'fixed_ip': {'address': u'10.0.1.3'},
            'instance': {'uuid': u'd6957005-3ce7-4727-91d2-ae37fe5a199a'},
            'address': u'192.168.138.196',
            'project_id': u'bf907fe9f01342949e9693ca47e7d856',
            'id': u'f4fafe68-77f2-410b-9f89-8bfb6ffdb4f1',
            'pool': u'public'
        }

    def disassociate_floating_ip(self, context, instance, address):
        pass


def fake_quantum_get_client(context):
    return FakeQuantumClient()
