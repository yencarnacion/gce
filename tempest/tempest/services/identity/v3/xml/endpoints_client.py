# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright 2013 OpenStack Foundation
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
import urlparse

from lxml import etree

from tempest.common import http
from tempest.common.rest_client import RestClientXML
from tempest.services.compute.xml.common import Document
from tempest.services.compute.xml.common import Element
from tempest.services.compute.xml.common import xml_to_json

XMLNS = "http://docs.openstack.org/identity/api/v3"


class EndPointClientXML(RestClientXML):

    def __init__(self, config, username, password, auth_url, tenant_name=None):
        super(EndPointClientXML, self).__init__(config, username, password,
                                                auth_url, tenant_name)
        self.service = self.config.identity.catalog_type
        self.endpoint_url = 'adminURL'

    def _parse_array(self, node):
        array = []
        for child in node.getchildren():
            tag_list = child.tag.split('}', 1)
            if tag_list[1] == "endpoint":
                array.append(xml_to_json(child))
        return array

    def _parse_body(self, body):
        json = xml_to_json(body)
        return json

    def request(self, method, url, headers=None, body=None, wait=None):
        """Overriding the existing HTTP request in super class RestClient."""
        dscv = self.config.identity.disable_ssl_certificate_validation
        self.http_obj = http.ClosingHttp(
            disable_ssl_certificate_validation=dscv)
        self._set_auth()
        self.base_url = self.base_url.replace(
            urlparse.urlparse(self.base_url).path, "/v3")
        return super(EndPointClientXML, self).request(method, url,
                                                      headers=headers,
                                                      body=body)

    def list_endpoints(self):
        """Get the list of endpoints."""
        resp, body = self.get("endpoints", self.headers)
        body = self._parse_array(etree.fromstring(body))
        return resp, body

    def create_endpoint(self, service_id, interface, url, **kwargs):
        """Create endpoint."""
        region = kwargs.get('region', None)
        enabled = kwargs.get('enabled', None)
        create_endpoint = Element("endpoint",
                                  xmlns=XMLNS,
                                  service_id=service_id,
                                  interface=interface,
                                  url=url, region=region,
                                  enabled=enabled)
        resp, body = self.post('endpoints', str(Document(create_endpoint)),
                               self.headers)
        body = self._parse_body(etree.fromstring(body))
        return resp, body

    def update_endpoint(self, endpoint_id, service_id=None, interface=None,
                        url=None, region=None, enabled=None):
        """Updates an endpoint with given parameters."""
        doc = Document()
        endpoint = Element("endpoint")
        doc.append(endpoint)

        if service_id:
            endpoint.add_attr("service_id", service_id)
        if interface:
            endpoint.add_attr("interface", interface)
        if url:
            endpoint.add_attr("url", url)
        if region:
            endpoint.add_attr("region", region)
        if enabled is not None:
            endpoint.add_attr("enabled", enabled)
        resp, body = self.patch('endpoints/%s' % str(endpoint_id),
                                str(doc), self.headers)
        body = self._parse_body(etree.fromstring(body))
        return resp, body

    def delete_endpoint(self, endpoint_id):
        """Delete endpoint."""
        resp_header, resp_body = self.delete('endpoints/%s' % endpoint_id)
        return resp_header, resp_body
