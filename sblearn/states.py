# -*- coding: utf-8 -*-

import action_library as actions


class State(object):
    def __init__(self, subject):
        self.subject = subject
        self.duration = 0

    def affect(self):
        self.duration += 1


class Pregnant(State):
    def __init__(self, subject):
        super(Pregnant, self).__init__(subject)

        self.timing = 15

    def affect(self):
        super(Pregnant, self).affect()

        if self.duration == self.timing:
            self.subject.action_queue.insert(0, actions.GiveBirth(self.subject, self))


class NotTheRightMood(State):
    def __init__(self, subject):
        super(NotTheRightMood, self).__init__(subject)

        self.timing = 10

    def affect(self):
        super(NotTheRightMood, self).affect()

        if self.duration == self.timing:
            self.subject.remove_state(self)
