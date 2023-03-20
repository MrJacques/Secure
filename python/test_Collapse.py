from datetime import date
from unittest import TestCase

from Collapse import Collapse


class Test(TestCase):
    def test_find_regex(self):
        c = Collapse(False, False)
        self.assertEqual(Collapse.find_regex(
            "2021-02-14", c.matching_regex), "2021-02-14")
        self.assertEqual(Collapse.find_regex(
            "2021-2-4", c.matching_regex), "2021-2-4")
        self.assertIsNone(Collapse.find_regex("2021-222-4", c.matching_regex))
        self.assertIsNone(Collapse.find_regex(
            "2021-2-4 2021-02-01", c.matching_regex))

    def test_date_from_dir(self):
        c = Collapse(False, False)
        expected_date = date(2021, 2, 4)
        self.assertEqual(c.date_from_dir("2021-02-04"), expected_date)
        self.assertEqual(c.date_from_dir("2021-2-4"), expected_date)
        self.assertNotEqual(c.date_from_dir("2021-2-5"), expected_date)

    def test_sliced_directories(self):
        c = Collapse(False, False)
        dirs = ["2021-06-23", "2021-6-22", "2017-12-04", "2017-12-03"]
        sd = c.sliced_directories(dirs)
        actual = []
        for pd, dns in sd:
            actual.append("Collapse in %s" % pd)
            for dn in dns:
                actual.append(dn)

        expected = ["Collapse in 2021-06-23",
                    "2021-06-23",
                    "Collapse in 2021-06-22",
                    "2021-6-22",
                    "Collapse in 2017-12-31",
                    "2017-12-04", "2017-12-03"]

        self.assertListEqual(actual, expected)

    # def test_collapse_directories(self):
    #     self.fail()
