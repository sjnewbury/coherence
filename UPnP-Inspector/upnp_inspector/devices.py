# -*- coding: utf-8 -*-

# Licensed under the MIT license
# http://opensource.org/licenses/mit-license.php

# Copyright 2009 - Frank Scholz <coherence@beebits.net>

import os.path
import time

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

from twisted.internet import reactor

from coherence.base import Coherence
from coherence.upnp.core.utils import means_true

from coherence import log

# gtk store defines
TYPE_COLUMN = 0
NAME_COLUMN = 1
UDN_COLUMN = 2
ICON_COLUMN = 3
OBJECT_COLUMN = 4

DEVICE = 0
SERVICE = 1
VARIABLE = 2
ACTION = 3
ARGUMENT = 4

from pkg_resources import resource_filename

class DevicesWidget(log.Loggable):
    logCategory = 'inspector'

    def __init__(self, coherence):
        self.coherence = coherence

        self.cb_item_dbl_click = None
        self.cb_item_left_click = None
        self.cb_item_right_click = None
        self.cb_resource_chooser = None

        self.build_ui()
        self.init_controlpoint()

    def build_ui(self):
        self.window = Gtk.ScrolledWindow()
        self.window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)

        self.icons = {}

        icon = resource_filename(__name__, os.path.join('icons','upnp-device.png'))
        self.icons['device'] = GdkPixbuf.Pixbuf.new_from_file(icon)
        icon = resource_filename(__name__, os.path.join('icons','network-server.png'))
        self.icons['mediaserver'] = GdkPixbuf.Pixbuf.new_from_file(icon)
        icon = resource_filename(__name__, os.path.join('icons','media-renderer.png'))
        self.icons['mediarenderer'] = GdkPixbuf.Pixbuf.new_from_file(icon)
        icon = resource_filename(__name__, os.path.join('icons','network-light.png'))
        self.icons['binarylight'] = GdkPixbuf.Pixbuf.new_from_file(icon)
        self.icons['dimmablelight'] = GdkPixbuf.Pixbuf.new_from_file(icon)
        icon = resource_filename(__name__, os.path.join('icons','camera-web.png'))
        self.icons['digitalsecuritycamera'] = GdkPixbuf.Pixbuf.new_from_file(icon)
        icon = resource_filename(__name__, os.path.join('icons','printer.png'))
        self.icons['printer'] = GdkPixbuf.Pixbuf.new_from_file(icon)
        icon = resource_filename(__name__, os.path.join('icons','folder.png'))
        self.folder_icon = GdkPixbuf.Pixbuf.new_from_file(icon)
        icon = resource_filename(__name__, os.path.join('icons','upnp-service.png'))
        self.service_icon = GdkPixbuf.Pixbuf.new_from_file(icon)
        icon = resource_filename(__name__, os.path.join('icons','upnp-action.png'))
        self.action_icon = GdkPixbuf.Pixbuf.new_from_file(icon)
        icon = resource_filename(__name__, os.path.join('icons','upnp-action-arg-in.png'))
        self.action_arg_in_icon = GdkPixbuf.Pixbuf.new_from_file(icon)
        icon = resource_filename(__name__, os.path.join('icons','upnp-action-arg-out.png'))
        self.action_arg_out_icon = GdkPixbuf.Pixbuf.new_from_file(icon)
        icon = resource_filename(__name__, os.path.join('icons','upnp-state-variable.png'))
        self.state_variable_icon = GdkPixbuf.Pixbuf.new_from_file(icon)

        self.store = Gtk.TreeStore(int,  # 0: type
                                   str,  # 1: name
                                   str,  # 2: device udn
                                   GdkPixbuf.Pixbuf,
                                   object
                                )

        self.treeview = Gtk.TreeView(self.store)
        self.column = Gtk.TreeViewColumn('Devices')
        self.treeview.append_column(self.column)

        # create a CellRenderers to render the data
        icon_cell = Gtk.CellRendererPixbuf()
        text_cell = Gtk.CellRendererText()

        self.column.pack_start(icon_cell, False)
        self.column.pack_start(text_cell, True)

        self.column.set_attributes(text_cell, text=1)
        self.column.add_attribute(icon_cell, "pixbuf",3)
        #self.column.set_cell_data_func(self.cellpb, get_icon)

        self.treeview.connect("button_press_event", self.button_action)
        self.treeview.connect("row-activated", self.activated)
        self.treeview.connect("move_cursor", self.moved_cursor)

        selection = self.treeview.get_selection()
        selection.set_mode(Gtk.SelectionMode.SINGLE)

        self.window.add(self.treeview)

        self.windows = {}

    def activated(self,view,row_path,column):
        iter = self.store.get_iter(row_path)
        if iter:
            type,object = self.store.get(iter,TYPE_COLUMN,OBJECT_COLUMN)
            if type == ACTION:
                id = '@'.join((object.service.device.get_usn(),object.service.service_type,object.name))
                try:
                    self.windows[id].show()
                except:
                    window = Gtk.Window()
                    window.set_default_size(350, 300)
                    window.set_title('Invoke Action %s' % object.name)
                    window.connect("delete_event", self.deactivate, id)

                    def build_label(icon,label):
                        hbox = Gtk.HBox(homogeneous=False, spacing=10)
                        image = Gtk.Image()
                        image.set_from_pixbuf(icon)
                        hbox.pack_start(image,False,False,2)
                        text = Gtk.Label(label=label)
                        hbox.pack_start(text,False,False,2)
                        return hbox

                    def build_button(label):
                        hbox = Gtk.HBox(homogeneous=False, spacing=10)
                        image = Gtk.Image()
                        image.set_from_pixbuf(self.action_icon)
                        hbox.pack_start(image,False,False,2)
                        text = Gtk.Label(label=label)
                        hbox.pack_start(text,False,False,2)
                        button = Gtk.Button()
                        button.set_can_default(True)
                        button.add(hbox)

                        return button

                    def build_arguments(action,direction):
                        text = Gtk.Label(label="<b>'%s' arguments:</b>'" % direction)
                        text.set_use_markup(True)
                        hbox = Gtk.HBox(homogeneous=False, spacing=10)
                        hbox.pack_start(text,False,False,2)
                        vbox = Gtk.VBox(homogeneous=False, spacing=10)
                        vbox.pack_start(hbox,False,False,2)
                        row = 0
                        if direction == 'in':
                            arguments = object.get_in_arguments()
                        else:
                            arguments = object.get_out_arguments()
                        table = Gtk.Table(rows=len(arguments), columns=2, homogeneous=False)
                        entries = {}
                        for argument in arguments:
                            variable = action.service.get_state_variable(argument.state_variable)
                            name = Gtk.Label(label=argument.name+':')
                            name.set_alignment(0,0)
                            #hbox = Gtk.HBox(homogeneous=False, spacing=2)
                            #hbox.pack_start(name,False,False,2)
                            table.attach(name, 0, 1, row, row+1,Gtk.AttachOptions.SHRINK)
                            if variable.data_type == 'boolean':
                                entry = Gtk.CheckButton()
                                if direction == 'in':
                                    entries[argument.name] = entry.get_active
                                else:
                                    entry.set_sensitive(False)
                                    entries[argument.name] = (variable.data_type,entry.set_active)
                            elif variable.data_type == 'string':
                                if direction == 'in' and len(variable.allowed_values) > 0:
                                    store = Gtk.ListStore(str)
                                    for value in variable.allowed_values:
                                        store.append((value,))
                                    entry = Gtk.ComboBox()
                                    text_cell = Gtk.CellRendererText()
                                    entry.pack_start(text_cell, True)
                                    entry.set_attributes(text_cell, text=0)
                                    entry.set_model(store)
                                    entry.set_active(0)
                                    entries[argument.name] = (entry.get_active,entry.get_model)
                                else:
                                    if direction == 'in':
                                        entry = Gtk.Entry(max=0)
                                        entries[argument.name] = entry.get_text
                                    else:
                                        entry = Gtk.ScrolledWindow()
                                        entry.set_border_width(1)
                                        entry.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
                                        entry.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
                                        textview = Gtk.TextView()
                                        textview.set_editable(False)
                                        textview.set_wrap_mode(Gtk.WrapMode.WORD)
                                        entry.add(textview)
                                        entries[argument.name] = ('text',textview)
                            else:
                                if direction == 'out':
                                    entry = Gtk.Entry(max=0)
                                    entry.set_editable(False)
                                    entries[argument.name] = (variable.data_type,entry.set_text)
                                else:
                                    adj = Gtk.Adjustment(0, 0, 4294967296, 1.0, 50.0, 0.0)
                                    entry = Gtk.SpinButton(adj, 0, 0)
                                    entry.set_numeric(True)
                                    entry.set_digits(0)
                                    entries[argument.name] = entry.get_value_as_int

                            table.attach(entry,1,2,row,row+1,Gtk.AttachOptions.FILL|Gtk.AttachOptions.EXPAND,Gtk.AttachOptions.FILL|Gtk.AttachOptions.EXPAND)
                            row += 1
                        #hbox = Gtk.HBox(homogeneous=False, spacing=10)
                        #hbox.pack_start(table,False,False,2)
                        #hbox.show()
                        vbox.pack_start(table,False,False,2)
                        return vbox,entries

                    vbox = Gtk.VBox(homogeneous=False, spacing=10)
                    vbox.pack_start(build_label(self.store[row_path[0]][ICON_COLUMN],self.store[row_path[0]][NAME_COLUMN]),False,False,2)
                    vbox.pack_start(build_label(self.service_icon,self.store[row_path[0],row_path[1]][NAME_COLUMN]),False,False,2)
                    vbox.pack_start(build_label(self.action_icon,object.name),False,False,2)
                    hbox = Gtk.HBox(homogeneous=False, spacing=10)
                    hbox.pack_start(vbox,False,False,2)
                    button = build_button('Invoke')
                    hbox.pack_end(button,False,False,20)
                    vbox = Gtk.VBox(homogeneous=False, spacing=10)
                    vbox.pack_start(hbox,False,False,2)
                    in_entries = {}
                    out_entries = {}
                    if len(object.get_in_arguments()) > 0:
                        box,in_entries = build_arguments(object, 'in')
                        vbox.pack_start(box,False,False,2)
                    if len(object.get_out_arguments()) > 0:
                        box,out_entries = build_arguments(object, 'out')
                        vbox.pack_start(box,False,False,2)
                    window.add(vbox)

                    status_bar = Gtk.Statusbar()
                    context_id = status_bar.get_context_id("Action Statusbar")
                    vbox.pack_end(status_bar,False,False,2)

                    button.connect('clicked',self.call_action,object,in_entries,out_entries,status_bar)

                    window.show_all()
                    self.windows[id] = window
            else:
                if view.row_expanded(row_path):
                    view.collapse_row(row_path)
                else:
                    view.expand_row(row_path, False)

    def deactivate(self,window,event,id):
        #print "deactivate",id
        del self.windows[id]

    def button_action(self, widget, event):
        x = int(event.x)
        y = int(event.y)
        path = self.treeview.get_path_at_pos(x, y)
        if path == None:
            return True
        row_path,column,_,_ = path
        if event.button == 3:
            if self.cb_item_right_click != None:
                return self.cb_item_right_click(widget, event)
            else:
                iter = self.store.get_iter(row_path)
                type,object= self.store.get(iter,TYPE_COLUMN,OBJECT_COLUMN)
                if type == DEVICE:
                    menu = Gtk.Menu()
                    item = Gtk.CheckMenuItem("show events")
                    item.set_sensitive(False)
                    menu.append(item)
                    item = Gtk.CheckMenuItem("show log")
                    item.set_sensitive(False)
                    menu.append(item)
                    menu.append(Gtk.SeparatorMenuItem())
                    item = Gtk.MenuItem("extract device and service descriptions...")
                    item.connect("activate", self.extract_descriptions, object)
                    menu.append(item)
                    menu.append(Gtk.SeparatorMenuItem())
                    item = Gtk.MenuItem("test device...")
                    item.set_sensitive(False)
                    menu.append(item)
                    if(object != None and
                       object.get_device_type().split(':')[3].lower() == 'mediaserver'):
                        menu.append(Gtk.SeparatorMenuItem())
                        item = Gtk.MenuItem("browse MediaServer")
                        item.connect("activate", self.mediaserver_browse, object)
                        menu.append(item)
                    if(object != None and
                       object.get_device_type().split(':')[3].lower() == 'mediarenderer'):
                        menu.append(Gtk.SeparatorMenuItem())
                        item = Gtk.MenuItem("control MediaRendererer")
                        item.connect("activate", self.mediarenderer_control, object)
                        menu.append(item)
                    if(object != None and
                       object.get_device_type().split(':')[3].lower() == 'internetgatewaydevice'):
                        menu.append(Gtk.SeparatorMenuItem())
                        item = Gtk.MenuItem("control InternetGatewayDevice")
                        item.connect("activate", self.igd_control, object)
                        menu.append(item)
                    menu.show_all()
                    menu.popup(None,None,None,event.button,event.time)
                    return True
                elif type == SERVICE:
                    menu = Gtk.Menu()
                    item = Gtk.CheckMenuItem("show events")
                    item.set_sensitive(False)
                    menu.append(item)
                    item = Gtk.CheckMenuItem("show log")
                    item.set_sensitive(False)
                    menu.append(item)
                    menu.show_all()
                    menu.popup(None,None,None,event.button,event.time)
                    return True
                return False
        if(event.button == 1 and
           self.cb_item_left_click != None):
            reactor.callLater(0.1,self.cb_item_left_click,widget,event)
            return False
        return 0

    def extract_descriptions(self,w,device):
        print "extract xml descriptions", w,device
        from extract import Extract
        id = '@'.join((device.get_usn(),'DeviceXMlExtract'))
        try:
            self.windows[id].show()
        except:
            ui = Extract(device)
            self.windows[id] = ui.window

    def moved_cursor(self,widget,step, count):
        reactor.callLater(0.1,self.cb_item_left_click,widget,None)
        return False

    def init_controlpoint(self):
        self.coherence.connect(self.device_found, 'Coherence.UPnP.RootDevice.detection_completed')
        self.coherence.connect(self.device_removed, 'Coherence.UPnP.RootDevice.removed')
        for device in self.coherence.devices:
            self.device_found(device)

    def call_action(self,widget,action,in_entries,out_entries,status_bar):
        self.debug("in_entries %r" % in_entries)
        self.debug("out_entries %r" % out_entries)
        context_id = status_bar.get_context_id("Action Statusbar")
        status_bar.pop(context_id)
        status_bar.push(context_id,"%s - calling %s" % (time.strftime("%H:%M:%S"),action.name))

        kwargs = {}
        for entry,method in in_entries.items():
            if isinstance(method,tuple):
                kwargs[entry] = unicode(method[1]()[method[0]()][0])
            else:
                value = method()
                if type(value) == bool:
                    if value == True:
                        kwargs[entry] = '1'
                    else:
                        kwargs[entry] = '0'
                else:
                    kwargs[entry] = unicode(value)

        def populate(result, entries):
            self.info("result %r" % result)
            self.info("entries %r" % entries)
            status_bar.pop(context_id)
            status_bar.push(context_id,"%s - ok" % time.strftime("%H:%M:%S"))
            for argument,value in result.items():
                type,method = entries[argument]
                if type == 'boolean':
                    value = means_true(value)
                if type == 'text':
                    method.get_buffer().set_text(value)
                    continue
                method(value)

        def fail(f):
            self.debug(f)
            status_bar.pop(context_id)
            status_bar.push(context_id,"%s - fail %s" % (time.strftime("%H:%M:%S"),str(f.value)))

        self.info("action %s call %r" % (action.name,kwargs))
        d = action.call(**kwargs)
        d.addCallback(populate,out_entries)
        d.addErrback(fail)

    def device_found(self,device=None,row=None):
        self.info(device.get_friendly_name(), device.get_usn(), device.get_device_type().split(':')[3].lower(), device.get_device_type())
        name = '%s (%s)' % (device.get_friendly_name(), ':'.join(device.get_device_type().split(':')[3:5]))
        item = self.store.append(row, (DEVICE,name,device.get_usn(),
                                        self.icons.get(device.get_device_type().split(':')[3].lower(),self.icons['device']),
                                        device))
        for service in device.services:
            _,_,_,service_class,version = service.service_type.split(':')
            service.subscribe()
            service_item = self.store.append(item,(SERVICE,':'.join((service_class,version)),service.service_type,self.service_icon,service))
            variables_item = self.store.append(service_item,(-1,'State Variables','',self.folder_icon,None))
            for variable in service.get_state_variables(0).values():
                self.store.append(variables_item,(VARIABLE,variable.name,'',self.state_variable_icon,variable))
            for action in service.get_actions().values():
                action_item = self.store.append(service_item,(ACTION,action.name,'',self.action_icon,action))
                for argument in action.get_in_arguments():
                    self.store.append(action_item,(ARGUMENT,argument.name,'',self.action_arg_in_icon,argument))
                for argument in action.get_out_arguments():
                    self.store.append(action_item,(ARGUMENT,argument.name,'',self.action_arg_out_icon,argument))

        for embedded_device in device.devices:
            self.device_found(embedded_device,row=item)

    def device_removed(self,usn=None):
        self.info('device_removed %r' % usn)
        row_count = 0
        for row in self.store:
            if usn == row[UDN_COLUMN]:
                ids = []
                for w in self.windows.keys():
                    if w.startswith(usn):
                        ids.append(w)
                for id in ids:
                    self.windows[id].destroy()
                    del self.windows[id]
                self.store.remove(self.store.get_iter(row_count))
                break
            row_count += 1

    def mediaserver_browse(self,widget,device):
        from mediaserver import MediaServerWidget
        id = '@'.join((device.get_usn(),'MediaServerBrowse'))
        try:
            self.windows[id].show()
        except:
            ui = MediaServerWidget(self.coherence,device)
            self.windows[id] = ui.window
        #ui.cb_item_right_click = self.button_pressed
        #ui.window.show_all()

    def mediarenderer_control(self,widget,device):
        from mediarenderer import MediaRendererWidget
        id = '@'.join((device.get_usn(),'MediaRendererControl'))
        try:
            self.windows[id].show()
        except:
            ui = MediaRendererWidget(self.coherence,device)
            self.windows[id] = ui.window

    def igd_control(self,widget,device):
        from igd import IGDWidget
        id = '@'.join((device.get_usn(),'IGDControl'))
        try:
            self.windows[id].show()
        except:
            ui = IGDWidget(self.coherence,device)
            self.windows[id] = ui.window
