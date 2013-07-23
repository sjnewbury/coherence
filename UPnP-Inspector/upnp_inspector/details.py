# -*- coding: utf-8 -*-

# Licensed under the MIT license
# http://opensource.org/licenses/mit-license.php

# Copyright 2009 - Frank Scholz <coherence@beebits.net>

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

from coherence import log

class DetailsWidget(log.Loggable):
    logCategory = 'inspector'

    def __init__(self, coherence):
        self.coherence = coherence
        self.window = Gtk.Window(Gtk.WindowType.TOPLEVEL)
        self.window.set_default_size(500,460)
        self.window.set_title('Details')
        scroll_window = Gtk.ScrolledWindow()
        scroll_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.store = Gtk.TreeStore(str,object)
        self.treeview = Gtk.TreeView(self.store)
        column = Gtk.TreeViewColumn('Name')
        self.treeview.append_column(column)
        text_cell = Gtk.CellRendererText()
        column.pack_start(text_cell, False)
        column.set_attributes(text_cell,text=0)
        column = Gtk.TreeViewColumn('Value')
        self.treeview.insert_column_with_data_func(-1,'Value',Gtk.CellRendererText(),self.celldatamethod)
        text_cell = Gtk.CellRendererText()
        column.pack_start(text_cell, True)
        column.set_attributes(text_cell,text=1)

        self.treeview.connect("button_press_event", self.button_action)

        self.clipboard = Gtk.clipboard_get(Gdk.SELECTION_CLIPBOARD)

        scroll_window.add(self.treeview)
        self.window.add(scroll_window)

    def celldatamethod(self,column,cell,model,iter):
        value, = model.get(iter,1)
        if isinstance(value,tuple):
            value = value[0]
        cell.set_property('text',value)

    def refresh(self,object):
        self.store.clear()
        if object == None:
            return
        try:
            for t in object.as_tuples():
                row = self.store.append(None,t)
                try:
                    if isinstance(t[1][2],dict):
                        for k,v in t[1][2].items():
                            self.store.append(row,(k,v))
                except (IndexError,TypeError):
                    pass
        except AttributeError:
            #import traceback
            #print traceback.format_exc()
            pass
        except Exception:
            import traceback
            print traceback.format_exc()

    def open_url(self,url):
        import webbrowser
        webbrowser.open(url)

    def button_action(self, widget, event):
        x = int(event.x)
        y = int(event.y)
        path = self.treeview.get_path_at_pos(x, y)
        if path == None:
            return True
        row_path,column,_,_ = path
        if event.button == 3:
            iter = self.store.get_iter(row_path)
            menu = Gtk.Menu()
            item = Gtk.MenuItem("copy value")
            value,= self.store.get(iter,1)
            if isinstance(value,tuple):
                item.connect("activate", lambda w: self.clipboard.set_text(value[0]))
            else:
                item.connect("activate", lambda w: self.clipboard.set_text(value))
            menu.append(item)
            if isinstance(value,tuple):
                menu.append(Gtk.SeparatorMenuItem())
                item = Gtk.MenuItem("copy URL")
                item.connect("activate", lambda w: self.clipboard.set_text(value[1]))
                menu.append(item)
                if(len(value) < 3 or
                   (value[2] == True or isinstance(value[2],dict))):
                    item = Gtk.MenuItem("open URL")
                    item.connect("activate", lambda w: self.open_url(value[1]))
                    menu.append(item)

            menu.show_all()
            menu.popup(None,None,None,event.button,event.time)
            return True

        return False