from datetime import timedelta, date
from enum import Enum


class Period(Enum):
    DAY = 1
    WEEK = 2
    MONTH = 3
    YEAR = 4

    @staticmethod
    def is_last_day_of_month(date_to_test: date) -> bool:
        """
        return true if the date is the last day of the month
        """
        assert date_to_test

        cur_month = date_to_test.month
        plus_day_month = (date_to_test + timedelta(days=1)).month
        return cur_month != plus_day_month

    def next_period(self) -> Enum:
        """
        :return: next largest period unless already is year
        """
        return self if self is Period.YEAR else Period(self.value + 1)

    def is_largest_date_in_period(self, date_to_test: date) -> bool:
        """
        :return: true iff date_to_test is the last day in the period
        """
        if not date_to_test:
            return False
        if self is Period.WEEK:
            return date_to_test.weekday() == 5  # Saturday
        if self is Period.MONTH:
            return Period.is_last_day_of_month(date_to_test)
        if self is Period.YEAR:
            return date_to_test.month == 12 and date_to_test.day == 31

        assert self is Period.DAY
        return True

    def is_start_of_next(self, date_to_test) -> bool:
        """
        :return: true iff date_to_test is the largest date in the next_period()
        """
        if self == Period.YEAR:
            # if the period is a year then it never ends
            return False

        return self.next_period().is_largest_date_in_period(date_to_test)
