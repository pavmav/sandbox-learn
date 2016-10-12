# -*- coding: utf-8 -*-

import cProfile
import math
import random

import entities
import states


def profile(func):
    """Decorator for run function profile"""

    def wrapper(*args, **kwargs):
        profile_filename = func.__name__ + '.prof'
        profiler = cProfile.Profile()
        result = profiler.runcall(func, *args, **kwargs)
        profiler.dump_stats(profile_filename)
        return result

    return wrapper


class Action(object):
    def __init__(self, subject):
        self.subject = subject
        self.accomplished = False
        self._done = False
        self.instant = False
        # self.time_start = subject.board.epoch
        # self.time_finish = None

    def get_objective(self):
        return {}

    def set_objective(self, control=False, **kwargs):
        valid_objectives = self.get_objective().keys()

        for key in kwargs.keys():
            if key not in valid_objectives:
                if control:
                    raise ValueError("{0} is not a valid objective".format(key))
                else:
                    pass  # maybe need to print
            else:
                setattr(self, "_{0}".format(key), kwargs[key])

    def action_possible(self):
        return True

    def do(self):
        self.check_set_results()
        self._done = True

    def check_set_results(self):
        self.accomplished = True

    @property
    def results(self):
        out = {"done": self._done, "accomplished": self.accomplished}
        return out

    def do_results(self):
        self.do()
        return self.results


class MovementXY(Action):
    def __init__(self, subject):
        super(MovementXY, self).__init__(subject)

        self._target_x = None
        self._target_y = None

        self.path = []

    def get_objective(self):
        out = {"target_x": self._target_x, "target_y": self._target_y}

        return out

    def action_possible(self):

        if self._target_x is None or self._target_y is None:
            return False

        if self.path is None or len(self.path) == 0:
            self.initialize_path()

        if self.path is None or len(self.path) == 0:
            return False

        return True

    def do(self):

        if self.results["done"]:
            return

        if not self.action_possible():
            return

        if not self.path or not self.check_path_passable():
            self.initialize_path()

        if not self.path:
            self.check_set_results()
            self._done = True
            return

        current_step_x, current_step_y = self.path.pop(0)

        if self.subject.board.cell_passable(current_step_x, current_step_y):
            self.subject.board.remove_object(self.subject, self.subject.x, self.subject.y)
            self.subject.board.insert_object(current_step_x, current_step_y, self.subject, epoch=1)

        self.check_set_results()

        self._done = self.results["accomplished"]

    def check_set_results(self):
        self.accomplished = (self.subject.x == self._target_x and self.subject.y == self._target_y)

    def initialize_path(self):

        self.path = self.subject.board.make_path(self.subject.x, self.subject.y, self._target_x, self._target_y)

    def check_path_passable(self):

        next_step = self.path[0]

        return self.subject.board.cell_passable(next_step[0], next_step[1])


class MovementToEntity(MovementXY):
    def __init__(self, subject):
        super(MovementToEntity, self).__init__(subject)

        self._target_entity = None

    def get_objective(self):
        out = {"target_entity": self._target_entity}

        return out

    def action_possible(self):

        if self._target_entity is None:
            return False

        self.set_target_coordinates()

        if self._target_x is None or self._target_y is None:
            return False

        if self.path is None or len(self.path) == 0:
            self.initialize_path()

        if self.path is None or len(self.path) == 0:
            return False

        return True

    def do(self):

        if self.results["done"]:
            return

        if not self.action_possible():
            return

        self.set_target_coordinates()

        self.initialize_path()

        if not self.action_possible():
            return

        super(MovementToEntity, self).do()

        self.check_set_results()

        self._done = self.results["accomplished"]

    def check_set_results(self):
        if self._target_entity.passable:
            self.accomplished = (self.subject.x == self._target_x and self.subject.y == self._target_y)
        else:
            distance = abs(self.subject.x - self._target_entity.x) + abs(self.subject.y - self._target_entity.y)
            self.accomplished = distance < 2

    def set_target_coordinates(self):
        if self._target_entity.passable:
            self._target_x = self._target_entity.x
            self._target_y = self._target_entity.y
        else:
            cells_near = []
            if self.subject.board.cell_passable(self._target_entity.x, self._target_entity.y + 1):
                cells_near.append((self._target_entity.x, self._target_entity.y + 1))
            if self.subject.board.cell_passable(self._target_entity.x, self._target_entity.y - 1):
                cells_near.append((self._target_entity.x, self._target_entity.y - 1))
            if self.subject.board.cell_passable(self._target_entity.x + 1, self._target_entity.y):
                cells_near.append((self._target_entity.x + 1, self._target_entity.y))
            if self.subject.board.cell_passable(self._target_entity.x - 1, self._target_entity.y):
                cells_near.append((self._target_entity.x - 1, self._target_entity.y))
            if len(cells_near) == 0:
                return

            best_coordinates = random.choice(cells_near)
            smallest_distance = 9e10

            for coordinates in cells_near:
                distance = math.sqrt((self.subject.x - coordinates[0]) ** 2 + (self.subject.y - coordinates[1]) ** 2)

                if distance < smallest_distance:
                    smallest_distance = distance
                    best_coordinates = coordinates

            self._target_x, self._target_y = best_coordinates


class SearchSubstance(Action):
    def __init__(self, subject):
        super(SearchSubstance, self).__init__(subject)

        self.instant = True

        self._target_substance_type = None

        self._substance_x = None
        self._substance_y = None

    def get_objective(self):
        out = {"target_substance_type": self._target_substance_type}

        return out

    def action_possible(self):
        if self._target_substance_type is None:
            return False

        return True

    def do(self):
        if self.results["done"]:
            return

        if not self.action_possible():
            return

        self.search()

        self.check_set_results()
        self._done = True

    def check_set_results(self):
        self.accomplished = (self._substance_x is not None and self._substance_y is not None)

    @property
    def results(self):
        out = super(SearchSubstance, self).results

        out["substance_x"] = self._substance_x
        out["substance_y"] = self._substance_y

        return out

    def search(self):
        current_wave = [(self.subject.x, self.subject.y)]
        checked = {self.subject.x, self.subject.y}

        while current_wave:
            next_wave = []

            for wave_coordinates in current_wave:
                x, y = wave_coordinates
                coordinates_to_check = [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]

                for coordinates in coordinates_to_check:
                    if self.subject.board.coordinates_valid(coordinates[0], coordinates[1]) \
                            and self.subject.board.cell_passable(coordinates[0], coordinates[1]) \
                            and (coordinates[0], coordinates[1]) not in checked:

                        cell = self.subject.board.get_cell(coordinates[0], coordinates[1])

                        for element in cell:
                            if element.contains(self._target_substance_type):
                                self._substance_x, self._substance_y = coordinates
                                return

                        next_wave.append(coordinates)
                        checked.add(coordinates)

            current_wave = next_wave[:]


class SearchMatingPartner(Action):
    def __init__(self, subject):
        super(SearchMatingPartner, self).__init__(subject)

        self.instant = True

        self._partner = None

    def do(self):
        if self.results["done"]:
            return

        if not self.action_possible():
            return

        self.search()

        self.check_set_results()
        self._done = True

    def check_set_results(self):
        self.accomplished = self._partner is not None

    @property
    def results(self):
        out = super(SearchMatingPartner, self).results

        out["partner"] = self._partner

        return out

    def search(self):
        current_wave = [(self.subject.x, self.subject.y)]
        checked = {self.subject.x, self.subject.y}

        height = self.subject.board.height
        length = self.subject.board.length

        while current_wave:
            next_wave = []

            for wave_coordinates in current_wave:
                x, y = wave_coordinates
                coordinates_to_check = [(x + 1, y),
                                        (x - 1, y),
                                        (x, y + 1),
                                        (x, y - 1)]

                for coordinates in coordinates_to_check:
                    if 0 <= coordinates[0] <= length - 1 \
                            and 0 <= coordinates[1] <= height - 1 \
                            and (coordinates[0], coordinates[1]) not in checked:

                        cell = self.subject.board.get_cell(coordinates[0], coordinates[1])

                        for element in cell:
                            if self.subject.can_mate(element):
                                self._partner = element
                                return

                        checked.add(coordinates)
                        if self.subject.board.cell_passable(coordinates[0], coordinates[1]):
                            next_wave.append(coordinates)

            current_wave = next_wave[:]


class ExtractSubstanceXY(Action):
    def __init__(self, subject):
        super(ExtractSubstanceXY, self).__init__(subject)

        self.instant = True

        self._substance_x = None
        self._substance_y = None

        self._substance_type = None

    def get_objective(self):
        out = {"substance_type": self._substance_type, "substance_x": self._substance_x,
               "substance_y": self._substance_y}

        return out

    def action_possible(self):
        if self._substance_x is None or self._substance_y is None or self._substance_type is None:
            return False

        cell_contains_substance = False
        cell = self.subject.board.get_cell(self._substance_x, self._substance_y)
        for element in cell:
            if element.contains(self._substance_type):
                cell_contains_substance = True
                break

        if not cell_contains_substance:
            return False

        x_distance = abs(self._substance_x - self.subject.x)
        y_distance = abs(self._substance_y - self.subject.y)

        if x_distance + y_distance > 1:
            return False

        return True

    def do(self):
        if self.results["done"]:
            return

        if not self.action_possible():
            return

        cell = self.subject.board.get_cell(self._substance_x, self._substance_y)

        extracted = False

        for element in cell:
            if element.contains(self._substance_type):
                self.subject.pocket(element.extract(self._substance_type))
                extracted = True
                break

        if extracted:
            self.check_set_results()

        self._done = True

    def check_set_results(self):
        self.accomplished = True


class Mate(Action):
    def __init__(self, subject):
        super(Mate, self).__init__(subject)

        self.instant = True

        self._target_entity = None

    def get_objective(self):
        out = {"target_entity": self._target_entity}

        return out

    def action_possible(self):
        if self._target_entity is None:
            return False

        if not self.subject.will_mate(self._target_entity) or not self._target_entity.will_mate(self.subject):
            return False

        distance = abs(self.subject.x - self._target_entity.x) + abs(self.subject.y - self._target_entity.y)
        if distance > 1:
            return False

        return True

    def do(self):
        if self.results["done"]:
            return

        if not self.action_possible():
            return

        self._target_entity.add_state(states.Pregnant(self._target_entity))
        self.subject.add_state(states.NotTheRightMood(self.subject))

        self._done = True

        self.check_set_results()

        self._done = self.results["accomplished"]

    def check_set_results(self):
        self.accomplished = self._done


class GiveBirth(Action):
    def __init__(self, subject, pregnant_state):
        super(GiveBirth, self).__init__(subject)

        self.pregnant_state = pregnant_state

    def action_possible(self):
        cells_around = self.get_empty_cells_around()

        if not cells_around:
            return False

        return True

    def do(self):
        if self.results["done"]:
            return

        if not self.action_possible():
            return

        cells_around = self.get_empty_cells_around()

        place = random.choice(cells_around)

        offspring = entities.Creature()

        self.subject.board.insert_object(place[0], place[1], offspring, epoch=1)

        self.subject.remove_state(self.pregnant_state)

        self._done = True

        self.check_set_results()

    def get_empty_cells_around(self):
        cells_near = []

        if self.subject.board.cell_passable(self.subject.x, self.subject.y + 1):
            cells_near.append((self.subject.x, self.subject.y + 1))
        if self.subject.board.cell_passable(self.subject.x, self.subject.y - 1):
            cells_near.append((self.subject.x, self.subject.y - 1))
        if self.subject.board.cell_passable(self.subject.x + 1, self.subject.y):
            cells_near.append((self.subject.x + 1, self.subject.y))
        if self.subject.board.cell_passable(self.subject.x - 1, self.subject.y):
            cells_near.append((self.subject.x - 1, self.subject.y))

        return cells_near


class HarvestSubstance(Action):
    def __init__(self, subject):
        super(HarvestSubstance, self).__init__(subject)

        self._target_substance_type = None

        self.search_action = SearchSubstance(subject)
        self.move_action = MovementXY(subject)
        self.extract_action = ExtractSubstanceXY(subject)

        self.current_action = None

    def get_objective(self):
        out = {"target_substance_type": self._target_substance_type}

        return out

    def set_objective(self, control=False, **kwargs):
        super(HarvestSubstance, self).set_objective(control, **kwargs)

        self.search_action.set_objective(**{"target_substance_type": self._target_substance_type})

        self.current_action = self.search_action

    def action_possible(self):

        if not self.current_action:
            return False

        return self.current_action.action_possible()

    def do(self):
        if self.results["done"]:
            return

        if not self.action_possible():
            return

        first = True

        while first or (self.current_action and self.current_action.instant):
            first = False

            current_results = self.current_action.do_results()

            if current_results["done"]:
                if current_results["accomplished"]:
                    if isinstance(self.current_action, SearchSubstance):
                        self.current_action = self.move_action
                        self.current_action.set_objective(**{"target_x": current_results["substance_x"],
                                                             "target_y": current_results["substance_y"]})
                    elif isinstance(self.current_action, MovementXY):
                        self.current_action = self.extract_action
                        self.current_action.set_objective(**{"substance_x": self.subject.x,
                                                             "substance_y": self.subject.y,
                                                             "substance_type": self._target_substance_type})
                    elif isinstance(self.current_action, ExtractSubstanceXY):
                        self.current_action = None
                        self._done = True
                else:
                    self.current_action = None
                    self._done = True
            else:
                break

    def check_set_results(self):
        self.accomplished = self._done


class GoMating(Action):
    def __init__(self, subject):
        super(GoMating, self).__init__(subject)

        self.search_action = SearchMatingPartner(subject)
        self.move_action = MovementToEntity(subject)
        self.mate_action = Mate(subject)

        self.current_action = self.search_action

    def action_possible(self):

        if not self.current_action:
            return False

        return self.current_action.action_possible()

    def do(self):
        if self.subject.has_state(states.NotTheRightMood):
            self._done = True
            return

        if self.results["done"]:
            return

        if not self.action_possible():
            self._done = True
            return

        first = True

        while first or (self.current_action and self.current_action.instant) and not self.results["done"]:

            first = False

            current_results = self.current_action.do_results()

            if current_results["done"]:
                if current_results["accomplished"]:
                    if isinstance(self.current_action, SearchMatingPartner):
                        if current_results["accomplished"]:
                            self.current_action = self.move_action
                            self.current_action.set_objective(**{"target_entity": current_results["partner"]})
                    elif isinstance(self.current_action, MovementXY):
                        self.current_action = self.mate_action
                        self.current_action.set_objective(**{"target_entity": self.search_action.results["partner"]})
                    elif isinstance(self.current_action, Mate):
                        self.current_action = None
                        self.accomplished = True
                        self._done = True
                else:
                    self.current_action = None
                    self._done = True
            else:
                break

    def check_set_results(self):
        self.accomplished = self._done


def divide(x, y):
    return x / y
