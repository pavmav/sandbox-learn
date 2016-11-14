import random

import numpy as np
from sklearn.exceptions import NotFittedError
from sklearn.linear_model import SGDClassifier

from sblearn import action_library as actions
from sblearn import brain
from sblearn import entities
from sblearn import field
from sblearn import states
from sblearn import substances
from sblearn import visualization
from sblearn import modelling


# Create deity
class Priapus(field.Demiurge):  # Create deity
    def __init__(self):
        self.public_memory = brain.LearningMemory(self)
        self.public_decision_model = SGDClassifier(warm_start=True)

    def handle_creation(self, creation, refuse):
        if isinstance(creation, entities.Creature):
            creation.public_memory = self.public_memory
            creation.public_decision_model = self.public_decision_model
            creation.memory_type = "public"
            creation.model_type = "public"
            creation.memory_batch_size = 20

            if creation.sex:
                def difference_in_num_substance(entity):
                    nearest_partner = actions.SearchMatingPartner(entity).do_results()["partner"]
                    if nearest_partner is None:
                        return 9e10
                    else:
                        self_has_substance = entity.count_substance_of_type(substances.Substance)
                        partner_has_substance = nearest_partner.count_substance_of_type(substances.Substance)
                        return partner_has_substance - self_has_substance


                def possible_partners_exist(entity):
                    find_partner = actions.SearchMatingPartner(entity)
                    search_results = find_partner.do_results()
                    return float(search_results["accomplished"])

                features = [{"func": lambda creation: float(creation.has_state(states.NotTheRightMood)),
                             "kwargs": {"creation": creation}},
                            {"func": difference_in_num_substance,
                             "kwargs": {"entity": creation}},
                             {"func": possible_partners_exist,
                              "kwargs": {"entity": creation}}]

                creation.set_memorize_task(actions.GoMating, features,
                                           {"func": lambda creation: creation.chosen_action.results["accomplished"],
                                            "kwargs": {"creation": creation}})

            def plan(creature):
                if creature.sex:
                    try:
                        # raise NotFittedError
                        current_features = creature.get_features(actions.GoMating)
                        current_features = np.asarray(current_features).reshape(1, -1)
                        if creature.public_decision_model.predict(current_features):
                            go_mating = actions.GoMating(creature)
                            creature.queue_action(go_mating)
                            return
                        else:
                            harvest_substance = actions.HarvestSubstance(creature)
                            harvest_substance.set_objective(
                                **{"target_substance_type": type(substances.Substance())})
                            creature.queue_action(harvest_substance)
                            return
                    except NotFittedError:
                        chosen_action = random.choice(
                            [actions.GoMating(creature), actions.HarvestSubstance(creature)])
                        if isinstance(chosen_action, actions.HarvestSubstance):
                            chosen_action.set_objective(
                                **{"target_substance_type": type(substances.Substance())})
                        creature.queue_action(chosen_action)
                        return
                else:
                    harvest_substance = actions.HarvestSubstance(creature)
                    harvest_substance.set_objective(**{"target_substance_type": type(substances.Substance())})
                    creature.queue_action(harvest_substance)

            creation.plan_callable = plan


universe = field.Field(60, 40)  # Create sample universe (length, height)

universe.set_demiurge(Priapus())  # Assign deity to universe

# Fill universe with blanks, blocks, other scenery if necessary
for y in range(10, 30):
    universe.insert_object(20, y, field.Block())

for x in range(21, 40):
    universe.insert_object(x, 10, field.Block())

for y in range(10, 30):
    universe.insert_object(40, y, field.Block())

universe.populate(entities.Creature, 20)  # Populate universe with creatures

visualization.visualize(universe)


def check_stop_function(field):
    return field.epoch >= 500


def score_function(field):
    stats = field.get_stats()
    if "Creature" not in stats:
        return 0
    else:
        return stats["Creature"]

# res = modelling.run_simulation(universe, check_stop_function, score_function, verbose=True, times=30)
# print res
# print np.asarray(res).mean()

# random 1000 10 [193, 37, 97, 224, 349, 165, 251, 130, 184, 335]
# SGDClassifier 1000 10 [9, 106, 127, 11, 187, 38, 193, 114, 236, 27]

# random 500 20 [63, 24, 38, 14, 30, 65, 29, 60, 28, 25, 93, 44, 51, 26, 104, 56, 53, 38, 23, 42] mean 45.299999999999997
# SGDClassifier 500 20 [116, 52, 50, 82, 109, 49, 109, 37, 25, 115, 130, 180, 52, 52, 113, 46, 34, 135, 26, 33] mean 77.25

# random 500 20 [71, 24, 57, 56, 34, 14, 75, 66, 41, 56, 29, 69, 30, 72, 40, 57, 49, 24, 41, 48] mean 47.65
# SGDClassifier 500 20 [175, 40, 117, 96, 119, 116, 58, 134, 67, 87, 73, 147, 124, 125, 82, 139, 78, 110, 74, 100] mean 103.05

# random 500 30 [42, 32, 62, 34, 30, 44, 51, 35, 63, 59, 50, 40, 75, 59, 50, 33, 45, 95, 82, 41, 43, 89, 94, 66, 64, 46, 34, 82, 66, 76]
# 56.0666666667
# SGDClassifier 500 30 [62, 85, 72, 42, 17, 48, 74, 53, 42, 73, 57, 29, 82, 51, 80, 84, 86, 73, 51, 36, 85, 85, 46, 59, 68, 33, 44, 38, 62, 26]
# 58.1




