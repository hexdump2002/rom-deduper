import argparse
import fnmatch
import os.path
import pathlib
import re
import shutil
import os.path as p
from typing import List

from enum import Enum

from fuzzywuzzy import fuzz

fileGroups=[]

class Find(Enum):
    WORD = 0
    REGEX= 1


class GameFile:

    def __init__(self, absPath:str, comparableFileName:str):
        self.absPath = absPath
        self.baseName = os.path.basename(absPath)
        self.comparableFileName = comparableFileName

class GameGroup:

    def __init__(self):
        self.games:List[GameFile] = []

    def addGame(self, game:GameFile):
        self.games.append(game)


    def getBestVersion(self) -> GameFile:
        assert len(self.games) > 0

        bestVer:GameFile = self.games[0]

        bestVerRating= getRatingForGameName(bestVer.baseName)
        #print("*Checking: %s -> %s" % (bestVer,bestVerRating))

        restOfFiles:List[GameFile] = self.games[1:]
        for game in restOfFiles:
            currentVerRating = getRatingForGameName(game.baseName)
            #print("*Checking: %s -> %s" % (game.absPath, currentVerRating))
            if currentVerRating > bestVerRating:
                bestVer = game
                bestVerRating = currentVerRating

        #print("Selected: %s with %s" % (bestVer.absPath, bestVerRating))

        return bestVer


class Comparers:

    @classmethod
    def exactCompare(self, game1:str, game2:str):
        return game1==game2

    @classmethod
    def fuzzyCompare(self, game1:str, game2:str):

        ratio = fuzz.ratio(game1, game2)

        return ratio >= 90



def  getNameToCompare(name:str, removeCharsFromStartCount:int):
    name = name[removeCharsFromStartCount:]
    name=name.replace("'","_") #do this because some sets come with these to symbols to diferentiate versions
    parts = name.split("(")
    return parts[0].strip()

def findWords(searchWords:[[]], text, trueIfAll=False):

    found = False
    for search in searchWords:
        word = search[0]
        matchFound = False
        if search[1]==Find.WORD:
            result = re.search(rf'\b{word}\b',text, re.IGNORECASE)
            matchFound = result is not None
        elif search[1]==Find.REGEX:
            result = re.search(rf'{word}', text, re.IGNORECASE)
            matchFound = result is not None
        else:
            assert False

        if matchFound:
            found = True;
            if not trueIfAll:
                break
        else:
            if trueIfAll:
                found=False
                break;

    return found

def getRatingForGameName(name):
    points = 0

    name = name.lower()

    isJap=False
    if findWords([["europe",Find.WORD],["eur",Find.WORD],["\(E\)",Find.REGEX]], name): points += 50
    if findWords([["japan",Find.WORD],["jap",Find.WORD],["\(J\)",Find.REGEX]], name):   points += 10; isJap=True
    if findWords([["usa",Find.WORD], ["\(U\)",Find.REGEX]], name): points += 30
    if findWords([["world",Find.WORD]], name): points += 20
    if findWords([["beta",Find.WORD]],name): points -=30
    if findWords([["\(proto.*?\)",Find.REGEX]], name): points -= 50
    if findWords([["spain",Find.WORD]],name): points += 100
    if findWords([["\[!\]",Find.REGEX]],name): points += 40
    if findWords([["\[b\d{0,2}\]",Find.REGEX]], name): points -= 40
    if findWords([["\[h\d{0,2}\]",Find.REGEX]], name): points -= 100
    if findWords([["\(UE\)",Find.REGEX],["\(EU\)",Find.REGEX]],name): points+=50
    if findWords([["\(UJ\)",Find.REGEX],["(JU)",Find.REGEX]], name): points += 30
    if findWords([["\[a\d{0,2}(?![-\w])\]",Find.REGEX]],name): points-=10
    if findWords([["\[o\d{0,2}(?![-\w])\]", Find.REGEX]], name): points -= 10 #Overdump

    if findWords([["\[t\-eng.*?\]", Find.REGEX]], name):
        points += 50
    elif findWords([["\[t\-spa.*?\]", Find.REGEX]], name): points += 60
    elif findWords([["\[t\-.*?\]", Find.REGEX]], name):
        if isJap:
            points += 40
        else:
            points -=40

    if findWords([["partial", Find.REGEX]], name):
        points-=10

    if findWords([["\[t\d{0,2}(?![-\w])\]", Find.REGEX]], name): points -= 20 #No trainers please

    return points

def calculateSizeOfFilesInBytes(gameFiles:List[GameFile]):
    totalSize = 0
    for gameFile in gameFiles:
        totalSize += os.path.getsize(gameFile.absPath)

    return totalSize

def convertBytesToMBStr(sizeInBytes:int) -> str:
    size = str (round ((sizeInBytes/(1024*1024)),1)) + ' MB'
    return size

def printReport(gneralReport:bool, clonesReport:bool):
    if gneralReport or clonesReport:
        print("Report")
        print("=========================================================================")

        if gneralReport:
            print("General Data...")
            print("===============")

            print("# Originals ->  File Count: %s Total Size: %s" % (totalFileCount, convertBytesToMBStr(totalFileSize)))
            print("# De duplicated -> File Count: %s TotalSize: %s" % (len(fileGroups), convertBytesToMBStr(bestVersSize)))
            print("# Total games removed: %s Total space saved: %s" % (totalFileCount - len(fileGroups), convertBytesToMBStr(totalFileSize - bestVersSize)))

        if clonesReport:
            print("Info: Writing clones report...")
            print("==============================")

            for i, bestVer in enumerate(bestVers):
                group = fileGroups[i]
                if len(group.games) == 1:
                    print("## Game with no clones: %s" % group.games[0].absPath)
                else:
                    print("##################################################################################")
                    for game in group.games:
                        if game == bestVer:
                            print("## [X] %s" % game.absPath)
                        else:
                            print("## [ ] %s" % game.absPath)
                    print("##################################################################################")


parser = argparse.ArgumentParser()

parser.add_argument('--game-folder', type=pathlib.Path, required=True, help='Game folder')
parser.add_argument('--output-folder', type=pathlib.Path, required=False, help='Good games output folder. If it is not provided no clean romset export witll be done')
parser.add_argument('--general-report', required=False, action='store_true', help='Print general report')
parser.add_argument('--clones-report', required=False, action='store_true', help='Print clones report')
parser.add_argument('--report-to-file', required=False, action='store_true', help='Write report to file too')
parser.add_argument('--extensions', required=True, help="add extensions to search in the form of ext1,ext2, etc.")
parser.add_argument('--compare-remove', required=False, type=int, default=0, help="How many character should I remove at the begining to compare file names")
parser.add_argument('--export-remove', required=False, type=int,default=0, help="How many characters should I remove at the beginning to export games")

args = parser.parse_args()

searchPath = args.game_folder
outputPath = args.output_folder

extensionList = args.extensions.split(",")

compareRemoveCharCount = args.compare_remove
exportRemoveCharCount = args.export_remove

games:List[GameFile] = []

for ext in extensionList:
    filesGenerator = searchPath.glob("*."+ext)

    for file in filesGenerator:
        absPath:str = str(file)
        games.append(GameFile(absPath, getNameToCompare(os.path.basename(absPath), compareRemoveCharCount)))

totalFileSize = calculateSizeOfFilesInBytes(games)

totalFileCount:int = len(games)

if totalFileCount == 0:
    print("Could not find any file to process.")
    print("Done.")
    exit(0)

print("Calculating duplicates...")

while len(games)>0:
    if len(games)==1:
        group = GameGroup()
        group.addGame(games[0])
        break;

    file = games[0]
    fileName = file.comparableFileName
    group = GameGroup()
    group.addGame(file)
    for index in range(1, len(games)):
        choice = games[index].comparableFileName
        if Comparers.exactCompare(fileName,choice):
            group.addGame(games[index])

    fileGroups.append(group)

    for game in group.games:
        games.remove(game)



print("Found %s duplicates..." %  (totalFileCount - len(fileGroups)))

bestVers:[] = []

print("Calculating best versions...")
for group in fileGroups:
    bestVer = group.getBestVersion()
    bestVers.append(bestVer)

bestVersSize:int = calculateSizeOfFilesInBytes(bestVers)


if args.output_folder:
    print("Exporting files to %s"%args.output_folder)
    copy:bool = True
    if not os.path.exists(args.output_folder):
        os.makedirs(args.output_folder)
    else:
        filesInFolderCount=len(fnmatch.filter(os.listdir(args.output_folder), '*'))
        if filesInFolderCount>0:
            print("ERROR: The output folder is not empty. Please delete it or its contains to export games")
            copy = False


    if copy:
        for i, bestVer in enumerate(bestVers):
             print("Copying %s to %s (%s/%s)" % (bestVer.absPath, outputPath, i,len(bestVers)))
             exportingName = bestVer.baseName[exportRemoveCharCount:]
             shutil.copy(bestVer.absPath, os.path.join(outputPath,exportingName))


printReport(args.general_report, args.clones_report)

print("Done!")
