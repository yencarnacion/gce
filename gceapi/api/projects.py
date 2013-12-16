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

import webob

from gceapi import exception

from gceapi.api import common as gce_common
from gceapi.api import project_api
from gceapi.api import wsgi as gce_wsgi


class Controller(gce_common.Controller):
    """GCE Projects controller"""

    def __init__(self, *args, **kwargs):
        super(Controller, self).__init__(*args, **kwargs)
        self._api = project_api.API()
        self._collection_name = None

    def _get_type(self):
        return "project"

    def format_item(self, request, project, scope):
        desc = project["project"].description
        result_dict = {
            "name": project["project"].name,
            "description": desc if desc else "",
            "commonInstanceMetadata": {
                "kind": "compute#metadata",
                "items": [project["keypair"]]
            } if project["keypair"] else {
                "kind": "compute#metadata",
            },
            "quotas": []
        }

        return self._format_item(request, result_dict, scope)

    def set_common_instance_metadata(self, req, body):
        context = self._get_context(req)

        try:
            self._api.set_common_instance_metadata(
                context, body.get("items", []))
        except exception.KeypairLimitExceeded:
            msg = _("Quota exceeded, too many key pairs.")
            raise webob.exc.HTTPRequestEntityTooLarge(
                        explanation=msg,
                        headers={'Retry-After': 0})
        except exception.InvalidKeypair:
            msg = _("Keypair data is invalid")
            raise webob.exc.HTTPBadRequest(explanation=msg)
        except exception.KeyPairExists:
            msg = _("Key pair already exists.")
            raise webob.exc.HTTPConflict(explanation=msg)

        return self._format_operation(req, "", "setMetadata", None)


def create_resource():
    return gce_wsgi.GCEResource(Controller())
