# -*- coding: utf-8 -*-

import math
import random

import pandas

import action_library as actions
import brain
import states
import substances


class Entity(object):
    def __init__(self):
        # home universe
        self.board = None

        # time-space coordinates
        self.x = None
        self.y = None
        self.z = None

        # lifecycle properties
        self.age = 0
        self.alive = False
        self.time_of_death = None

        # action queues
        self.action_queue = []
        self.action_log = []

        # common properties
        self.passable = False
        self.scenery = True
        self._container = []
        self._states_list = []

        # visualization properties
        self.color = "#004400"

    def __str__(self):
        raise Exception

    @classmethod
    def class_name(cls):
        return "Entity"

    def live(self):
        self.get_affected()
        self.z += 1
        self.age += 1

    def get_affected(self):
        for state in self._states_list:
            state.affect()

    def has_state(self, state_type):
        for state in self._states_list:
            if isinstance(state, state_type):
                return True
        return False

    def add_state(self, state):
        self._states_list.append(state)

    def remove_state(self, state):
        self._states_list.remove(state)

    def contains(self, substance_type):
        for element in self._container:
            if type(element) == substance_type:
                return True
        return False

    def extract(self, substance_type):
        substance_index = None
        for i, element in enumerate(self._container):
            if type(element) == substance_type:
                substance_index = i
                break
        if substance_index is None:
            return None
        return self._container.pop(substance_index)

    def pocket(self, substance_object):
        if substance_object is not None:
            self._container.append(substance_object)

    def dissolve(self):
        self.board.remove_object(self)

    def find_nearest_coordinates_by_type(self, type_to_find):

        list_found = self.board.find_all_coordinates_by_type(type_to_find)

        smallest_distance = 9e10
        closest_so_far = None

        for coordinates in list_found:
            distance = math.sqrt((self.x - coordinates[0]) ** 2 + (self.y - coordinates[1]) ** 2)
            if distance <= smallest_distance:
                smallest_distance = distance
                closest_so_far = coordinates

        return closest_so_far

    def find_nearest_entity_by_type(self, type_to_find):
        coordinates = self.find_nearest_coordinates_by_type(type_to_find)

        if coordinates is None:
            return None

        cell = self.board.get_cell(**coordinates)

        for element in cell:
            if isinstance(element, type_to_find):
                return element

        return None

    def count_substance_of_type(self, type_of_substance):
        num = 0
        for element in self._container:
            if isinstance(element, type_of_substance):
                num += 1

        return num


class Blank(Entity):
    def __init__(self):
        super(Blank, self).__init__()
        self.passable = True
        self.color = "#004400"

    def __str__(self):
        return '.'

    @classmethod
    def class_name(cls):
        return "Blank"

    def live(self):
        super(Blank, self).live()

        if random.random() <= 0.0004:
            self._container.append(substances.Substance())

        if len(self._container) > 0:
            self.color = "#224444"
        else:
            self.color = "#004400"


class Block(Entity):
    def __init__(self):
        super(Block, self).__init__()
        self.passable = False
        self.color = "#000000"

    def __str__(self):
        return '#'

    @classmethod
    def class_name(cls):
        return "Block"


class Creature(Entity):
    def __init__(self):
        super(Creature, self).__init__()
        self.passable = False
        self.scenery = False
        self.alive = True
        self.name = ''
        self.sex = random.choice([True, False])
        if self.sex:
            self.color = "#550000"
        else:
            self.color = "#990000"
        self.mortal = True
        self.private_learning_memory = brain.LearningMemory(self)
        self.public_memory = None

        self.private_decision_model = None
        self.public_decision_model = None

        self.plan_callable = None

        self.memory_type = ""
        self.model_type = ""

        self.memory_batch_size = 1

        self.memorize_tasks = {}
        self.chosen_action = None

    def __str__(self):
        return '@'

    @classmethod
    def class_name(cls):
        return "Creature"

    def live(self):
        super(Creature, self).live()
        if (self.time_of_death is not None) and self.z - self.time_of_death > 10:
            self.dissolve()
            return

        if not self.alive:
            return

        if random.random() <= 0.001 and self.age > 10:
            self.die()
            return

        if self.need_to_update_plan():
            self.plan()

        if len(self.action_queue) > 0:

            current_action = self.action_queue[0]

            self.perform_action_save_memory(current_action)

            while len(self.action_queue) > 0 and self.action_queue[0].instant:
                current_action = self.action_queue[0]

                self.perform_action_save_memory(current_action)

        self.update_decision_model()

    def set_sex(self, sex):
        self.sex = sex
        if self.sex:
            self.color = "#550000"
        else:
            self.color = "#990000"

    def need_to_update_plan(self):
        return len(self.action_queue) == 0

    def plan(self):

        if self.plan_callable is not None:
            self.plan_callable(self)
            return

    def die(self):
        if not self.mortal:
            return
        self.alive = False
        self.time_of_death = self.z

    def perform_action(self, action):
        results = action.do_results()

        if results["done"] or not action.action_possible():
            self.action_log.append(self.action_queue.pop(0))

        return results

    def perform_action_save_memory(self, action):
        self.chosen_action = action

        if type(action) in self.memorize_tasks:
            results = self.perform_action(action)
            if results["done"]:
                self.private_learning_memory.save_results(self.get_target(type(action)), action)
                self.public_memory.save_results(self.get_target(type(action)), action)
        else:
            results = self.perform_action(action)

        self.chosen_action = None
        return results

    def queue_action(self, action):

        if type(action) in self.memorize_tasks:
            self.private_learning_memory.save_state(self.get_features(type(action)), action)
            self.public_memory.save_state(self.get_features(type(action)), action)

        self.action_queue.append(action)

    def can_mate(self, with_who):
        if isinstance(with_who, Creature):
            if with_who.sex != self.sex:

                if not self.alive or not with_who.alive:
                    return False

                if self.sex:
                    return not with_who.has_state(states.Pregnant)
                else:
                    return not self.has_state(states.Pregnant)

        return False

    def will_mate(self, with_who):
        if not self.can_mate(with_who):
            return False

        if self.sex:
            if self.has_state(states.NotTheRightMood):
                return False
            return True
        else:
            self_has_substance = self.count_substance_of_type(substances.Substance)
            partner_has_substance = with_who.count_substance_of_type(substances.Substance)
            if self_has_substance + partner_has_substance == 0:
                return False
            if self_has_substance <= partner_has_substance:
                return True
            else:
                return random.random() < 1. * partner_has_substance / (self_has_substance*3 + partner_has_substance)

    def update_decision_model(self):
        model_to_use = None
        memory_to_use = None

        if self.memory_type == "public":
            memory_to_use = self.public_memory
        elif self.memory_type == "private":
            memory_to_use = self.private_learning_memory

        if self.model_type == "public":
            model_to_use = self.public_decision_model
        elif self.model_type == "private":
            model_to_use = self.private_decision_model

        if memory_to_use is None or model_to_use is None:
            raise Exception("You should set memory and model types ('public' or 'private')")

        table_list = memory_to_use.make_table(actions.GoMating)
        if len(table_list) >= self.memory_batch_size:
            df_train = pandas.DataFrame(table_list)
            y_train = df_train.pop(len(table_list[0])-1)
            X_train = df_train
            model_to_use.fit(X_train, y_train)
            memory_to_use.obliviate()

    def set_memorize_task(self, action_types, features_list, target):
        if isinstance(action_types, list):
            for action_type in action_types:
                self.memorize_tasks[action_type] = {"features": features_list,
                                                    "target": target}
        else:
            self.memorize_tasks[action_types] = {"features": features_list,
                                                 "target": target}

    def get_features(self, action_type):
        if action_type not in self.memorize_tasks:
            return None

        features_list_raw = self.memorize_tasks[action_type]["features"]
        features_list = []

        for feature_raw in features_list_raw:
            if isinstance(feature_raw, dict):
                if "kwargs" in feature_raw:
                    features_list.append(feature_raw["func"](**feature_raw["kwargs"]))
                else:
                    features_list.append(feature_raw["func"]())
            elif callable(feature_raw):
                features_list.append(feature_raw())
            else:
                features_list.append(feature_raw)

        return features_list

    def get_target(self, action_type):
        if action_type not in self.memorize_tasks:
            return None

        target_raw = self.memorize_tasks[action_type]["target"]

        if callable(target_raw):
            return target_raw()
        elif isinstance(target_raw, dict):
            if "kwargs" in target_raw:
                return target_raw["func"](**target_raw["kwargs"])
            else:
                return target_raw["func"]()
        else:
            return target_raw


class BreedingGround(Entity):
    def __init__(self):
        super(BreedingGround, self).__init__()
        self.passable = True
        self.color = "#000055"

    def __str__(self):
        return "*"

    def live(self):
        super(BreedingGround, self).live()

        if not self.board.cell_passable(self.x, self.y):
            return

        if random.random() < 0.2:
            new_creature = Creature()
            self.board.insert_object(self.x, self.y, new_creature)

    @classmethod
    def class_name(cls):
        return "Breeding ground"
