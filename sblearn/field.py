# -*- coding: utf-8 -*-

from entities import *
import pickle
import threading

import cProfile


def profile(func):
    """Decorator for run function profile"""

    def wrapper(*args, **kwargs):
        profile_filename = func.__name__ + '.prof'
        profiler = cProfile.Profile()
        result = profiler.runcall(func, *args, **kwargs)
        profiler.dump_stats(profile_filename)
        return result

    return wrapper


class Field(object):
    def __init__(self, length, height):
        self.__length = length
        self.__height = height
        self.__field = []
        self.__epoch = 0
        self.pause = False

        self.demiurge = None

        for y in range(self.__height):
            row = []
            self.__field.append(row)
            for x in range(self.__length):
                if y == 0 or x == 0 or y == (height - 1) or x == (length - 1):
                    init_object = Block()
                else:
                    init_object = Blank()

                init_object.x = x
                init_object.y = y
                init_object.z = 0

                row.append([init_object])

    @property
    def epoch(self):
        return self.__epoch

    @property
    def length(self):
        return self.__length

    @property
    def height(self):
        return self.__height

    def _get_field(self):
        return self.__field

    def get_cell(self, x, y):
        return self.__field[y][x]

    def cell_passable(self, x, y):
        return self.__field[y][x][-1].passable

    def print_field(self):
        for y in range(self.height):
            row_str = ''
            for element in self.__field[y]:
                row_str += str(element[-1]) + ' '
            print row_str

    def list_str_representation(self):
        representation = []
        for y in range(self.height):
            row_str = ''
            for element in self.__field[y]:
                row_str += str(element[-1])
            representation.append(row_str)
        return representation

    def list_obj_representation(self):
        representation = []
        for y in range(self.height):
            row_list = []
            for cell in self.__field[y]:
                row_list.append(cell[-1])
            representation.append(row_list)
        return representation

    def insert_object(self, x, y, entity_object, epoch_shift=0):
        if self.demiurge is not None:
            refuse = False
            self.demiurge.handle_creation(entity_object, refuse)
            if refuse:
                return

        assert x < self.length
        assert y < self.height

        if self.__field[y][x][-1].scenery:
            self.__field[y][x].append(entity_object)
        else:
            self.__field[y][x][-1] = entity_object

        entity_object.z = self.epoch + epoch_shift

        entity_object.board = self
        entity_object.x = x
        entity_object.y = y

    def remove_object(self, entity_object, x=None, y=None):
        if x is not None and y is not None:
            cell = self.get_cell(x, y)
            cell.remove(entity_object)
        else:
            for row in self.__field:
                for cell in row:
                    if entity_object in cell:
                        cell.remove(entity_object)

    def make_time(self):
        if self.pause:
            return

        for y in range(self.height):
            for x in range(self.length):
                for element in self.__field[y][x]:
                    if element.z == self.epoch:
                        element.live()

        self.__epoch += 1

    def _make_time(self):
        if self.pause:
            return

        threads_list = []

        for y in range(self.height):
            for x in range(self.length):
                for element in self.__field[y][x]:
                    if element.z == self.epoch:
                        threads_list.append(threading.Thread(target=element.live))

        for t in threads_list:
            t.start()

        wait = True

        while wait:
            wait = False
            for t in threads_list:
                if t.isAlive():
                    wait = True
                    continue

        self.__epoch += 1

    def integrity_check(self):
        error_list = []
        # First we check the __field structure
        # and make full list of objects
        objects_full_list = []
        if len(self.__field) != self.height:
            error_str = "Field height ({0}) is not equal to the number of rows({1})".format(self.height,
                                                                                            len(self.__field))
            error_list.append(error_str)
        for y, row in enumerate(self.__field):
            if len(row) != self.length:
                error_str = "Field length ({0}) is not equal to the number of cells ({1}) in row {2}".format(
                    self.height, len(self.__field), y)
                error_list.append(error_str)
            for x, cell in enumerate(row):
                if len(cell) == 0:
                    error_str = "Absolute vacuum (empty list) at coordinates x:{0} y:{1}".format(x, y)
                    error_list.append(error_str)
                for element in cell:
                    objects_full_list.append(element)
                    if element.x != x or element.y != y:
                        error_str = "Object at coordinates x:{0} y:{1} thinks it's at x:{2} y:{3}".format(x, y,
                                                                                                          element.x,
                                                                                                          element.y)
                        error_list.append(error_str)
                    if element.z != self.epoch:
                        error_str = "Object {0} at spacial coordinates x:{1} y:{2} travels in time. Global " \
                                    "epoch: {3}, its local time: {4}".format(str(element), x, y, self.epoch, element.z)
                        error_list.append(error_str)

        # Then we check for object doubles

        for line in error_list:
            print line
        return error_list

    def get_stats(self):
        stats = {}

        for row in self.__field:
            for cell in row:
                for element in cell:
                    class_name = element.class_name()

                    if class_name not in stats:
                        stats[class_name] = 1
                    else:
                        stats[class_name] += 1

        return stats

    def save_pickle(self, filename):
        with open(filename, 'wb') as f:
            pickle.dump(self, f)

    def find_all_coordinates_by_type(self, type_to_find):
        field = self.__field

        list_found = []

        for y, row in enumerate(field):
            for x, cell in enumerate(row):
                for element in cell:
                    if isinstance(element, type_to_find):
                        if (x, y) not in list_found:
                            list_found.append((x, y))
                    if element.contains(type_to_find):
                        if (x, y) not in list_found:
                            list_found.append((x, y))

        return list_found

    def find_all_entities_by_type(self, type_to_find):
        field = self.__field

        list_found = []

        for row in field:
            for cell in row:
                for element in cell:
                    if isinstance(element, type_to_find):
                        if element not in list_found:
                            list_found.append(element)

        return list_found

    def make_path(self, x1, y1, x2, y2):

        if not self.cell_passable(x2, y2):
            return []

        field_map = self.__make_map()
        self.__wave(field_map, x1, y1, x2, y2)

        return self.__find_backwards(field_map, x2, y2)

    def __make_map(self):
        field_map = []

        for input_row in self.__field:
            row = []
            for cell in input_row:
                if cell[-1].passable:
                    row.append(None)
                else:
                    row.append(-1)
            field_map.append(row)

        return field_map

    @staticmethod
    def __wave(field_map, x1, y1, x2, y2):
        current_wave_list = [(x1, y1)]
        field_map[y1][x1] = 0

        while len(current_wave_list) > 0 and field_map[y2][x2] is None:
            next_wave_list = []
            for coordinates in current_wave_list:
                x, y = coordinates
                wave_num = field_map[y][x] + 1

                if (len(field_map) - 1 >= y + 1) and field_map[y + 1][x] is None:
                    field_map[y + 1][x] = wave_num
                    next_wave_list.append((x, y + 1))

                if (y > 0) and field_map[y - 1][x] is None:
                    field_map[y - 1][x] = wave_num
                    next_wave_list.append((x, y - 1))

                if (len(field_map[y]) - 1 >= x + 1) and field_map[y][x + 1] is None:
                    field_map[y][x + 1] = wave_num
                    next_wave_list.append((x + 1, y))

                if (x > 0) and field_map[y][x - 1] is None:
                    field_map[y][x - 1] = wave_num
                    next_wave_list.append((x - 1, y))

            current_wave_list = next_wave_list[:]

    @staticmethod
    def __find_backwards(field_map, x2, y2):
        num_steps = field_map[y2][x2]

        if num_steps is None or num_steps == -1:
            return None

        path = [(x2, y2)]
        num_steps -= 1

        while num_steps > 0:

            x, y = path[-1]

            possible_steps = []

            if (len(field_map) - 1 >= y + 1) and (field_map[y + 1][x] == num_steps):
                possible_steps.append((x, y + 1))
            elif (y > 0) and (field_map[y - 1][x] == num_steps):
                possible_steps.append((x, y - 1))
            elif (len(field_map[y]) - 1 >= x + 1) and (field_map[y][x + 1] == num_steps):
                possible_steps.append((x + 1, y))
            elif (x > 0) and (field_map[y][x - 1] == num_steps):
                possible_steps.append((x - 1, y))

            path.append(random.choice(possible_steps))

            num_steps -= 1

        path.reverse()

        return path

    def coordinates_valid(self, x, y):
        if x < 0 or y < 0:
            return False

        if x >= self.__length or y >= self.__height:
            return False

        return True

    def populate(self, entity_type, number):
        for i in range(number):
            x = random.randint(0, self.length - 1)
            y = random.randint(0, self.height - 1)

            if self.cell_passable(x, y):
                self.insert_object(x, y, entity_type())
            else:
                i -= 1

    def set_demiurge(self, demiurge):
        self.demiurge = demiurge


class Demiurge(object):
    def handle_creation(self, creation, refuse):
        pass


def load_from_pickle(filename):
    with open(filename, 'rb') as f:
        field = pickle.load(f)
    return field
