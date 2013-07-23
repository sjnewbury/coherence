# -*- coding: utf-8 -*-

# Licensed under the MIT license
# http://opensource.org/licenses/mit-license.php

# Copyright 2009 - Frank Scholz <coherence@beebits.net>

import time

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

from coherence import log

class LogWidget(log.Loggable):
    logCategory = 'inspector'

    def __init__(self, coherence,max_lines=500):
        self.coherence = coherence
        self.max_lines = max_lines
        self.window = Gtk.Window(Gtk.WindowType.TOPLEVEL)
        self.window.set_default_size(500,400)
        self.window.set_title('Log')
        scroll_window = Gtk.ScrolledWindow()
        scroll_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.store = Gtk.ListStore(str,str,str,str)
        self.treeview = Gtk.TreeView(self.store)
        column = Gtk.TreeViewColumn('Time')
        self.treeview.append_column(column)
        text_cell = Gtk.CellRendererText()
        column.pack_start(text_cell, False)
        column.set_attributes(text_cell,text=0)
        column = Gtk.TreeViewColumn('')
        self.treeview.append_column(column)
        text_cell = Gtk.CellRendererText()
        column.pack_start(text_cell, False)
        column.set_attributes(text_cell,text=1)
        column = Gtk.TreeViewColumn('Host')
        self.treeview.append_column(column)
        text_cell = Gtk.CellRendererText()
        column.pack_start(text_cell, False)
        column.set_attributes(text_cell,text=2)
        column = Gtk.TreeViewColumn('')
        self.treeview.append_column(column)
        text_cell = Gtk.CellRendererText()
        column.pack_start(text_cell, True)
        column.set_attributes(text_cell,text=3)
        scroll_window.add_with_viewport(self.treeview)
        #self.treeview.set_fixed_height_mode(True)
        self.window.add(scroll_window)
        self.coherence.connect(self.append, 'Coherence.UPnP.Log')

    def append(self,module,host,txt):
        if len(self.store) >= 500:
            del self.store[0]

        timestamp = time.strftime("%H:%M:%S")
        self.store.insert(0,(timestamp,module,host,txt))