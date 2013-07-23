# -*- coding: utf-8 -*-

# Licensed under the MIT license
# http://opensource.org/licenses/mit-license.php

# Copyright 2009 - Frank Scholz <coherence@beebits.net>

import os
import tempfile

from twisted.internet import defer
from twisted.internet import protocol

from twisted.python.filepath import FilePath

try:
    from twisted.mail import smtp

    from twisted.names import client as namesclient
    from twisted.names import dns

    import StringIO

    EMAIL_RECIPIENT = 'upnp.fingerprint@googlemail.com'

    class SMTPClient(smtp.ESMTPClient):

        """ build an email message and send it to our googlemail account
        """

        def __init__(self, mail_from, mail_to, mail_subject, mail_file, *args, **kwargs):
            smtp.ESMTPClient.__init__(self, *args, **kwargs)
            self.mailFrom = mail_from
            self.mailTo = mail_to
            self.mailSubject = mail_subject
            self.mail_file =  mail_file
            self.mail_from =  mail_from

        def getMailFrom(self):
            result = self.mailFrom
            self.mailFrom = None
            return result

        def getMailTo(self):
            return [self.mailTo]

        def getMailData(self):
            from email.mime.application import MIMEApplication
            from email.mime.multipart import MIMEMultipart

            msg = MIMEMultipart()
            msg['Subject'] = self.mailSubject
            msg['From'] = self.mail_from
            msg['To'] = self.mailTo
            fp = open(self.mail_file, 'rb')
            tar = MIMEApplication(fp.read(),'x-tar')
            fp.close()
            tar.add_header('Content-Disposition', 'attachment', filename=os.path.basename(self.mail_file))
            msg.attach(tar)
            return StringIO.StringIO(msg.as_string())

        def sentMail(self, code, resp, numOk, addresses, log):
            print 'Sent', numOk, 'messages'

    class SMTPClientFactory(protocol.ClientFactory):
        protocol = SMTPClient

        def __init__(self, mail_from, mail_to, mail_subject, mail_file, *args, **kwargs):
            self.mail_from = mail_from
            self.mail_to = mail_to
            self.mail_subject = mail_subject
            self.mail_file = mail_file

        def buildProtocol(self, addr):
            return self.protocol(self.mail_from, self.mail_to,
                                 self.mail_subject, self.mail_file,
                                 secret=None, identity='localhost')

    haz_smtp = True
except ImportError:
    haz_smtp = False

from coherence.upnp.core.utils import downloadPage

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

class Extract(object):

    def __init__(self,device):
        self.device = device
        self.window = Gtk.Dialog(title="Extracting XMl descriptions",
                            parent=None,flags=0,buttons=None)
        self.window.connect("delete_event", self.hide)
        label = Gtk.Label("Extracting XMl device and service descriptions\nfrom %s @ %s" % (device.friendly_name, device.host))
        self.window.vbox.pack_start(label, True, True, 10)
        tar_button = Gtk.CheckButton("tar.gz them")
        tar_button.connect("toggled", self._toggle_tar)
        self.window.vbox.pack_start(tar_button, True, True, 5)

        if haz_smtp == True:
            self.email_button = Gtk.CheckButton("email them to Coherence HQ (%s)" % EMAIL_RECIPIENT)
            self.email_button.set_sensitive(False)
            self.window.vbox.pack_start(self.email_button, True, True, 5)

        align = Gtk.Alignment.new(0.5, 0.5, 0.9, 0)
        self.window.vbox.pack_start(align, False, False, 5)
        self.progressbar = Gtk.ProgressBar()
        align.add(self.progressbar)

        button = Gtk.Button(stock=Gtk.STOCK_CANCEL)
        self.window.action_area.pack_start(button, True, True, 5)
        button.connect("clicked", lambda w: self.window.destroy())
        button = Gtk.Button(stock=Gtk.STOCK_OK)
        self.window.action_area.pack_start(button, True, True, 5)
        button.connect("clicked", lambda w: self.extract(w,tar_button.get_active()))
        self.window.show_all()

    def _toggle_tar(self,w):
        if haz_smtp:
            self.email_button.set_sensitive(w.get_active())

    def hide(self,w,e):
        w.hide()
        return True

    def extract(self,w,make_tar):
        print w, make_tar
        self.progressbar.pulse()
        try:
            l = []
            path = FilePath(tempfile.gettempdir())

            def device_extract(workdevice, workpath):
                tmp_dir = workpath.get_child()(workdevice.get_uuid())
                if tmp_dir.exists():
                    tmp_dir.remove()
                tmp_dir.createDirectory()
                target = tmp_dir.get_child()('device-description.xml')
                print "d",target,target.path
                d = downloadPage(workdevice.get_location(),target.path)
                l.append(d)

                for service in workdevice.services:
                    target = tmp_dir.get_child()('%s-description.xml'%service.service_type.split(':',3)[3])
                    print "s",target,target.path
                    d = downloadPage(service.get_scpd_url(),target.path)
                    l.append(d)

                for ed in workdevice.devices:
                    device_extract(ed, tmp_dir)

            def finished(result):
                uuid = self.device.get_uuid()
                print "extraction of device %s finished" % uuid
                print "files have been saved to %s" % os.path.join(tempfile.gettempdir(),uuid)
                if make_tar == True:
                    tgz_file = self.create_tgz(path.get_child()(uuid))
                    if haz_smtp == True and self.email_button.get_active() == True:
                        self.send_email(tgz_file)
                    path.get_child()(uuid).remove()
                self.progressbar.set_fraction(0.0)
                self.window.hide()

            device_extract(self.device,path)

            dl = defer.DeferredList(l)
            dl.addCallback(finished)
        except Exception, msg:
            print "problem creating download directory: %r (%s)" % (Exception,msg)
            self.progressbar.set_fraction(0.0)

    def create_tgz(self,path):
        print "create_tgz", path, path.basename()
        cwd = os.getcwd()
        os.chdir(path.dirname())
        import tarfile
        tgz_file = os.path.join(tempfile.gettempdir(),path.basename()+'.tgz')
        tar = tarfile.open(tgz_file, "w:gz")
        for file in path.children():
            tar.add(os.path.join(path.basename(),file.basename()))
        tar.close()
        os.chdir(cwd)
        return tgz_file

    def send_email(self, file):

        def got_mx(result):
            mx_list = result[0]
            mx_list.sort(lambda x, y: cmp(x.payload.preference, y.payload.preference))
            if len(mx_list) > 0:
                import posix, pwd
                import socket
                from twisted.internet import reactor
                reactor.connectTCP(str(mx_list[0].payload.name), 25,
                    SMTPClientFactory('@'.join((pwd.getpwuid(posix.getuid())[0],socket.gethostname())), EMAIL_RECIPIENT, 'xml-files', file))

        mx = namesclient.lookupMailExchange('googlemail.com')
        mx.addCallback(got_mx)
