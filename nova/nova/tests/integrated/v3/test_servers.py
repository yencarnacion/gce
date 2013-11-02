# vim: tabstop=4 shiftwidth=4 softtabstop=4
# Copyright 2012 Nebula, Inc.
# Copyright 2013 IBM Corp.
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

from nova.tests.image import fake
from nova.tests.integrated.v3 import api_sample_base


class ServersSampleBase(api_sample_base.ApiSampleTestBaseV3):
    def _post_server(self):
        subs = {
            'image_id': fake.get_valid_image_id(),
            'host': self._get_host(),
            'glance_host': self._get_glance_host()
        }
        response = self._do_post('servers', 'server-post-req', subs)
        subs = self._get_regexes()
        return self._verify_response('server-post-resp', subs, response, 202)


class ServersSampleJsonTest(ServersSampleBase):
    sample_dir = 'servers'

    def test_servers_post(self):
        return self._post_server()

    def test_servers_get(self):
        uuid = self.test_servers_post()
        response = self._do_get('servers/%s' % uuid)
        subs = self._get_regexes()
        subs['hostid'] = '[a-f0-9]+'
        subs['id'] = uuid
        subs['hypervisor_hostname'] = r'[\w\.\-]+'
        subs['mac_addr'] = '(?:[a-f0-9]{2}:){5}[a-f0-9]{2}'
        self._verify_response('server-get-resp', subs, response, 200)

    def test_servers_list(self):
        uuid = self._post_server()
        response = self._do_get('servers')
        subs = self._get_regexes()
        subs['id'] = uuid
        self._verify_response('servers-list-resp', subs, response, 200)

    def test_servers_details(self):
        uuid = self._post_server()
        response = self._do_get('servers/detail')
        subs = self._get_regexes()
        subs['hostid'] = '[a-f0-9]+'
        subs['id'] = uuid
        subs['hypervisor_hostname'] = r'[\w\.\-]+'
        subs['mac_addr'] = '(?:[a-f0-9]{2}:){5}[a-f0-9]{2}'
        self._verify_response('servers-details-resp', subs, response, 200)


class ServersSampleXmlTest(ServersSampleJsonTest):
    ctype = 'xml'


class ServersSampleAllExtensionJsonTest(ServersSampleJsonTest):
    all_extensions = True


class ServersSampleAllExtensionXmlTest(ServersSampleXmlTest):
    all_extensions = True


class ServersActionsJsonTest(ServersSampleBase):
    sample_dir = 'servers'

    def _test_server_action(self, uuid, action,
                            subs={}, resp_tpl=None, code=202):
        subs.update({'action': action,
                     'glance_host': self._get_glance_host()})
        response = self._do_post('servers/%s/action' % uuid,
                                 'server-action-%s' % action.replace('_',
                                                                     '-'),
                                 subs)
        if resp_tpl:
            subs.update(self._get_regexes())
            self._verify_response(resp_tpl, subs, response, code)
        else:
            self.assertEqual(response.status, code)
            self.assertEqual(response.read(), "")

    def test_server_resize(self):
        self.flags(allow_resize_to_same_host=True)
        uuid = self._post_server()
        self._test_server_action(uuid, "resize",
                                 {"id": 2,
                                  "host": self._get_host()})
        return uuid

    def test_server_confirm_resize(self):
        uuid = self.test_server_resize()
        self._test_server_action(uuid, "confirm_resize")


class ServersActionsXmlTest(ServersActionsJsonTest):
    ctype = 'xml'
