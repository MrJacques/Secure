from __future__ import annotations

import logging
from datetime import timedelta, date

from CalendarPeriod import Period


class CalendarSlice:
    """
    Each CalendarSlice has a start and end date (day).

    start <= end. Immutable.

    """

    def __init__(self, start: date, end: date):
        assert start is not None
        assert end is not None
        assert start <= end

        self._start = start
        self._end = end

    @property
    def start(self) -> date:
        return self._start

    @property
    def end(self) -> date:
        return self._end

    def contains(self, date_to_test: date) -> bool:
        """
        Returns true if start < date_to_test <= end
        """
        return self.start <= date_to_test <= self.end if date_to_test else None

    def __str__(self):
        if (self.end - self.start).days < 2:
            return "Slice(" + self.start.strftime("%Y-%m-%d") + ")"
        else:
            return "Slice(" + self.start.strftime("%Y-%m-%d") + ", " + self.end.strftime("%Y-%m-%d") + ")"

    @staticmethod
    def get_calendar_slices(date_newest: date,
                            date_oldest: date,
                            min_days: int = 7,
                            min_weeks: int = 4,
                            min_months: int = 12) -> list[CalendarSlice]:
        """
        This breaks up a date range into "slices".  The slices will start as individual days, then
        progress to weekly, monthly and finally yearly slices.

        Given a large enough date range, it will create min_days daily slices followed by however many
        days are needed to get to a Saturday.  Then weekly slices until min_weeks has been reached and
        then continue with weekly slices until the end of a month is reached.  Same thing with months,
        and then years.

        e.g. If newest_date was a Friday, then it would iterate over the date range backwards from Friday
        creating slices until min_days slices has been created.  It would then continue iterating backwards
        until

        :param date_newest: date to start slices at
        :param date_oldest: date to end slices at
        :param min_days: minimum number of daily slices to create before changing to weekly slices
        :param min_weeks: minimum number of weekly slices to create before changing to monthly slices
        :param min_months: minimum number of monthly slices to create before changing to yearly.
        :return: Ordered list of CalendarSlice's
        """

        period_minimums = {
            Period.DAY: min_days,
            Period.WEEK: min_weeks,
            Period.MONTH: min_months
        }

        logging.debug(
            f"get_calendar_slices, newest {date_newest}, oldest {date_oldest}")
        logging.debug(
            f"Periods Days {min_days}, Weeks {min_weeks}, Months {min_months}")

        slice_boundaries = []
        cur_date = date_newest
        current_period = Period.DAY
        slices_in_period = 0

        while cur_date >= date_oldest:
            is_largest_in_period = current_period.is_largest_date_in_period(
                cur_date)
            is_new_period = current_period.is_start_of_next(cur_date)

            if is_largest_in_period or is_new_period:
                slice_boundaries.append(cur_date)
                slices_in_period += 1

            if is_new_period and slices_in_period >= period_minimums[current_period]:
                current_period = current_period.next_period()
                slices_in_period = 0

            cur_date -= timedelta(days=1)

        slice_boundaries.append(date_oldest - timedelta(days=1))
        slices = []
        prev_boundary = None
        for b in slice_boundaries:
            if prev_boundary:
                slices.append(CalendarSlice(
                    b + timedelta(days=1), prev_boundary))
                logging.debug(slices[-1])
            prev_boundary = b

        return slices


# newest = date(2021, 6, 23)
# oldest = date(2017, 6, 22)
# the_slices = CalendarSlice.get_calendar_slices(newest, oldest)
#
# for s in the_slices:
#     print(s)
