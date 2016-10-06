#!/usr/bin/env python
# -*- coding:utf-8 -*-

#
# Copyright 2011 malev.com.ar
#
# Author: Marcos Vanetta <marcosvanetta@gmail.com>
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of either or both of the following licenses:
#
# 1) the GNU Lesser General Public License version 3, as published by the
# Free Software Foundation; and/or
# 2) the GNU Lesser General Public License version 2.1, as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranties of
# MERCHANTABILITY, SATISFACTORY QUALITY or FITNESS FOR A PARTICULAR
# PURPOSE.  See the applicable version of the GNU Lesser General Public
# License for more details.
#
# You should have received a copy of both the GNU Lesser General Public
# License version 3 and version 2.1 along with this program.  If not, see
# <http://www.gnu.org/licenses/>

"""
Pomodoro's indicator
"""

import os
import gobject
import gtk
import pynotify
import sys
import wave
import pyaudio
import pomodoro_state
import configuration
from taskw import TaskWarriorShellout as tw

# ICONS
# http://www.softicons.com/free-icons/food-drinks-icons/veggies-icons-by-icon-icon/tomato-icon


class PomodoroOSDNotificator(object):
    """ Provide a panel indicator and notifier for Pomodora timer"""

    loop = None

    def __init__(self):
        self.icon_directory = configuration.icon_directory()
        pynotify.init("icon-summary-body")

    def alarm_sound(self):
        return self.icon_directory + "bells_1.wav"

    def beep(self):
        # define stream chunk
        chunk = 1024

        # open a wav format music
        snd_path = self.alarm_sound()
        f = wave.open(snd_path, "rb")
        # instantiate PyAudio
        p = pyaudio.PyAudio()
        # open stream
        stream = p.open(format=p.get_format_from_width(f.getsampwidth()),
                        channels=f.getnchannels(),
                        rate=f.getframerate(),
                        output=True)
        # read data
        data = f.readframes(chunk)

        # paly stream
        while data != '':
            stream.write(data)
            data = f.readframes(chunk)

        # stop stream
        stream.stop_stream()
        stream.close()

        # close PyAudio
        p.terminate()

    def big_red_icon(self):
        return self.icon_directory + "tomato_32.png"

    def stateResume(self):
        pass

    def notificate_with_sound(self, state, unpause):
        def resume(osd_box, action):
            stateResume()
            osd_box.close()
            global loop
            loop.quit()
        message = self.generate_message(state)
        global stateResume
        stateResume = unpause

        osd_box = pynotify.Notification(
            "Pomodoro",
            message,
            self.big_red_icon()
        )
        self.beep()
        if PomodoroIndicator.gpause is True:
            osd_box.add_action("action_go", "Ready?",
                               resume)
            osd_box.set_timeout(pynotify.EXPIRES_NEVER)
            osd_box.show()
            global loop
            loop = gobject.MainLoop()
            loop.run()
        else:
            osd_box.show()

    def generate_message(self, status):
        message = status            # dodgy message
        if status == pomodoro_state.WORKING_STATE:
            message = "You should start working."
        elif status == pomodoro_state.RESTING_STATE:
            message = "You can take a break now."
        elif status == pomodoro_state.LONG_RESTING_STATE:
            message = "You can take a longer break now."

        return message


class PomodoroIndicator:

    gpause = False

    def __init__(self, work, short, longer, start, pause, debug):
        PomodoroIndicator.gpause = pause
        self.pomodoro = pomodoro_state.PomodoroMachine(work, short, longer)
        self.notificator = PomodoroOSDNotificator()
        self.icon_directory = configuration.icon_directory()

        self.statusicon = gtk.StatusIcon()
        pixbuf = gtk.gdk.pixbuf_new_from_file(self.attention_icon())
        self.statusicon.set_from_pixbuf(pixbuf)

        self.statusicon.set_has_tooltip(True)
        # following line only posible with -replacement
        self.handler_id = self.statusicon.connect(
            "query-tooltip", self.icon_tooltip_callback)

        self.tw_installed = False

        home = os.path.expanduser("~/.taskrc")
        if os.path.exists(home):
            self.tw_installed = True
            test = os.path.expanduser("~/.taskrc_test")
            if debug is True:
                self.w = tw(config_filename="~/.taskrc_test")
            else:
                self.w = tw()
                test = None

            try:
                from app.twcurrent import TwCurrent
                twc = TwCurrent(test)
                current = twc.get_current()
                self.desc = 'Current task: ' + current['description']
            except:
                pass

        self.menu_setup()

        self.timer_id = None

        pomodoro_state.transition_blocked = pause

        if start is True:
            self.start_timer()
            self.pomodoro.start()
            pixbuf = gtk.gdk.pixbuf_new_from_file(self.active_icon())
            self.statusicon.set_from_pixbuf(pixbuf)
            self.redraw_menu()

    def icon_tooltip_callback(self, widget, x, y, keyboard_mode, tooltip):
        # set the text for the tooltip
        self.tooltip = tooltip
        time_remaining = self.pomodoro.state.max_time - \
            self.pomodoro.state.elapsed_time
        str_time_remaining = self.pomodoro.convert_time(time_remaining)
        tip_content = (
            "<b><big>Pomodoro </big></b>\n" +
            self.pomodoro.state.current_state() + " " +
            str_time_remaining + " remaining\n")
        if self.desc:
            tip_content += self.desc
        self.tooltip.set_markup(tip_content)
        # set an icon for the tooltip
        pixbuf = gtk.gdk.pixbuf_new_from_file(self.big_red_icon())
        self.tooltip.set_icon(pixbuf)
        # show the tooltip
        return True

    def attention_icon(self):
        return self.icon_directory + "tomato_grey.png"  # "indicator-messages"

    def idle_icon(self):
        return self.icon_directory + "tomato_green_24.png"  # "ind...-messages"

    def active_icon(self):
        return self.icon_directory + "tomato_24.png"  # "indicator-messages"

    def big_red_icon(self):
        return self.icon_directory + "tomato_32.png"

    def menu_setup(self):
        self.menu = gtk.Menu()
        self.popup_menu = self.menu
        self.separator1 = gtk.SeparatorMenuItem()
        self.separator2 = gtk.SeparatorMenuItem()
        self.separator3 = gtk.SeparatorMenuItem()
        self.current_state_item = gtk.MenuItem("Waiting")
        self.timer_item = gtk.MenuItem("00:00")

        # Drawing buttons
        self.start_item = gtk.MenuItem("Start")
        self.pause_item = gtk.MenuItem("Pause")
        self.resume_item = gtk.MenuItem("Resume")
        self.stop_item = gtk.MenuItem("Stop")
        self.quit_item = gtk.MenuItem("Quit")
        self.tw_item = gtk.MenuItem("Task")

        self.state_visible_menu_items = {
            pomodoro_state.WAITING_STATE: [self.start_item],
            pomodoro_state.WORKING_STATE: [self.pause_item, self.stop_item],
            pomodoro_state.RESTING_STATE: [self.pause_item, self.stop_item],
            pomodoro_state.LONG_RESTING_STATE: [self.pause_item,
                                                self.stop_item],
            pomodoro_state.PAUSED_STATE: [self.resume_item, self.stop_item]
        }

        self.available_states = pomodoro_state.AVAILABLE_STATES

        self.hidable_menu_items = [self.start_item, self.pause_item,
                                   self.resume_item, self.stop_item]

        self.start_item.connect("activate", self.start)
        self.pause_item.connect("activate", self.pause)
        self.resume_item.connect("activate", self.resume)
        self.stop_item.connect("activate", self.stop)
        self.quit_item.connect("activate", self.quit)
        self.tw_item.connect("activate", self.tw_dialog)

        self.menu_items = [
            self.current_state_item,
            self.timer_item,
            self.separator1,
            self.start_item,
            self.pause_item,
            self.resume_item,
            self.stop_item,
            self.separator2,
            self.tw_item,
            self.separator3,
            self.quit_item
        ]
        self.tw = True
        for item in self.menu_items:
            item.show()
            self.menu.append(item)

        if self.tw_installed is False:
            self.tw_item.hide()
            self.separator3.hide()
        self.redraw_menu()
        self.statusicon.connect("popup-menu", self.on_popup)
        self.statusicon.connect('activate', self.on_left_click)

    def on_popup(self, icon, button, time):
        self.popup_menu.popup(
            None, None, gtk.status_icon_position_menu, button,
            time, self.statusicon)

    def on_left_click(self, event):
        self.message("Status Icon Left Clicked")

    def message(self, data=None):
        "Pomodoro left click."
        msg = gtk.MessageDialog(None, gtk.DIALOG_MODAL,
                                gtk.MESSAGE_INFO, gtk.BUTTONS_OK, data)
        msg.run()
        msg.destroy()

    def button_pushed(self, widget, data=None):
        method = getattr(self, data.get_child().get_text().lower())
        method()

    def hide_hidable_menu_items(self):
        for item in self.hidable_menu_items:
            item.hide()

    def redraw_menu(self):
        self.hide_hidable_menu_items()
        self.change_status_menu_item_label()
        for state, items in self.state_visible_menu_items.iteritems():
            if self.current_state() == state:
                for item in items:
                    item.show()

    def change_status_menu_item_label(self):
        label = self.current_state_item.child
        label.set_text(self.pomodoro.current_state().capitalize())

    def change_timer_menu_item_label(self, next_label):
        label = self.timer_item.child
        label.set_text(next_label)

    def tw_dialog(self, widget):
        window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        window.set_usize(200, 100)
        window.set_title("New Task Details")
        window.connect("delete_event", gtk.mainquit)

        vbox = gtk.VBox(gtk.FALSE, 0)
        window.add(vbox)
        vbox.show()

        entry = gtk.Entry(50)
        entry.connect("activate", self.enter_callback, entry)
        entry.set_text("hello")
        entry.append_text(" world")
        entry.select_region(0, len(entry.get_text()))
        vbox.pack_start(entry, gtk.TRUE, gtk.TRUE, 0)
        entry.show()

        hbox = gtk.HBox(gtk.FALSE, 0)
        vbox.add(hbox)
        hbox.show()

        button = gtk.Button("Close")
        button.connect_object("clicked", self.close_window, window)
        vbox.pack_start(button, gtk.TRUE, gtk.TRUE, 0)
        button.set_flags(gtk.CAN_DEFAULT)
        button.grab_default()
        button.show()
        window.show()

    def enter_callback(self, widget, entry):
        entry_text = entry.get_text()
        print "Entry contents: %s\n" % entry_text
        self.w.task_add(entry_text, tag="in")
        parent = widget.get_parent()
        parent = parent.get_parent()
        parent.destroy()

    def close_window(self, widget):
        box = widget.get_child()
        children = box.get_children()
        entry = children.pop()
        while not isinstance(entry, gtk.Entry):
            entry = children.pop()
        entry_text = entry.get_text()
        print "Entry contents: %s\n" % entry_text
        self.w.task_add(entry_text, tag="in")

        widget.destroy()

    def generate_notification(self):
        if self.current_state() == pomodoro_state.WORKING_STATE:
            pixbuf = gtk.gdk.pixbuf_new_from_file(self.active_icon())
            self.statusicon.set_from_pixbuf(pixbuf)
        elif self.current_state() == pomodoro_state.RESTING_STATE:
            pixbuf = gtk.gdk.pixbuf_new_from_file(self.idle_icon())
            self.statusicon.set_from_pixbuf(pixbuf)
        elif self.current_state() == pomodoro_state.LONG_RESTING_STATE:
            pixbuf = gtk.gdk.pixbuf_new_from_file(self.idle_icon())
            self.statusicon.set_from_pixbuf(pixbuf)

        if PomodoroIndicator.gpause is True:
            self.stop_timer()
        self.notificator.notificate_with_sound(self.current_state(),
                                               self.start_timer)

    # Methods that interact with the PomodoroState collaborator.
    def update_timer(self):
        self.start_timer()
        changed = self.pomodoro.next_second()
        self.change_timer_menu_item_label(self.pomodoro.elapsed_time())
        if changed:
            self.generate_notification()
            self.redraw_menu()

    def current_state(self):
        for state in self.available_states:
            if self.pomodoro.in_this_state(state):
                return state

    def start(self, widget, data=None):
        self.start_timer()
        self.pomodoro.start()
        pixbuf = gtk.gdk.pixbuf_new_from_file(self.active_icon())
        self.statusicon.set_from_pixbuf(pixbuf)
        self.redraw_menu()

    def pause(self, widget=None, data=None):
        self.stop_timer()
        self.pomodoro.pause()
        self.redraw_menu()

    def resume(self, widget=None, data=None):
        self.start_timer()
        self.pomodoro.resume()
        self.redraw_menu()

    def toggle_pause(self):
        if self.current_state() != "paused":
            self.pause()
        else:
            self.resume()

    def stop(self, widget, data=None):
        self.stop_timer()
        pynotify.Notification.close
        self.pomodoro.stop()
        self.redraw_menu()

    def start_timer(self):
        self.timer_id = gobject.timeout_add(1000, self.update_timer)

    def stop_timer(self):
        if self.timer_id:
            gobject.source_remove(self.timer_id)
        self.timer_id = None

    def main(self):
        gtk.main()

    def quit(self, widget):
        sys.exit(0)

if __name__ == "__main__":
    print __doc__
