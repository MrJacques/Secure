import argparse
import hashlib
import logging
import os
import shutil
from os import scandir
from os.path import join
from typing import AnyStr, List, Dict, Set, Callable, TypeVar


class FileInfo:
    """
    Convenient class to associate information with a file.

    Breaks the path up into base directory, rest of the path and file name.

    The md5 property is lazy in that it is only calculated when requested.
    """

    def __init__(self, base_dir: AnyStr, file_dir: AnyStr, file_name: AnyStr, file_size: int = None):
        self._full_name = join(base_dir, file_dir, file_name)
        assert os.path.exists(self._full_name)
        assert not os.path.isdir(self._full_name)

        self._base_dir = base_dir
        self._file_dir = file_dir
        self._file_name = file_name
        self._size = file_size
        self._md5 = None

    @property
    def full_name(self) -> AnyStr:
        """
        :return: Full path and name
        """
        return self._full_name

    @property
    def file_name(self) -> AnyStr:
        """
        :return: file name, no path
        """
        return self._file_name

    @property
    def file_dir(self) -> AnyStr:
        """
        :return: path minus base_dir
        """
        return self._file_dir

    @property
    def size(self) -> int:
        if self._size is None:
            self._size = os.path.getsize(self._full_name)
        return self._size

    @property
    def md5(self) -> str:
        if not self._md5:
            self._md5 = create_md5(self._full_name)
        return self._md5


def create_md5(file_name: AnyStr) -> str:
    """
    Calculate md5 hash of file.

    :param file_name: to calculate hash for
    :return: md5 hash string
    """
    with open(file_name, "rb") as f:
        file_hash = hashlib.md5()
        while chunk := f.read(8192):
            file_hash.update(chunk)

    md5 = file_hash.hexdigest()
    logging.info(f"md5: {md5} {file_name}")
    return md5


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


def dir_contains(dirs_to_check_for: List[AnyStr], dir_path: AnyStr):
    """
    Check to see if dir_path is contained in any of the dirs_to_check

    :param dirs_to_check_for: list of directories
    :param dir_path: directory to check
    :return: true if dir_path in any of the dirs_to_check
    """
    assert dir_path
    if dirs_to_check_for:
        assert all(d for d in dirs_to_check_for)

        abs_path = os.path.abspath(dir_path).lower()
        for to_check in dirs_to_check_for:
            abs_to_check = os.path.abspath(to_check).lower()
            if abs_path.startswith(abs_to_check):
                return True

    return False


class DuplicateFinder:

    @staticmethod
    def get_file_infos(base_dir, dirs_to_ignore: List[AnyStr] = None) -> List[FileInfo]:
        """
        Return a list of FileInfo's for each file in (recursively) the base_dir
        """
        logging.debug(f"get_file_infos({base_dir})")
        cwd = os.getcwd()
        try:
            os.chdir(base_dir)
            infos = []
            count = 0

            to_scan = ["."]
            while len(to_scan):
                dir_to_scan = to_scan.pop(0)
                logging.debug(f"Scan {dir_to_scan}")

                entry: os.DirEntry
                for entry in scandir(dir_to_scan):
                    name = entry.name
                    if entry.is_dir(follow_symlinks=False):
                        if not dir_contains(dirs_to_ignore, name):
                            to_scan.append(join(dir_to_scan, name))
                    else:
                        size = entry.stat(follow_symlinks=False).st_size
                        logging.debug(
                            f"found {join(dir_to_scan, name)}, {size}")
                        infos.append(FileInfo(base_dir, dir_to_scan, name))
                        count += 1
                        if count % 100 == 0:
                            logging.info(f"{count}: {join(dir_to_scan, name)}")

            return infos
        finally:
            os.chdir(cwd)

    name_size_function: Callable[[FileInfo], tuple[AnyStr, int]] = lambda info: (
        info.file_name, info.size)
    """ Extract name and size from a FileInfo """

    size_function: Callable[[FileInfo],
                            tuple[AnyStr, int]] = lambda info: info.size
    """ Extract size from FileInfo """

    T = TypeVar('T')

    @staticmethod
    def get_key_infos(base_dir: str,
                      key_function: Callable[[FileInfo], T],
                      dirs_to_ignore: List[AnyStr] = None) -> Dict[T, List[FileInfo]]:
        """
        Returns dictionary keyed on the values returned by the key_function with a list of matching FileInfo's
        for all the files in base_dir (recursively)

        e.g. get_key_infos(secondary_dirs, lambda info: (info.file_name, info.size)) would return a
        dictionary with a (file_name, size) tuple as the key for file
        """

        results = {}
        for info in DuplicateFinder.get_file_infos(base_dir, dirs_to_ignore):
            key = key_function(info)
            result_value = results.get(key)
            if result_value:
                result_value.append(info)
            else:
                results[key] = [info]
        return results

    @staticmethod
    def get_size_infos(base_dir: str) -> Dict[tuple[str, int], List[FileInfo]]:
        """
        Returns dictionary keyed on file size with a list of matching FileInfo's
        for all the files in base_dir (recursively)
        """
        return DuplicateFinder.get_key_infos(base_dir, DuplicateFinder.size_function)

    @staticmethod
    def get_key_duplicates(
            primary_directories: List[AnyStr],
            secondary_directories: List[AnyStr],
            key_function: Callable[[FileInfo], T]) -> Set[FileInfo]:
        """
        List files that have matching key_function value and matching md5.

        Only files that match key_function return value have the md5 checked.

        It will list any secondary file that has a primary file match.

        If there are files that match in the secondary directory it will return all but the last matching file.

        All the returned files are safe to delete.

        :param key_function:
        :param primary_directories: list of primary directory names.  These files are never returned in the
        duplicate list
        :param secondary_directories: list of secondary directory names
        :return: set of files that are duplicated elsewhere.
        """
        duplicates = set()

        # Get all secondary files
        secondary = {}
        for base_dir in secondary_directories:
            secondary.update(DuplicateFinder.get_key_infos(
                base_dir, key_function))
        logging.debug("Secondary (found {len(secondary})")

        # Get all primary files
        primary = {}
        for base_dir in primary_directories:
            primary.update(DuplicateFinder.get_key_infos(
                base_dir, key_function, secondary_directories))
        logging.debug("Primary (found {len(primary})")

        # Get md5s of all primary's that match a secondary (name, size)
        primary_md5s = set()
        for key, infos in secondary.items():
            to_test = primary.get(key)
            if to_test:
                for info in to_test:
                    primary_md5s.add(info.md5)

        # Get list if secondary items that match a primary md5
        primary_duplicates = []
        for key, infos in secondary.items():
            if key in primary:
                primary_duplicates += [(key, info)
                                       for info in infos
                                       if info.md5 in primary_md5s]

        # Delete primary_duplicates items in secondary
        for key, info in primary_duplicates:
            infos = secondary.get(key)
            if infos:
                while info in infos:
                    infos.remove(info)
                if len(infos) == 0:
                    del secondary[key]

        [duplicates.add(info) for _, info in primary_duplicates]

        # for _, info in primary_duplicates:
        #     print("Delete(P) %s/%s" % (info.file_dir, info.file_name))

        # trim secondary duplicates
        key_dups = [(key, infos)
                    for key, infos in secondary.items()
                    if len(infos) > 1 and any(info.size > 1024 for info in infos)]

        md5_infos = {}
        for _, infos in key_dups:
            for info in infos:
                matches = md5_infos.get(info.md5)
                if matches:
                    matches.append(info)
                else:
                    md5_infos[info.md5] = [info]

        for file_hash, dup_files in md5_infos.items():
            if len(dup_files) > 1:
                # print(file_hash, dup_files[0].file_name)
                for info in dup_files[:-1]:
                    duplicates.add(info)
                #     print("   Delete(S) %s" % info.file_dir)
                # print("   Keep(S) %s" % dup_files[-1].file_dir)

        return duplicates

    @staticmethod
    def get_size_duplicates(
            primary_directories: List[AnyStr],
            secondary_directories: List[AnyStr]) -> Set[FileInfo]:
        """
        List files that have matching size and md5.  Only files that match the name and size are have the md5 checked.

        It will list any secondary file that has a primary file match.

        If there are files that match in the secondary directory it will return all but the last matching file.

        All the returned files are safe to delete.

        :param primary_directories: list of primary directory names.  These files are never returned in the
        duplicate list
        :param secondary_directories: list of secondary directory names
        :return: set of files that are duplicated elsewhere.
        """

        return DuplicateFinder.get_key_duplicates(primary_directories, secondary_directories,
                                                  DuplicateFinder.size_function)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(usage='%(prog)s [options]',
                                     description='Find and remove duplicates')

    parser.add_argument('-n', '--pretend',
                        action='store_true',
                        help='Do not actually collapse')

    parser.add_argument('-v', '--verbose',
                        action='store_true',
                        help='Turn on verbose output')

    parser.add_argument('-p', '--primary',
                        help='Primary directory (never delete primary directories; repeatable)',
                        action='append',
                        type=path_type
                        )

    parser.add_argument('-s', '--secondary',
                        required=True,
                        help='Secondary directory (delete duplicates in these directories; repeatable)',
                        action='append',
                        type=path_type
                        )

    parser.usage = parser.format_help()

    parser.add_argument('--loglevel',
                        choices=['critical', 'error',
                                 'warning', 'info', 'debug'],
                        type=str.lower,
                        help='Set logging level. Example --loglevel debug')
    args = parser.parse_args()

    if args.loglevel:
        logging.basicConfig(level=args.loglevel.upper())
        logging.info(f"Logging set to {args.loglevel.upper()}")

    pretend_mode = args.pretend
    verbose_mode = args.verbose or pretend_mode
    primary_dirs = args.primary
    secondary_dirs = args.secondary

    to_delete = list(DuplicateFinder.get_size_duplicates(
        primary_dirs, secondary_dirs))
    to_delete.sort(key=lambda info: info.file_name)

    total_files = 0
    total_size = 0
    for file in to_delete:
        if not pretend_mode:
            if os.path.isdir(file.full_name):
                shutil.rmtree(file.full_name)
            else:
                os.remove(file.full_name)
        if verbose_mode:
            print("remove %s" % file.full_name)

        total_files += 1
        total_size += file.size

    if verbose_mode:
        print("Total files:", total_files)
        print("Total size:", total_size)
