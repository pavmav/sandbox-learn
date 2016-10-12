# -*- coding: utf-8 -*-
import unittest


class LearningMemory(object):
    def __init__(self, host):
        self.host = host
        self.memories = {}

    def save_state(self, state, action):
        self.memories[action] = {"state": state}

    def save_results(self, results, action):
        if action in self.memories:
            self.memories[action]["results"] = results
        else:
            pass

    def make_table(self, action_type):
        table_list = []
        for memory in self.memories:
            if isinstance(memory, action_type):
                if "state" not in self.memories[memory] or "results" not in self.memories[memory]:
                    continue
                row = self.memories[memory]["state"][:]
                row.append(self.memories[memory]["results"])
                table_list.append(row)

        return table_list

    def obliviate(self):
        self.memories = {}


class TestLearningMemory(unittest.TestCase):
    def setUp(self):
        self.mem = LearningMemory(None)

    def test_init(self):
        self.assertTrue(self.mem.host is None)

    def test_save_state(self):
        self.mem.save_state({"foo": 1, "bar": 2}, 12)
        self.mem.save_state({"foo": 6, "bar": 4}, 65)
        self.mem.save_state({"spam": 1, "eggs": 2, "time": 55}, "42")

        self.assertEqual(self.mem.memories, {12: {'state': {'foo': 1, 'bar': 2}},
                                             65: {'state': {'foo': 6, 'bar': 4}},
                                             "42": {'state': {"spam": 1, "eggs": 2, "time": 55}}})

    def test_save_results(self):
        self.mem.save_state({"foo": 1, "bar": 2}, 12)
        self.mem.save_state({"foo": 6, "bar": 4}, 65)
        self.mem.save_state({"spam": 1, "eggs": 2, "time": 55}, "42")

        results = {"done": True, "accomplished": False}

        self.mem.save_results(results, 65)

        self.assertEqual(self.mem.memories, {12: {'state': {'foo': 1, 'bar': 2}},
                                             65: {'state': {'foo': 6, 'bar': 4},
                                                  'results': False},
                                             "42": {'state': {"spam": 1, "eggs": 2, "time": 55}}})

        self.assertRaises(ValueError, self.mem.save_results, **{"results": results,
                                                                "action": 88})

    def test_make_table(self):
        self.mem.save_state([1, 2], 12)
        self.mem.save_state([6, 4], 65)
        self.mem.save_state([1, 2, 55], "42")
        results = {"done": True, "accomplished": False}
        self.mem.save_results(results, 65)
        results = {"done": True, "accomplished": True}
        self.mem.save_results(results, 12)

        print self.mem.make_table(int)

        self.assertEqual(self.mem.make_table(int), [[6, 4, False],
                                                    [1, 2, True]])


if __name__ == '__main__':
    unittest.main()
