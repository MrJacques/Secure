from datetime import datetime, timedelta
from unittest import TestCase

from CalendarSlice import CalendarSlice


class Test(TestCase):
    def test_calendar_slice(self):
        start = datetime(2020, 6, 1)
        end = datetime(2020, 6, 15)
        one_day = timedelta(days=1)

        cs = CalendarSlice(start, end)
        self.assertEqual(cs.start, start)
        self.assertEqual(cs.end, end)

        self.assertFalse(cs.contains(start - one_day))
        self.assertTrue(cs.contains(start))
        self.assertTrue(cs.contains(start + one_day))

        date = start + one_day
        while date <= end:
            self.assertTrue(cs.contains(date))
            date += one_day

        self.assertFalse(cs.contains(end + one_day))

        self.assertEqual(str(cs), "Slice(2020-06-01, 2020-06-15)")

    def test_slicer(self):
        newest = datetime(2021, 6, 23)
        oldest = datetime(2017, 6, 22)
        the_slices = CalendarSlice.get_calendar_slices(newest, oldest)

        actual = []
        for s in the_slices:
            actual.append(str(s))

        expected = ["Slice(2021-06-23)",
                    "Slice(2021-06-22)",
                    "Slice(2021-06-21)",
                    "Slice(2021-06-20)",
                    "Slice(2021-06-19)",
                    "Slice(2021-06-18)",
                    "Slice(2021-06-17)",
                    "Slice(2021-06-16)",
                    "Slice(2021-06-15)",
                    "Slice(2021-06-14)",
                    "Slice(2021-06-13)",
                    "Slice(2021-06-06, 2021-06-12)",
                    "Slice(2021-06-01, 2021-06-05)",
                    "Slice(2021-05-30)",
                    "Slice(2021-05-23, 2021-05-29)",
                    "Slice(2021-05-16, 2021-05-22)",
                    "Slice(2021-05-09, 2021-05-15)",
                    "Slice(2021-05-02, 2021-05-08)",
                    "Slice(2021-05-01)",
                    "Slice(2021-04-01, 2021-04-30)",
                    "Slice(2021-03-01, 2021-03-31)",
                    "Slice(2021-02-01, 2021-02-28)",
                    "Slice(2021-01-01, 2021-01-31)",
                    "Slice(2020-12-01, 2020-12-31)",
                    "Slice(2020-11-01, 2020-11-30)",
                    "Slice(2020-10-01, 2020-10-31)",
                    "Slice(2020-09-01, 2020-09-30)",
                    "Slice(2020-08-01, 2020-08-31)",
                    "Slice(2020-07-01, 2020-07-31)",
                    "Slice(2020-06-01, 2020-06-30)",
                    "Slice(2020-05-01, 2020-05-31)",
                    "Slice(2020-04-01, 2020-04-30)",
                    "Slice(2020-03-01, 2020-03-31)",
                    "Slice(2020-02-01, 2020-02-29)",
                    "Slice(2020-01-01, 2020-01-31)",
                    "Slice(2019-01-01, 2019-12-31)",
                    "Slice(2018-01-01, 2018-12-31)",
                    "Slice(2017-06-22, 2017-12-31)"]

        self.assertListEqual(actual, expected)
