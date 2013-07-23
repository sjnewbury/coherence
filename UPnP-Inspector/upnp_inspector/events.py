# -*- coding: utf-8 -*-

# Licensed under the MIT license
# http://opensource.org/licenses/mit-license.php

# Copyright 2009 - Frank Scholz <coherence@beebits.net>

import time

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

from twisted.internet import reactor

from coherence import log

class EventsWidget(log.Loggable):
    logCategory = 'inspector'

    def __init__(self, coherence,max_lines=500):
        self.coherence = coherence
        self.max_lines = max_lines
        self.window = Gtk.Window(Gtk.WindowType.TOPLEVEL)
        self.window.set_default_size(500,400)
        self.window.set_title('Events')
        scroll_window = Gtk.ScrolledWindow()
        scroll_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.store = Gtk.ListStore(str,str,str,str,str,str)
        self.treeview = Gtk.TreeView(self.store)
        column = Gtk.TreeViewColumn('Time')
        self.treeview.append_column(column)
        text_cell = Gtk.CellRendererText()
        column.pack_start(text_cell, False)
        column.set_attributes(text_cell,text=0)
        column = Gtk.TreeViewColumn('Device')
        self.treeview.append_column(column)
        text_cell = Gtk.CellRendererText()
        column.pack_start(text_cell, False)
        column.set_attributes(text_cell,text=1)
        column = Gtk.TreeViewColumn('Service')
        self.treeview.append_column(column)
        text_cell = Gtk.CellRendererText()
        column.pack_start(text_cell, False)
        column.set_attributes(text_cell,text=2)
        column = Gtk.TreeViewColumn('Variable')
        self.treeview.append_column(column)
        text_cell = Gtk.CellRendererText()
        column.pack_start(text_cell, False)
        column.set_attributes(text_cell,text=3)
        column = Gtk.TreeViewColumn('Value')
        self.treeview.append_column(column)
        text_cell = Gtk.CellRendererText()
        column.pack_start(text_cell, True)
        column.set_attributes(text_cell,text=4)
        scroll_window.add_with_viewport(self.treeview)
        #self.treeview.set_fixed_height_mode(True)
        self.window.add(scroll_window)

        self.treeview.connect("button_press_event", self.button_action)

        self.coherence.connect(self.append, 'Coherence.UPnP.DeviceClient.Service.Event.processed')

    def append(self,service,event):
        if len(self.store) >= 500:
            del self.store[0]

        timestamp = time.strftime("%H:%M:%S")
        _,_,_,service_class,version = service.service_type.split(':')
        self.store.insert(0,(timestamp,service.device.friendly_name,service_class,event[0],event[1],event[2]))

    def button_action(self, widget, event):
        x = int(event.x)
        y = int(event.y)
        path = self.treeview.get_path_at_pos(x, y)
        if path == None:
            return True
        row_path,column,_,_ = path
        if event.button == 3:
            clipboard = Gtk.clipboard_get(Gdk.SELECTION_CLIPBOARD)
            iter = self.store.get_iter(row_path)
            menu = Gtk.Menu()
            item = Gtk.MenuItem("copy value")
            value,= self.store.get(iter,4)
            item.connect("activate", lambda w: clipboard.set_text(value))
            menu.append(item)

            item = Gtk.MenuItem("copy raw event")
            raw,= self.store.get(iter,5)
            try:
                from coherence.extern.et import ET, indent, parse_xml
                xml = parse_xml(raw)
                xml = xml.getroot()
                indent(xml,0)
                raw = ET.tostring(xml, encoding='utf-8')
            except:
                import traceback
                print traceback.format_exc()

            item.connect("activate", lambda w: clipboard.set_text(raw))
            menu.append(item)


            menu.show_all()
            menu.popup(None,None,None,event.button,event.time)
            return True

        return False