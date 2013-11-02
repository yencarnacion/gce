# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 IBM Corp.
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

# See: http://wiki.openstack.org/Nova/CoverageExtension for more information
# and usage explanation for this API extension

import os
import re
import socket
import sys
import telnetlib
import tempfile

from oslo.config import cfg
from webob import exc

from nova.api.openstack import extensions
from nova import baserpc
from nova import db
from nova.openstack.common.gettextutils import _
from nova.openstack.common import log as logging
from nova.openstack.common.rpc import common as rpc_common


LOG = logging.getLogger(__name__)
authorize = extensions.extension_authorizer('compute', 'coverage_ext')
CONF = cfg.CONF


class CoverageController(object):
    """The Coverage report API controller for the OpenStack API."""
    def __init__(self):
        self.data_path = None
        self.services = []
        self.combine = False
        self._cover_inst = None
        self.host = CONF.host
        super(CoverageController, self).__init__()

    @property
    def coverInst(self):
        if not self._cover_inst:
            try:
                import coverage
                if self.data_path is None:
                    self.data_path = tempfile.mkdtemp(prefix='nova-coverage_')
                data_out = os.path.join(self.data_path, '.nova-coverage.api')
                self._cover_inst = coverage.coverage(data_file=data_out)
            except ImportError:
                pass
        return self._cover_inst

    def _find_services(self, req):
        """Returns a list of services."""
        context = req.environ['nova.context']
        services = db.service_get_all(context)
        hosts = []
        for serv in services:
            hosts.append({"service": serv["topic"], "host": serv["host"]})
        return hosts

    def _find_ports(self, req, hosts):
        """Return a list of backdoor ports for all services in the list."""
        context = req.environ['nova.context']
        ports = []
        #TODO(mtreinish): Figure out how to bind the backdoor socket to 0.0.0.0
        # Currently this will only work if the host is resolved as loopback on
        # the same host as api-server
        for host in hosts:
            base = baserpc.BaseAPI(host['service'])
            _host = host
            try:
                _host['port'] = base.get_backdoor_port(context, host['host'])
            except rpc_common.UnsupportedRpcVersion:
                _host['port'] = None

            #NOTE(mtreinish): if the port is None then it wasn't set in
            # the configuration file for this service. However, that
            # doesn't necessarily mean that we don't have backdoor ports
            # for all the services. So, skip the telnet connection for
            # this service.
            if _host['port']:
                ports.append(_host)
            else:
                LOG.warning(_("Can't connect to service: %s, no port"
                              "specified\n"), host['service'])
        return ports

    def _start_coverage_telnet(self, tn, service):
        data_file = os.path.join(self.data_path,
                                '.nova-coverage.%s' % str(service))
        tn.write('from __future__ import print_function\n')
        tn.write('import sys\n')
        tn.write('from coverage import coverage\n')
        tn.write("coverInst = coverage(data_file='%s') "
                 "if 'coverInst' not in locals() "
                 "else coverInst\n" % data_file)
        tn.write('coverInst.skipModules = sys.modules.keys()\n')
        tn.write("coverInst.start()\n")
        tn.write("print('finished')\n")
        tn.expect([re.compile('finished')])

    def _start_coverage(self, req, body):
        '''Begin recording coverage information.'''
        LOG.debug(_("Coverage begin"))
        body = body['start']
        self.combine = False
        if 'combine' in body.keys():
            self.combine = bool(body['combine'])
        self.coverInst.skipModules = sys.modules.keys()
        self.coverInst.start()
        hosts = self._find_services(req)
        ports = self._find_ports(req, hosts)
        self.services = []
        for service in ports:
            try:
                service['telnet'] = telnetlib.Telnet(service['host'],
                                                     service['port'])
            # NOTE(mtreinish): Fallback to try connecting to lo if
            # ECONNREFUSED is raised. If using the hostname that is returned
            # for the service from the service_get_all() DB query raises
            # ECONNREFUSED it most likely means that the hostname in the DB
            # doesn't resolve to 127.0.0.1. Currently backdoors only open on
            # loopback so this is for covering the common single host use case
            except socket.error as e:
                exc_info = sys.exc_info()
                if 'ECONNREFUSED' in e and service['host'] == self.host:
                        service['telnet'] = telnetlib.Telnet('127.0.0.1',
                                                             service['port'])
                else:
                    raise exc_info[0], exc_info[1], exc_info[2]
            self.services.append(service)
            self._start_coverage_telnet(service['telnet'], service['service'])

    def _stop_coverage_telnet(self, tn):
        tn.write("coverInst.stop()\n")
        tn.write("coverInst.save()\n")
        tn.write("print('finished')\n")
        tn.expect([re.compile('finished')])

    def _check_coverage(self):
        try:
            self.coverInst.stop()
            self.coverInst.save()
        except AssertionError:
            return True
        return False

    def _stop_coverage(self, req):
        for service in self.services:
            self._stop_coverage_telnet(service['telnet'])
        if self._check_coverage():
            msg = _("Coverage not running")
            raise exc.HTTPNotFound(explanation=msg)
        return {'path': self.data_path}

    def _report_coverage_telnet(self, tn, path, xml=False):
        if xml:
            execute = str("coverInst.xml_report(outfile='%s')\n" % path)
            tn.write(execute)
            tn.write("print('finished')\n")
            tn.expect([re.compile('finished')])
        else:
            execute = str("output = open('%s', 'w')\n" % path)
            tn.write(execute)
            tn.write("coverInst.report(file=output)\n")
            tn.write("output.close()\n")
            tn.write("print('finished')\n")
            tn.expect([re.compile('finished')])
        tn.close()

    def _report_coverage(self, req, body):
        self._stop_coverage(req)
        xml = False
        html = False
        path = None

        body = body['report']
        if 'file' in body.keys():
            path = body['file']
            if path != os.path.basename(path):
                msg = _("Invalid path")
                raise exc.HTTPBadRequest(explanation=msg)
            path = os.path.join(self.data_path, path)
        else:
            msg = _("No path given for report file")
            raise exc.HTTPBadRequest(explanation=msg)

        if 'xml' in body.keys():
            xml = body['xml']
        elif 'html' in body.keys():
            if not self.combine:
                msg = _("You can't use html reports without combining")
                raise exc.HTTPBadRequest(explanation=msg)
            html = body['html']

        if self.combine:
            data_out = os.path.join(self.data_path, '.nova-coverage')
            import coverage
            coverInst = coverage.coverage(data_file=data_out)
            coverInst.combine()
            if xml:
                coverInst.xml_report(outfile=path)
            elif html:
                if os.path.isdir(path):
                    msg = _("Directory conflict: %s already exists") % path
                    raise exc.HTTPBadRequest(explanation=msg)
                coverInst.html_report(directory=path)
            else:
                output = open(path, 'w')
                coverInst.report(file=output)
                output.close()
            for service in self.services:
                service['telnet'].close()
        else:
            if xml:
                apipath = path + '.api'
                self.coverInst.xml_report(outfile=apipath)
                for service in self.services:
                    self._report_coverage_telnet(service['telnet'],
                                              path + '.%s'
                                              % service['service'],
                                              xml=True)
            else:
                output = open(path + '.api', 'w')
                self.coverInst.report(file=output)
                for service in self.services:
                    self._report_coverage_telnet(service['telnet'],
                                            path + '.%s' % service['service'])
                output.close()
        return {'path': path}

    def _reset_coverage_telnet(self, tn):
        tn.write("coverInst.erase()\n")
        tn.write("print('finished')\n")
        tn.expect([re.compile('finished')])

    def _reset_coverage(self, req):
        # Reopen telnet connections if they are closed.
        for service in self.services:
            if not service['telnet'].get_socket():
                service['telnet'].open(service['host'], service['port'])

        # Stop coverage if it is started.
        try:
            self._stop_coverage(req)
        except exc.HTTPNotFound:
            pass

        for service in self.services:
            self._reset_coverage_telnet(service['telnet'])
            service['telnet'].close()
        self.coverInst.erase()

    def action(self, req, body):
        _actions = {
                'start': self._start_coverage,
                'stop': self._stop_coverage,
                'report': self._report_coverage,
                'reset': self._reset_coverage,
        }
        authorize(req.environ['nova.context'])
        if not self.coverInst:
            msg = _("Python coverage module is not installed.")
            raise exc.HTTPServiceUnavailable(explanation=msg)
        for action, data in body.iteritems():
            if action == 'stop' or action == 'reset':
                return _actions[action](req)
            elif action == 'report' or action == 'start':
                return _actions[action](req, body)
            else:
                msg = _("Coverage doesn't have %s action") % action
                raise exc.HTTPBadRequest(explanation=msg)
        raise exc.HTTPBadRequest(explanation=_("Invalid request body"))


class Coverage_ext(extensions.ExtensionDescriptor):
    """Enable Nova Coverage."""

    name = "Coverage"
    alias = "os-coverage"
    namespace = ("http://docs.openstack.org/compute/ext/"
                  "coverage/api/v2")
    updated = "2012-10-15T00:00:00+00:00"

    def get_resources(self):
        resources = []
        res = extensions.ResourceExtension('os-coverage',
                                        controller=CoverageController(),
                                        collection_actions={"action": "POST"})
        resources.append(res)
        return resources
