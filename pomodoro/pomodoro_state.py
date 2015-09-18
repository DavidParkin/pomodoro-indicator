#!/usr/bin/env python
#-*- coding:utf-8 -*-
import traceback, sys
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
Pomodoro's state machine. Should handle the states, and the maximun
times.
>>> machine = PomodoroMachine()
>>> machine.current_state()
'Waiting'
>>> machine.elapsed_time()
'00:00'
>>> machine.start()
>>> machine.current_state()
'Working'
>>> machine.start()
>>> machine.current_state()
'Working'
>>> machine.next_second()
>>> machine.elapsed_time()
'00:01'
>>> machine.next_second()
>>> machine.elapsed_time()
'00:02'
>>> machine.pause()
>>> machine.current_state()
'Paused'
"""
WAITING_STATE = "waiting"
WORKING_STATE = "working"
RESTING_STATE = "resting"
LONG_RESTING_STATE = "longresting"
PAUSED_STATE = "paused"
MAX_RESTING_TIME = 300
MAX_WORKING_TIME = 1500
AVAILABLE_STATES = [WAITING_STATE, WORKING_STATE, RESTING_STATE, LONG_RESTING_STATE, PAUSED_STATE]


class PomodoroState(object):

    """Base state. This is to share functionality"""

    def current_state(self):
        """Scan the dial to the next station"""
        return self.name

    def enabled_buttons(self):
        pass

    def start(self):
        pass

    def next_state(self):
        pass

    def next_second(self):
        """Returns true if the next second produce a state change."""
        return False

    def pause(self):
        pass

    def resume(self):
        pass

    def stop(self):
        self.pomodoro.state = self.pomodoro.waiting_state
        self.pomodoro.state.elapsed_time = 0

    def working(self):
        return False

    def resting(self):
        return False

    def paused(self):
        return False

    def waiting(self):
        return False

    def longresting(self):
        return False

    def running_next_second(self):
        self.elapsed_time += 1
        if self.elapsed_time >= self.max_time:
            self.next_state()
            self.pomodoro.state.elapsed_time = 0
            return True
        return False

    def pause_it(self):
        self.pomodoro.previous_state = self.pomodoro.state
        self.pomodoro.previous_elapsed_time = self.pomodoro.state.elapsed_time
        self.pomodoro.state = self.pomodoro.paused_state


class WaitingState(PomodoroState):

    """Idle state. When is waiting to start to work."""

    def __init__(self, pomodoro):
        self.pomodoro = pomodoro
        self.elapsed_time = 0
        self.name = WAITING_STATE

    def waiting(self):
        return True

    def start(self):
        self.next_state()

    def next_state(self):
        self.pomodoro.state = self.pomodoro.working_state
        self.pomodoro.state.elapsed_time = 0


class WorkingState(PomodoroState):

    sessions = 0

    """Working state. Should last 25 minutes."""

    def __init__(self, pomodoro, work):
        self.pomodoro = pomodoro
        self.name = WORKING_STATE
        self.max_time = MAX_WORKING_TIME
        self.max_time = work
        self.elapsed_time = 0

    def next_state(self):
        WorkingState.sessions += 1
        print 'Sessions completed ' + repr(WorkingState.sessions)
        if WorkingState.sessions > 3:
            WorkingState.sessions = 0
            self.pomodoro.state = self.pomodoro.longresting_state
        else:
            self.pomodoro.state = self.pomodoro.resting_state

    def pause(self):
        self.pause_it()

    def next_second(self):
        return self.running_next_second()

    def working(self):
        return True


class RestingState(PomodoroState):

    def __init__(self, pomodoro, short):
        self.pomodoro = pomodoro
        self.name = RESTING_STATE
        self.max_time = MAX_RESTING_TIME
        self.max_time = short

    def next_state(self):
        self.pomodoro.state = self.pomodoro.working_state

    def pause(self):
        self.pause_it()

    def next_second(self):
        return self.running_next_second()

    def resting(self):
        return True


class LongRestingState(PomodoroState):

    def __init__(self, pomodoro, longer):
        self.pomodoro = pomodoro
        self.name = LONG_RESTING_STATE
        self.max_time = MAX_RESTING_TIME
        self.max_time = longer

    def next_state(self):
        print "long rest"

        self.pomodoro.state = self.pomodoro.working_state

    def pause(self):
        self.pause_it()

    def next_second(self):
        return self.running_next_second()

    def longresting(self):
        return True


class PausedState(PomodoroState):

    def __init__(self, pomodoro):
        self.pomodoro = pomodoro
        self.elapsed_time = 0
        self.name = PAUSED_STATE

    def resume(self):
        print "paused class"
        self.next_state()

    def next_state(self):
        self.pomodoro.state = self.pomodoro.previous_state
        self.pomodoro.state.elapsed_time = self.pomodoro.previous_elapsed_time

    def paused(self):
        return True


class PomodoroMachine(object):

    def __init__(self, work, short, longer):
        self.waiting_state = WaitingState(self)
        self.working_state = WorkingState(self, work)
        self.resting_state = RestingState(self, short)
        self.longresting_state = LongRestingState(self, longer)
        self.paused_state = PausedState(self)
        self.previous_state = None
        self.previous_elapsed_time = 0
        self.state = self.waiting_state

    def current_state(self):
        return self.state.current_state()

    def in_this_state(self, str_state):
        if hasattr(self.state, str_state):
            return getattr(self.state, str_state)()
        return False

    def elapsed_time(self):
        return self.convert_time(self.state.elapsed_time)

    def start(self):
        self.state.start()

    def stop(self):
        self.state.stop()

    def pause(self):
        self.state.pause()

    def resume(self):
        self.state.resume()

    def next_second(self):
        """Returns true if the next second produce a state change."""
        return self.state.next_second()

    def show_start_button(self):
        return self.state.working()

    def show_stop_button(self):
        return self.state.working() or self.state.resting()  \
            or self.state.paused()

    def show_pause_button(self):
        return self.state.working() or self.state.resting()

    def show_resume_button(self):
        return self.state.paused()

    def convert_time(self, seconds):
        minutes = seconds / 60
        seconds -= minutes * 60
        return "%02d:%02d" % (minutes, seconds)

if __name__ == "__main__":
    print __doc__
