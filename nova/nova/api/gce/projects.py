#    Copyright 2012 Cloudscaling Group, Inc
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

from nova import exception

from nova.api.gce import common as gce_common
from nova.api.gce import project_api
from nova.api.gce import wsgi as gce_wsgi


class Controller(gce_common.Controller):
    """GCE Projects controller"""

    def __init__(self, *args, **kwargs):
        super(Controller, self).__init__(*args, **kwargs)
        self._api = project_api.API()

    def _get_type(self):
        return "project"

    def basic(self, request, project, zone_id):
        result_dict = {
            "name": project["project"].name,
            "description": project["project"].description,
            "commonInstanceMetadata": {
                "kind": "compute#metadata",
                "items": [project["keypair"]]
            } if project["keypair"] else {}
        }

        return self._format_item(request,
                                 result_dict,
                                 project["project"].name,
                                 zone_id
                                 )

    def set_common_instance_metadata(self, req, body):
        context = req.environ['nova.context']

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

        return self._format_operation(req, "", "update")


def create_resource():
    return gce_wsgi.GCEResource(Controller())
