# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013 IBM Corp
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

from lxml import etree

from tempest.common.rest_client import RestClientXML
from tempest.services.compute.xml.common import Document
from tempest.services.compute.xml.common import Element
from tempest.services.compute.xml.common import Text
from tempest.services.compute.xml.common import xml_to_json


class FixedIPsClientXML(RestClientXML):

    def __init__(self, config, username, password, auth_url, tenant_name=None):
        super(FixedIPsClientXML, self).__init__(config, username, password,
                                                auth_url, tenant_name)
        self.service = self.config.compute.catalog_type

    def _parse_fixed_ip_details(self, body):
        body = xml_to_json(etree.fromstring(body))
        return body

    def get_fixed_ip_details(self, fixed_ip):
        url = "os-fixed-ips/%s" % (fixed_ip)
        resp, body = self.get(url, self.headers)
        body = self._parse_resp(body)
        return resp, body

    def reserve_fixed_ip(self, ip, body):
        """This reserves and unreserves fixed ips."""
        url = "os-fixed-ips/%s/action" % (ip)
        # NOTE(maurosr): First converts the dict body to a json string then
        # accept any action key value here to permit tests to cover cases with
        # invalid actions raising badrequest.
        key, value = body.popitem()
        xml_body = Element(key)
        xml_body.append(Text(value))
        resp, body = self.post(url, str(Document(xml_body)), self.headers)
        return resp, body
