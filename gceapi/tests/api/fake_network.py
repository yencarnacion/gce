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
