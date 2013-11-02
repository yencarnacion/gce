# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013 NEC Corporation
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

import urllib

from lxml import etree

from tempest.common.rest_client import RestClientXML
from tempest.services.compute.xml.common import xml_to_json


class TenantUsagesClientXML(RestClientXML):

    def __init__(self, config, username, password, auth_url, tenant_name=None):
        super(TenantUsagesClientXML, self).__init__(config, username,
                                                    password, auth_url,
                                                    tenant_name)
        self.service = self.config.compute.catalog_type

    def _parse_array(self, node):
        json = xml_to_json(node)
        return json

    def list_tenant_usages(self, params=None):
        url = 'os-simple-tenant-usage'
        if params:
            url += '?%s' % urllib.urlencode(params)

        resp, body = self.get(url, self.headers)
        tenant_usage = self._parse_array(etree.fromstring(body))
        return resp, tenant_usage['tenant_usage']

    def get_tenant_usage(self, tenant_id, params=None):
        url = 'os-simple-tenant-usage/%s' % tenant_id
        if params:
            url += '?%s' % urllib.urlencode(params)

        resp, body = self.get(url, self.headers)
        tenant_usage = self._parse_array(etree.fromstring(body))
        return resp, tenant_usage
