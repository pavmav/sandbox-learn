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

                def nearest_partner_has_substance(entity):
                    return float(actions.SearchMatingPartner(entity).do_results()["partner"].count_substance_of_type(
                        substances.Substance))

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
                            # {"func": lambda creation: float(creation.count_substance_of_type(substances.Substance)),
                            #  "kwargs": {"creation": creation}},
                             {"func": possible_partners_exist,
                              "kwargs": {"entity": creation}}]

                creation.set_memorize_task(actions.GoMating, features,
                                           {"func": lambda creation: creation.chosen_action.results["accomplished"],
                                            "kwargs": {"creation": creation}})

            def plan(creature):
                if creature.sex:
                    try:
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


universe = field.Field(60, 40)  # Create sample universe (length, height

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
