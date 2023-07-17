import argparse
import pathlib

import deduper

'''
def dedupFolder(args):
    dedupFolder(args)

def dedupGameList(args):
    dedupGameList(args)

parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers()

parserA = subparsers.add_parser('dedup_folder',help='Given a folder with roms we dedup it and send the output roms to a folder')
parserA.set_defaults(func=dedupFolder)
parserA.add_argument('--game-folder', type=pathlib.Path, required=True, help='Game folder')
parserA.add_argument('--output-folder', type=pathlib.Path, required=False, help='Good games output folder. If it is not provided no clean romset export witll be done')
parserA.add_argument('--general-report', required=False, action='store_true', help='Print general report')
parserA.add_argument('--clones-report', required=False, action='store_true', help='Print clones report')
parserA.add_argument('--report-to-file', required=False, action='store_true', help='Write report to file too')
parserA.add_argument('--extensions', required=True, help="add extensions to search in the form of ext1,ext2, etc.")
parserA.add_argument('--compare-remove', required=False, type=int, default=0, help="How many character should I remove at the begining to compare file names")
parserA.add_argument('--export-remove', required=False, type=int,default=0, help="How many characters should I remove at the beginning to export games")
parserA.add_argument('--delete-output-folder', required=False, action='store_true',default=0, help="Delete output folder before exporting games")


parserB = subparsers.add_parser('dedup_gamelist',help='Given a gamelist in Emulation station format we dedup the system moving duplicates to an output folder')
parserB.add_argument('--output-folder', type=pathlib.Path, required=False, help='Good games output folder. If it is not provided no clean romset export witll be done')
parserB.add_argument('--general-report', required=False, action='store_true', help='Print general report')
parserB.add_argument('--clones-report', required=False, action='store_true', help='Print clones report')
parserB.add_argument('--delete-output-folder', required=False, action='store_true',default=0, help="Delete output folder before exporting games")

args = parser.parse_args()
if hasattr(args, 'func'):
    args.func(args)

'''
deduper.dedupGameList([])