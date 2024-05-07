import argparse
import pathlib

import cd2chd
import deduper

from  rating_functions import DSFilesRating,DSValidateGame

def dedupFolder(args):
    deduper.dedupFolder(args, DSFilesRating, DSValidateGame)

def dedupGameList(args):
    deduper.dedupGameList(args)

def cd2chdAction(args):
    cd2chd.convert(args)

parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers()

parserA = subparsers.add_parser('dedup_folder',help='Given a folder with roms we dedup it and send the output roms to a folder')
parserA.set_defaults(func=dedupFolder)
parserA.add_argument('--rom-folder', type=pathlib.Path, required=True, help='Folder with roms')
parserA.add_argument('--output-folder', type=pathlib.Path, required=False, help='Good games output folder. The copying of good roms will be performed if this param is given')
parserA.add_argument('--general-report', required=False, action='store_true', help='Print general report')
parserA.add_argument('--clones-report', required=False, action='store_true', help='Print clones report')
parserA.add_argument('--report-to-file', required=False, action='store_true', help='Write report to file too')
parserA.add_argument('--extensions', required=True, help="add extensions to search in the form of ext1,ext2, etc.")
parserA.add_argument('--compare-remove', required=False, type=int, default=0, help="How many character should I remove at the begining to compare file names")
parserA.add_argument('--export-remove', required=False, type=int,default=0, help="How many characters should I remove at the beginning to export games")
parserA.add_argument('--delete-output-folder', required=False, action='store_true',default=0, help="Delete output folder before exporting games")

parserB = subparsers.add_parser('dedup_gamelist',help='Given a gamelist in Emulation station format we dedup the system moving duplicates to an output folder')
parserB.set_defaults(func=dedupGameList)
parserB.add_argument('--game-list', type=pathlib.Path, required=True, help='Path to gamelist')
parserB.add_argument('--rom-folder', type=pathlib.Path, required=True, help='Path to rom folder related to the gamelist')
parserB.add_argument('--output-folder', type=pathlib.Path, required=False, help='Removed roms folder. The movement of roms will be performed if this param is given')
parserB.add_argument('--general-report', required=False, action='store_true', help='Print general report')
parserB.add_argument('--clones-report', required=False, action='store_true', help='Print clones report')
parserB.add_argument('--delete-output-folder', required=False, action='store_true',default=0, help="Delete output folder before outputing duplicated roms")

parserB = subparsers.add_parser('cd2chd',help='Give a folder or a file name (iso, cue, img,ccd) to convert cd images')
parserB.set_defaults(func=cd2chdAction)
parserB.add_argument('--source-files', type=pathlib.Path, required=True, help='Can be a folder or a file')
parserB.add_argument('--output-folder', type=pathlib.Path, required=False, help='Removed roms folder. The movement of roms will be performed if this param is given')
parserB.add_argument('--delete-original', required=False, action='store_true',default=0, help="Delete original iso images to save space")


args = parser.parse_args()
if hasattr(args, 'func'):
    args.func(args)

print("Done.")



