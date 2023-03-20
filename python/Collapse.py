import argparse
import logging
import os
import re
import shutil
from datetime import datetime, date
from os import path
from os.path import join
from re import Pattern
from typing import AnyStr, List, Union

from CalendarSlice import CalendarSlice


class Collapse:
    """
    Utility class to collapse directory by calender periods

    TODO explain dates etc
    """

    def __init__(self, pretend_mode, verbose_mode):

        # if pretend_mode then do not actually collapse
        self.pretend_mode = pretend_mode
        self.verbose_mode = verbose_mode

        # Match the date part of directories to be collapsed
        # Match year-month-day where year is two or four digits and day and month are one or two
        matching_pattern = r"(\d{4}|\d{2})-(\d{2}|\d)-(\d{2}|\d{1})"

        self.matching_regex = re.compile(
            matching_pattern, re.MULTILINE | re.IGNORECASE | re.VERBOSE)

        # Extract the date from strings matching the matching_pattern
        self.extract_match = "%Y-%m-%d"

        # Used to create a collapsed directory for a specific date
        self.period_destination = "%Y-%m-%d"

    @staticmethod
    def find_regex(content: str, regex: Pattern[AnyStr]) -> Union[AnyStr, None]:
        """
        Searches through the content and returns the first pattern matched by the regex .
        Returns None if not found or more than one match found
        """
        assert regex

        result = None
        for match in regex.finditer(content):
            if result is None:
                result = match.group()
            else:
                # This must be 2nd match
                result = None
                break

        return result

    @staticmethod
    def path_type(dir_path: AnyStr) -> AnyStr:
        """
        Validates that the dir_path exists and is a directory.

        throws an ArgumentTypeError if the dir_path is not valid.

        :param dir_path: item to check
        :return: the validated dir_path
        """
        if os.path.isdir(dir_path):
            return dir_path
        else:
            raise argparse.ArgumentTypeError(
                f"readable_dir:{dir_path} is not a valid path")

    def date_from_dir(self, dir_name: str) -> Union[date, None]:
        """
        Use the matching_pattern to extract the date from a directory name
        """
        match = Collapse.find_regex(dir_name, self.matching_regex)
        return datetime.strptime(match, self.extract_match).date() if match else None

    def sliced_directories(self, dir_list: List[str]) -> list[tuple[str, List[str]]]:
        """
        Slice the dir_list into time periods according to the dates embedded in the top level
        directory names.  The newest slices always starts at the current date.

        Only directories that match the matching_pattern are returned

        :param dir_list: list of directories to be put into calendar slices
        :return: list of tuples with directory and list of dir_list items that belong in the
        directory.  The directory name will match the period_destination.
        """

        assert dir_list

        # list of (datetime, directory)
        date_dirs = []
        oldest = None
        current_date = datetime.now().date()

        for dir_name in dir_list:
            dir_date = self.date_from_dir(dir_name)
            if dir_date:
                date_dirs.append((dir_date, dir_name))
                if not oldest or dir_date < oldest:
                    oldest = dir_date
                if dir_date > current_date:
                    logging.debug(
                        f"Current date in the future ({current_date})")
                    current_date = dir_date

        if len(date_dirs) == 0:
            # no directories that match the matching_pattern found
            return []

        # Get calendar slices sorted newest to oldest
        cal_slices = CalendarSlice.get_calendar_slices(current_date, oldest)

        # Sorted newest to oldest
        date_dirs = sorted(date_dirs, key=lambda dd: dd[0], reverse=True)
        dd_iter = iter(date_dirs)
        # assert dd_iter has at least one item
        dir_date, dir_name = next(dd_iter)
        logging.debug(f"dd_iter {dir_date}, {dir_name}")

        if logging.root.level <= logging.DEBUG:
            logging.debug(
                f'Slices: {", ".join([s.__str__() for s in cal_slices])}')

        slice_dirs = []
        for cal_slice in cal_slices:
            logging.debug(f"Filling slice: {cal_slice}")
            current_dirs = []
            while cal_slice.contains(dir_date):
                current_dirs.append(dir_name)
                logging.debug(f"Adding {dir_date} to {cal_slice}")
                try:
                    dir_date, dir_name = next(dd_iter)
                    logging.debug(f"dd_iter {dir_date}, {dir_name}")
                except StopIteration:
                    # Nothing left in dd_iter so break
                    break

            if len(current_dirs) > 0:
                # assert current_dirs is already sorted
                assert current_dirs == sorted(
                    current_dirs, key=lambda dn: self.date_from_dir(dn), reverse=True)

                period_directory = cal_slice.end.strftime(
                    self.period_destination)
                slice_dirs.append((period_directory, current_dirs))

        # dd_iter has reached StopIteration
        assert next(dd_iter, None) is None, "dd_iter should have been empty"
        return slice_dirs

    def rename_path(self, source: AnyStr, destination: AnyStr):
        """
        Move source to destination.

        :param source: Must exist
        :param destination: Must not exists
        """
        assert path.exists(source), f"{source} should exist"
        assert not path.exists(destination), f"{destination} should not exist"

        logging.info(f'shutil.move("{source}", "{destination}")')

        if self.verbose_mode:
            print(f'shutil.move("{source}", "{destination}") # Rename')
        if not self.pretend_mode:
            shutil.move(source, destination)

    def move_and_delete(self, source: str, destination: str):
        # print('move_and_delete("%s", "%s")' % (source, destination))
        source_exists = path.exists(source)
        dest_exists = path.exists(destination)

        source_is_dir = path.isdir(source)
        dest_is_dir = path.isdir(destination)

        if not source_exists:
            raise FileNotFoundError(f'"{source}" is not found')

        if dest_exists and not dest_is_dir:
            raise NotImplementedError(f'"{source}" must be a directory')

        if source == destination:
            # nothing to do
            logging.debug(
                f"move and delete where destination = source({source}")
            assert source_is_dir == dest_is_dir
        elif not dest_exists:
            # rename source to destination
            self.rename_path(source, destination)
        elif not source_is_dir:
            # move source file into destination directory
            self.rename_path(source, join(destination, source))
        else:
            # move contents of source into destination
            assert source_exists
            assert source_is_dir
            assert dest_exists
            assert dest_is_dir

            logging.debug(f"Move dir {source} into dir {destination}")

            # want to move the items in source into destination
            to_process = os.listdir(source)

            while len(to_process):
                current = to_process.pop(0)
                cur_full = path.join(source, current)
                assert path.exists(cur_full), f'"{cur_full}" should exist'

                dest_full = join(destination, current)

                if not path.exists(dest_full):
                    self.rename_path(cur_full, dest_full)
                elif path.isdir(cur_full):
                    for item in os.listdir(cur_full):
                        to_process.append(join(current, item))
                elif self.verbose_mode:
                    print(f'Skipped (exist) "{cur_full}"')

            # delete using current information
            if path.exists(source):
                if path.isdir(source):
                    if self.verbose_mode:
                        print(f'Remove Directory "{source}"')
                    if not self.pretend_mode:
                        shutil.rmtree(source)
                else:
                    if self.verbose_mode:
                        print('os.remove("%s")' % source)
                    if not self.pretend_mode:
                        os.remove(source)

    def collapse_directories(self, dir_list: List[str]):
        """
        Slice up the directories in the dir_list and collapse each slice into a single directory
        """
        sliced_dirs = self.sliced_directories(dir_list)

        for destination, dir_names in sliced_dirs:
            for dir_name in dir_names:
                if dir_name != destination:
                    logging.debug(f"move {dir_name} to {destination}")
                    self.move_and_delete(dir_name, destination)

    def collapse(self, dir_to_collapse: str):
        if not path.exists(dir_to_collapse):
            raise FileNotFoundError("%s does not exists" % dir_to_collapse)

        if not path.isdir(dir_to_collapse):
            raise NotImplementedError(
                "%s must be a directory" % dir_to_collapse)

        current_directory = os.getcwd()
        os.chdir(dir_to_collapse)
        logging.debug(f"Changed to {dir_to_collapse}")
        try:
            dirs = os.listdir(".")
            self.collapse_directories(dirs)
        finally:
            if current_directory != dir_to_collapse:
                os.chdir(current_directory)
                logging.debug(f"Changed back to {current_directory}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(usage='%(prog)s [options] path to collapse',
                                     description='Collapse directory by days, weeks, months and years')

    parser.add_argument('-n', '--pretend',
                        action='store_true',
                        help='Do not actually collapse')

    parser.add_argument('-v', '--verbose',
                        action='store_true',
                        help='Turn on verbose output')

    parser.add_argument('path',
                        help='Base Directory with directories to collapse',
                        type=Collapse.path_type
                        )

    parser.add_argument('--loglevel',
                        choices=['critical', 'error',
                                 'warning', 'info', 'debug'],
                        type=str.lower,
                        help='Set logging level. Example --loglevel debug')

    parser.usage = parser.format_help()
    args = parser.parse_args()

    if args.loglevel:
        logging.basicConfig(level=args.loglevel.upper())
        logging.info(f"Logging set to {args.loglevel.upper()}")

    c = Collapse(pretend_mode=args.pretend,
                 verbose_mode=args.verbose or args.pretend)
    to_collapse = args.path
    if not to_collapse:
        parser.error("A directory to collapse is required and must exists")

    logging.debug(
        "Collapse, Pretend Mode {c.pretend_mode}, Verbose Mode {c.verbose_mode}, Directory {dir_to_collapse}")

    if c.pretend_mode or c.verbose_mode:
        print("Pretend mode (no actions will be performed)" if c.pretend_mode
              else "Real mode (directory will be collapsed)")

    c.collapse(to_collapse)
