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

from nova import context
from nova.api.openstack import wsgi as os_wsgi


class HTTPRequest(os_wsgi.Request):

    @classmethod
    def blank(cls, url, has_body=False, *args, **kwargs):
        kwargs['base_url'] = 'http://localhost/compute/v1beta15/projects'
        use_admin_context = kwargs.pop('use_admin_context', False)
        if has_body:
            kwargs.setdefault("content_type", "application/json")
        out = os_wsgi.Request.blank(url, *args, **kwargs)
        user_id = 'c2bc8099-8861-46ab-a416-99f06bb89198'
        user_name = 'fake_user'
        project_id = '4a5cc7d8893544a9babb3b890227d75e'
        project_name = 'fake_project'
        fake_context = context.RequestContext(user_id,
                                              project_id,
                                              user_name=user_name,
                                              project_name=project_name,
                                              is_admin=True)
        out.environ['nova.context'] = fake_context
        return out
