"""
Scratch script to pick a bunch of file for the canary check
"""


import random
from os import path

from DuplicateDelete import DuplicateFinder

base_dirs = [r"backup-old"]

dirs_to_ignore = [r"backup-old\old"]

files_picked_per_ext = 5

files = []
for base_dir in base_dirs:
    files.extend(DuplicateFinder.get_file_infos(base_dir, dirs_to_ignore))

print(f'{len(files)} files found in "{base_dirs}"')

files_by_ext = {}

for file in files:
    file_name, file_ext = path.splitext(file.full_name)
    if file_ext:
        files_for_ext = files_by_ext.get(file_ext)

        if files_for_ext:
            files_for_ext.append(file)
        else:
            files_by_ext[file_ext] = [file]

for file_ext, files in files_by_ext.items():
    print("%5d   %s" % (len(files), file_ext))

picked_files = []
for file_ext, files in files_by_ext.items():
    to_pick = files_picked_per_ext if files_picked_per_ext <= len(
        files) else len(files)

    picked_for_ext = random.sample(files, k=to_pick)
    print(f"{file_ext}:")
    [print(f"   {path.join(file.file_dir, file.file_name)}")
     for file in sorted(picked_for_ext, key=lambda info: info.full_name)]

    picked_files.extend(picked_for_ext)

print()
print("Calculating md5 file")
print()

for file in sorted(picked_files, key=lambda info: info.full_name):
    print(f"{file.md5}  {file.full_name}")
