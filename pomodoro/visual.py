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

import gobject
import gtk
import appindicator
import pynotify
import sys
import pomodoro_state
import configuration

"""
Pomodoro's indicator
"""
# ICONS
# http://www.softicons.com/free-icons/food-drinks-icons/veggies-icons-by-icon-icon/tomato-icon


class PomodoroOSDNotificator:

    def __init__(self):
        self.icon_directory = configuration.icon_directory()
        pynotify.init("icon-summary-body")

    def beep(self):
        pass

    def big_red_icon(self):
        return self.icon_directory + "tomato_32.png"

    def outer_resume(self, osd_box, action):
        print "Found outer callback"
        print action
        stateResume()
        print "back from resume"
        osd_box.close()
        global loop
        loop.quit()

    def notificate_with_sound(self, state, unpause):
        message = self.generate_message(state)
        global stateResume
        stateResume = unpause

        osd_box = pynotify.Notification(
            "Pomodoro",
            message,
            self.big_red_icon()
        )
        print PomodoroIndicator.gpause
        print state
        if PomodoroIndicator.gpause is True:
            osd_box.add_action("action_go", "Ready?",
                               self.outer_resume)
            osd_box.set_timeout(pynotify.EXPIRES_NEVER)

            osd_box.show()
            #gobject.MainLoop().run()
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

    def __init__(self, work, short, longer, start, pause):
        PomodoroIndicator.gpause = pause
        self.pomodoro = pomodoro_state.PomodoroMachine(work, short, longer)
        self.notificator = PomodoroOSDNotificator()
        self.icon_directory = configuration.icon_directory()
        self.ind = appindicator.Indicator(
            "pomodoro-indicator",
            self.idle_icon(),
            appindicator.CATEGORY_APPLICATION_STATUS)
        self.ind.set_status(appindicator.STATUS_ACTIVE)
        self.ind.set_attention_icon("new-messages-red")
        self.ind.set_label("25:00")
        self.ind.set_attention_icon(self.idle_icon())

        self.menu_setup()
        self.ind.set_menu(self.menu)

        self.timer_id = None

        if start is True:
            self.start_timer()
            self.pomodoro.start()
            self.redraw_menu()

    def attention_icon(self):
        return self.icon_directory + "tomato_grey.png"  # "indicator-messages"

    def idle_icon(self):
        return self.icon_directory + "tomato_green_24.png"  # "ind...-messages"

    def active_icon(self):
        return self.icon_directory + "tomato_24.png"  # "indicator-messages"

    def menu_setup(self):
        self.menu = gtk.Menu()
        self.separator1 = gtk.SeparatorMenuItem()
        self.separator2 = gtk.SeparatorMenuItem()
        self.current_state_item = gtk.MenuItem("Waiting")
        self.timer_item = gtk.MenuItem("00:00")

        # Drawing buttons
        self.start_item = gtk.MenuItem("Start")
        self.pause_item = gtk.MenuItem("Pause")
        self.resume_item = gtk.MenuItem("Resume")
        self.stop_item = gtk.MenuItem("Stop")
        self.quit_item = gtk.MenuItem("Quit")

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

        self.menu_items = [
            self.current_state_item,
            self.timer_item,
            self.separator1,
            self.start_item,
            self.pause_item,
            self.resume_item,
            self.stop_item,
            self.separator2,
            self.quit_item
        ]

        for item in self.menu_items:
            item.show()
            self.menu.append(item)
        self.redraw_menu()

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

    def generate_notification(self):
        if self.current_state() == pomodoro_state.WORKING_STATE:
            self.ind.set_status(appindicator.STATUS_ACTIVE)
        elif self.current_state() == pomodoro_state.RESTING_STATE:
            self.ind.set_status(appindicator.STATUS_ATTENTION)
        elif self.current_state() == pomodoro_state.LONG_RESTING_STATE:
            self.ind.set_status(appindicator.STATUS_ATTENTION)

        if PomodoroIndicator.gpause is True:
            #self.pomodoro.pause()
            self.toggle_pause()
            #self.pomodoro.pause()
            #self.redraw_menu()
        self.notificator.notificate_with_sound(self.current_state(),
                                               self.toggle_pause)
        # self.notificator.notificate_with_sound(self.current_state(),
        #                                        self.toggle_pause)


    # Methods that interact with the PomodoroState collaborator.
    def update_timer(self):
        print "update_timer()"
        self.start_timer()
        changed = self.pomodoro.next_second()
        self.change_timer_menu_item_label(self.pomodoro.elapsed_time())
        if changed:
            print ("update_timer changed")
            self.generate_notification()
            self.redraw_menu()

    def current_state(self):
        for state in self.available_states:
            if self.pomodoro.in_this_state(state):
                return state

    def start(self, widget, data=None):
        self.start_timer()
        self.pomodoro.start()
        self.ind.set_icon(self.active_icon())
        self.redraw_menu()

    def pause(self, widget=None, data=None):
        self.stop_timer()
        self.pomodoro.pause()
        self.redraw_menu()

    def resume(self, widget=None, data=None):
        # assume this can only be used by menu
        # self.stop_timer()
        self.start_timer()
        self.pomodoro.resume()
        self.redraw_menu()

    def toggle_pause(self):
        print ("toggle_pause " + self.current_state())
        import pdb; pdb.set_trace()  # XXX BREAKPOINT
        if self.current_state() != "paused":
            self.pause()
        else:
            print ("toggle_pause_else " + self.current_state())
            self.resume()
        print ("toggle_pause_end " + self.current_state())

    def stop(self, widget, data=None):
        self.stop_timer()
        self.pomodoro.stop()
        self.redraw_menu()

    def start_timer(self):
        self.timer_id = gobject.timeout_add(1000, self.update_timer)
        print ("start_timer " + repr(self.timer_id))

    def stop_timer(self):
        gobject.source_remove(self.timer_id)
        self.timer_id = None

    def main(self):
        gtk.main()

    def quit(self, widget):
        sys.exit(0)

if __name__ == "__main__":
    print __doc__
