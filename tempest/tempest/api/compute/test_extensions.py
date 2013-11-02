# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 OpenStack Foundation
# All Rights Reserved.
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


from tempest.api.compute import base
from tempest.test import attr


class ExtensionsTestJSON(base.BaseV2ComputeTest):
    _interface = 'json'

    @attr(type='gate')
    def test_list_extensions(self):
        # List of all extensions
        resp, extensions = self.extensions_client.list_extensions()
        self.assertIn("extensions", extensions)
        self.assertEqual(200, resp.status)


class ExtensionsTestXML(ExtensionsTestJSON):
    _interface = 'xml'
