from datetime import datetime, timedelta
from unittest import TestCase

from CalendarPeriod import Period


class TestPeriod(TestCase):
    def test_is_last_day_of_month(self):
        date = datetime(1999, 1, 1)
        end_date = datetime(2050, 12, 31)

        while date < end_date:
            if date.month in (1, 3, 5, 7, 8, 10, 12):
                last = 31
            elif date.month == 2:
                last = 28 if date.year % 4 else 29
            else:
                last = 30
            expected = date.day == last
            self.assertEqual(Period.is_last_day_of_month(date), expected,
                             "%s should be %r" % (date.strftime("%y/%m/%d"), expected))

            # print(date, Period.is_last_day_of_month(date), expected )
            date += timedelta(days=1)

    def test_next_period(self):
        self.assertEqual(Period.DAY.next_period(), Period.WEEK, "DAY")
        self.assertEqual(Period.WEEK.next_period(), Period.MONTH, "WEEK")
        self.assertEqual(Period.MONTH.next_period(), Period.YEAR, "MONTH")
        # self.assertEqual(Period.YEAR.next_period(), Period.YEAR, "YEAR")

        names = [e.value for e in Period]
        self.assertEqual(len(names), 4, "Only expected 4 values in Period")

    def test_is_largest_date_in_period(self):
        date = datetime(1999, 1, 1)
        end_date = datetime(2050, 12, 31)

        while date < end_date:
            if date.month in (1, 3, 5, 7, 8, 10, 12):
                last = 31
            elif date.month == 2:
                last = 28 if date.year % 4 else 29
            else:
                last = 30
            last_day_in_month = date.day == last
            self.assertTrue(Period.DAY.is_largest_date_in_period(date),
                            "%s DAY should always be largest" % date.strftime("%y/%m/%d"))

            self.assertEqual(Period.WEEK.is_largest_date_in_period(date), date.weekday() == 5,
                             "%s WEEK ends on Saturday" % date.strftime("%y/%m/%d"))

            self.assertEqual(Period.MONTH.is_largest_date_in_period(date), last_day_in_month,
                             "%s MONTH last day" % date.strftime("%y/%m/%d"))

            self.assertEqual(Period.YEAR.is_largest_date_in_period(date), date.month == 12 and date.day == 31,
                             "%s YEAR last day" % date.strftime("%y/%m/%d"))

            # print(date, Period.is_last_day_of_month(date), expected )
            date += timedelta(days=1)

    def test_start_of_next(self):
        date = datetime(1999, 1, 1)
        end_date = datetime(2050, 12, 31)

        while date < end_date:
            if date.month in (1, 3, 5, 7, 8, 10, 12):
                last = 31
            elif date.month == 2:
                last = 28 if date.year % 4 else 29
            else:
                last = 30
            last_day_in_month = date.day == last
            self.assertEqual(Period.DAY.is_start_of_next(date), date.weekday() == 5,
                             "%s WEEK ends on Saturday" % date.strftime("%y/%m/%d"))

            self.assertEqual(Period.WEEK.is_start_of_next(date), last_day_in_month,
                             "%s MONTH last day" % date.strftime("%y/%m/%d"))

            self.assertEqual(Period.MONTH.is_start_of_next(date), date.month == 12 and date.day == 31,
                             "%s YEAR last day" % date.strftime("%y/%m/%d"))

            self.assertFalse(Period.YEAR.is_start_of_next(
                date), "%s YEAR is always false" % date.strftime("%y/%m/%d"))

            # print(date, Period.is_last_day_of_month(date), expected )
            date += timedelta(days=1)
