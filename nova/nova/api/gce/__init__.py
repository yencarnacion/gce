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


import routes
import webob
import webob.dec
import webob.exc
from oslo.config import cfg

from nova.api.gce import disks
from nova.api.gce import images
from nova.api.gce import instances
from nova.api.gce import machine_types
from nova.api.gce import kernels
from nova.api.gce import zones
from nova.api.gce import networks
from nova.api.gce import projects
from nova.api.gce import firewalls

from nova.api import openstack as openstack_api
from nova import config
from nova import context
from nova import wsgi

from nova.openstack.common import log as logging

gce_opts = [
        cfg.StrOpt('keystone_gce_url',
            default='http://127.0.0.1:5000/v2.0',
            help='Keystone URL'),
        cfg.StrOpt('gce_host',
            default='$my_ip',
            help='the ip of the gce api server'),
        cfg.StrOpt('gce_dmz_host',
            default='$my_ip',
            help='the internal ip of the gce api server'),
        cfg.IntOpt('gce_port',
            default=8777,
            help='the port of the gce api server'),
        cfg.StrOpt('gce_scheme',
            default='http',
            help='the protocol to use when connecting to the gce api '
                 'server (http, https)'),
        cfg.StrOpt('gce_path',
            default='/compute/v1beta15/projects',
            help='the path prefix used to call the gce api server'),
        ]

CONF = cfg.CONF
CONF.register_opts(gce_opts)

LOG = logging.getLogger(__name__)


class StubAuth(wsgi.Middleware):

    @webob.dec.wsgify(RequestClass=wsgi.Request)
    def __call__(self, req):
        ctx = context.get_admin_context()
        ctx.project_id = "demo"

        req.environ['nova.context'] = ctx
        return self.application


class APIRouter(wsgi.Router):
    """
    Routes requests on the GCE API to the appropriate controller
    and method.
    """

    @classmethod
    def factory(cls, global_config, **local_config):
        """Simple paste factory, :class:`nova.wsgi.Router` doesn't have one."""

        return cls()

    def __init__(self):
        mapper = openstack_api.ProjectMapper()
        self.resources = {}
        self._setup_routes(mapper)
        super(APIRouter, self).__init__(mapper)

    def _setup_routes(self, mapper):
        mapper.redirect("", "/")

        self.resources['firewalls'] = firewalls.create_resource()
        self.resources['disks'] = disks.create_resource()
        self.resources['machineTypes'] = machine_types.create_resource()
        self.resources['kernels'] = kernels.create_resource()
        self.resources['instances'] = instances.create_resource()
        self.resources['images'] = images.create_resource()
        self.resources['instances'] = instances.create_resource()
        self.resources['zones'] = zones.create_resource()
        self.resources['networks'] = networks.create_resource()
        self.resources['instances'] = instances.create_resource()
        self.resources['projects'] = projects.create_resource()

        mapper.resource("disks", "zones/{zone_id}/disks",
                controller=self.resources['disks'])
        mapper.connect("/{project_id}/aggregated/disks",
                controller=self.resources['disks'],
                action="aggregated_list",
                conditions={"method": ["GET"]})

        mapper.resource("machineTypes", "zones/{zone_id}/machineTypes",
                controller=self.resources['machineTypes'])
        mapper.connect("/{project_id}/aggregated/machineTypes",
                controller=self.resources['machineTypes'],
                action="aggregated_list",
                conditions={"method": ["GET"]})

        mapper.resource("instances", "zones/{zone_id}/instances",
                controller=self.resources['instances'])
        mapper.connect("/{project_id}/aggregated/instances",
                controller=self.resources['instances'],
                action="aggregated_list",
                conditions={"method": ["GET"]})
        mapper.connect("/{project_id}/zones/{zone_id}/instances/{id}/"
                       "addAccessConfig",
                controller=self.resources['instances'],
                action="add_access_config",
                conditions={"method": ["POST"]})
        mapper.connect("/{project_id}/zones/{zone_id}/instances/{id}/"
                       "deleteAccessConfig",
                controller=self.resources['instances'],
                action="delete_access_config",
                conditions={"method": ["POST"]})
        mapper.connect("/{project_id}/zones/{zone_id}/instances/{id}/reset",
                controller=self.resources['instances'],
                action="reset_instance",
                conditions={"method": ["POST"]})

        mapper.resource("images", "global/images",
                controller=self.resources['images'])
        mapper.resource("zones", "zones",
                controller=self.resources['zones'])
        mapper.resource("networks", "global/networks",
                controller=self.resources["networks"])
        mapper.resource("firewalls", "global/firewalls",
                controller=self.resources["firewalls"])
        mapper.resource("kernels", "global/kernels",
                controller=self.resources['kernels'])

        mapper.connect("/{project_id}", controller=self.resources['projects'],
                action="show", conditions={"method": ["GET"]})
        mapper.connect("/{project_id}/setCommonInstanceMetadata",
                controller=self.resources['projects'],
                action="set_common_instance_metadata",
                conditions={"method": ["POST"]})
