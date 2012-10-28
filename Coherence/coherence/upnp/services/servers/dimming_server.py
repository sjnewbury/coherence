"""
"""
# Licensed under the MIT license
# http://opensource.org/licenses/mit-license.php
# Copyright 2008, Frank Scholz <coherence@beebits.net>
# Dimming service


from twisted.web import resource
from coherence.upnp.core.soap_service import UPnPPublisher
from coherence.upnp.core import service
from coherence import log


class DimmingControl(service.ServiceControl, UPnPPublisher):

    def __init__(self, server):
        self.service = server
        self.variables = server.get_variables()
        self.actions = server.get_actions()
        #print "dimming_server service:{0:}".format(self.service)
        #print "dimming_server variables:{0:}".format(self.variables)
        #print "dimming_server actions:{0:}\n".format(self.actions)
        pass


class DimmingServer(service.ServiceServer, resource.Resource, log.Loggable):
    logCategory = 'dimming_server'

    def __init__(self, device, backend = None):
        self.device = device
        if backend == None:
            backend = self.device.backend
        resource.Resource.__init__(self)
        service.ServiceServer.__init__(self, 'Dimming', self.device.version, backend)
        self.control = DimmingControl(self)
        self.putChild(self.scpd_url, service.scpdXML(self, self.control))
        self.putChild(self.control_url, self.control)
