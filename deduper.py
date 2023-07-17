import argparse
import fnmatch
import os.path
import pathlib
import re
import shutil
import os.path as p
import time
from typing import List

from enum import Enum

import xml.etree.ElementTree as ET
from fuzzywuzzy import fuzz


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

        bestVerRating= _getRatingForGameName(bestVer.baseName)
        #print("*Checking: %s -> %s" % (bestVer,bestVerRating))

        restOfFiles:List[GameFile] = self.games[1:]
        for game in restOfFiles:
            currentVerRating = _getRatingForGameName(game.baseName)
            #print("*Checking: %s -> %s" % (game.absPath, currentVerRating))
            if currentVerRating > bestVerRating:
                bestVer = game
                bestVerRating = currentVerRating

        #print("Selected: %s with %s" % (bestVer.absPath, bestVerRating))

        return bestVer

    def getNonBestVersionGames(self):
        bestVersion:GameFile = self.getBestVersion()

        gamesToRemove:[] = [*self.games]
        gamesToRemove.remove(bestVersion)

        return gamesToRemove

class Comparers:

    @classmethod
    def exactCompare(self, game1:str, game2:str):
        return game1==game2

    @classmethod
    def fuzzyCompare(self, game1:str, game2:str):

        ratio = fuzz.ratio(game1, game2)

        return ratio >= 90



def  _getNameToCompare(name:str, removeCharsFromStartCount:int):
    name = name[removeCharsFromStartCount:]
    name=name.replace("'","_") #do this because some sets come with these to symbols to diferentiate versions
    parts = name.split("(")
    return parts[0].strip()

def _findWords(searchWords:[[]], text, trueIfAll=False):

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

def _getRatingForGameName(name):
    points = 0

    name = name.lower()

    isJap=False
    if _findWords([["europe", Find.WORD], ["eur", Find.WORD], ["\(E\)", Find.REGEX]], name): points += 50
    if _findWords([["japan", Find.WORD], ["jap", Find.WORD], ["\(J\)", Find.REGEX]], name):   points += 10; isJap=True
    if _findWords([["usa", Find.WORD], ["\(U\)", Find.REGEX], ["australia", Find.WORD]], name): points += 30
    if _findWords([["world", Find.WORD]], name): points += 20
    if _findWords([["beta", Find.WORD]], name): points -=30
    if _findWords([["\(proto.*?\)", Find.REGEX]], name): points -= 50
    if _findWords([["spain", Find.WORD]], name): points += 100
    if _findWords([["\[!\]", Find.REGEX]], name): points += 40
    if _findWords([["\[b\d{0,2}\]", Find.REGEX]], name): points -= 40
    if _findWords([["\[h\d{0,2}\]", Find.REGEX]], name): points -= 100
    if _findWords([["\(UE\)", Find.REGEX], ["\(EU\)", Find.REGEX]], name): points+=50
    if _findWords([["\(UJ\)", Find.REGEX], ["(JU)", Find.REGEX]], name): points += 30
    if _findWords([["\[a\d{0,2}(?![-\w])\]", Find.REGEX]], name): points-=10
    if _findWords([["\[o\d{0,2}(?![-\w])\]", Find.REGEX]], name): points -= 10 #Overdump

    if _findWords([["\[t\-eng.*?\]", Find.REGEX]], name):
        points += 50
    elif _findWords([["\[t\-spa.*?\]", Find.REGEX]], name): points += 60
    elif _findWords([["\[t\-.*?\]", Find.REGEX]], name):
        if isJap:
            points += 40
        else:
            points -=40

    if _findWords([["partial", Find.REGEX]], name):
        points-=10

    if _findWords([["\[t\d{0,2}(?![-\w])\]", Find.REGEX]], name): points -= 20 #No trainers please

    return points

def _calculateSizeOfFilesInBytes(gameFiles:List[GameFile]):
    totalSize = 0
    for gameFile in gameFiles:
        totalSize += os.path.getsize(gameFile.absPath)

    return totalSize

def _convertBytesToMBStr(sizeInBytes:int) -> str:
    size = str (round ((sizeInBytes/(1024*1024)),1)) + ' MB'
    return size

def _dedupFolderPrintReport(generalReport:bool, clonesReport:bool, totalFileCount:int, totalFileSize:int, bestVersSize:int, gameGroups:[], bestVers:[]):
    if generalReport or clonesReport:
        print("Report")
        print("=========================================================================")

        if generalReport:
            print("General Data...")
            print("===============")

            print("# Originals ->  File Count: %s Total Size: %s" % (totalFileCount, _convertBytesToMBStr(totalFileSize)))
            print("# De duplicated -> File Count: %s TotalSize: %s" % (len(gameGroups), _convertBytesToMBStr(bestVersSize)))
            print("# Total games removed: %s Total space saved: %s" % (totalFileCount - len(gameGroups), _convertBytesToMBStr(totalFileSize - bestVersSize)))

        if clonesReport:
            print("Info: Writing clones report...")
            print("==============================")

            for i, bestVer in enumerate(bestVers):
                group = gameGroups[i]
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

def _dedupGameListPrintReport(generalReport:bool, clonesReport:bool,gamesTotalCount:int, gamesTotalSize:int, gameGroups:[], bestVers:[], nonBestVersGames:[]):
    if generalReport or clonesReport:
        nonBestVersGamesSize = _calculateSizeOfFilesInBytes(nonBestVersGames)
        nonBestVersGamesCount = len(nonBestVersGames)

        print("Report")
        print("=========================================================================")

        if generalReport:
            print("General Data...")
            print("===============")

            print("# Originals ->  File Count: %s Total Size: %s" % (gamesTotalCount, _convertBytesToMBStr(gamesTotalSize)))
            print("# Removed %s games and you saved %s" % (nonBestVersGamesCount, _convertBytesToMBStr(nonBestVersGamesSize)))

        if clonesReport:
            print("Info: Writing clones report...")
            print("==============================")

            for i, bestVer in enumerate(bestVers):
                group = gameGroups[i]
                if len(group.games) == 1:
                    print("## Game with no clones: %s" % group.games[0].absPath)
                else:
                    print("##################################################################################")
                    for game in group.games:
                        if game == bestVer:
                            print("## [\u2713] %s" % game.absPath)
                        else:
                            print("## [X] %s" % game.absPath)
                    print("##################################################################################")

def _calculateDuplicates(games:List[GameFile]) -> List[GameGroup]:
    print("Calculating duplicates...")
    clonedGameList = [];
    clonedGameList.extend(games)
    games=clonedGameList

    gameGroups = []

    while len(games) > 0:
        if len(games) == 1:
            group = GameGroup()
            group.addGame(games[0])
            gameGroups.append(group)
            break;

        file = games[0]

        fileName = file.comparableFileName
        group = GameGroup()
        group.addGame(file)
        for index in range(1, len(games)):
            choice = games[index].comparableFileName
            if Comparers.exactCompare(fileName, choice):
                group.addGame(games[index])

        gameGroups.append(group)

        for game in group.games:
            games.remove(game)

    return gameGroups

def _copyFiles(outputFolder:str, games:[], exportRemoveCharCount:int):
    _copyAndMoveFiles(outputFolder,games,exportRemoveCharCount,True)

def _moveFiles(outputFolder:str, games:[], exportRemoveCharCount:int):
    _copyAndMoveFiles(outputFolder,games,exportRemoveCharCount,False)

def _copyAndMoveFiles(outputFolder:str, games:[], exportRemoveCharCount:int, copyAction:bool=True):
        copy: bool = True
        if not os.path.exists(outputFolder):
            os.makedirs(outputFolder)
        else:
            filesInFolderCount = len(fnmatch.filter(os.listdir(outputFolder), '*'))
            if filesInFolderCount > 0:
                print("ERROR: The output folder is not empty. Please delete it or its contains to export games")
                copy = False

        if copy:
            for i, game in enumerate(games):
                exportingName = game.baseName[exportRemoveCharCount:]
                if copyAction:
                    print("Copying %s to %s (%s/%s)" % (game.absPath, outputFolder, i+1, len(games)))
                    shutil.copy(game.absPath, os.path.join(outputFolder, exportingName))
                else:
                    print("Moving %s to %s (%s/%s)" % (game.absPath, outputFolder, i+1, len(games)))
                    shutil.move(game.absPath, os.path.join(outputFolder, exportingName))

def dedupFolder(args):
    searchPath = args.rom_folder
    outputPath = args.output_folder

    extensionList = args.extensions.split(",")

    compareRemoveCharCount = args.compare_remove
    exportRemoveCharCount = args.export_remove

    gameGroups=[]
    games: List[GameFile] = []

    for ext in extensionList:
        filesGenerator = searchPath.glob("*." + ext)

        for file in filesGenerator:
            absPath: str = str(file)
            games.append(GameFile(absPath, _getNameToCompare(os.path.basename(absPath), compareRemoveCharCount)))

    totalFileSize = _calculateSizeOfFilesInBytes(games)

    totalFileCount: int = len(games)

    if totalFileCount == 0:
        print("Could not find any file to process.")
        print("Done.")
        exit(0)

    if args.delete_output_folder and os.path.exists(outputPath):
        print("Deleting output folder %s" % outputPath)
        shutil.rmtree(outputPath)

    gameGroups = _calculateDuplicates(games)
    print("Found %s duplicates..." % (totalFileCount - len(gameGroups)))

    bestVers: [] = []

    print("Calculating best versions...")
    for group in gameGroups:
        bestVer = group.getBestVersion()
        bestVers.append(bestVer)

    bestVersSize: int = _calculateSizeOfFilesInBytes(bestVers)

    if args.output_folder:
        print("Exporting files to %s" % args.output_folder)
        _copyFiles(args.output_folder, bestVers, exportRemoveCharCount)


    _dedupFolderPrintReport(args.general_report, args.clones_report, totalFileCount, totalFileSize, bestVersSize, gameGroups, bestVers)

    print("Done!")

def dedupGameList(args):
    gameList:str=args.game_list
    romFolder:str=args.rom_folder
    outputFolder:str=args.output_folder
    reportGeneral:bool=args.general_report
    clonesResport:bool=args.clones_report
    deleteOutputFolder:bool=args.delete_output_folder

    if not os.path.exists(gameList):
        print("Error: Game list file does not exist at %s" % gameList)
        exit(1)

    tree = ET.parse(gameList)
    root = tree.getroot()

    elements = root.findall('./game')

    games = []
    for element in elements:
        path = element.find("path").text
        name = element.find("name").text
        path = os.path.join(romFolder,os.path.basename(path))
        games.append(GameFile(path,name))


    totalFileCount: int = len(games)

    if totalFileCount == 0:
        print("Could not find any rom to process in %s." % romFolder)
        print("Done.")
        exit(0)

    if deleteOutputFolder and os.path.exists(outputFolder):
        print("Deleting output folder %s" % outputFolder)
        shutil.rmtree(outputFolder)

    gameGroups = _calculateDuplicates(games)

    bestVers: [] = []
    gamesToRemove: [] = []
    print("Calculating best versions...")
    for group in gameGroups:
        bestVer = group.getBestVersion()
        bestVers.append(bestVer)

    for group in gameGroups:
        nonBestVersionGames = group.getNonBestVersionGames()
        gamesToRemove.extend(nonBestVersionGames)

    gamesTotalSize = _calculateSizeOfFilesInBytes(games)
    gamesTotalCount = len(games)

    _dedupGameListPrintReport(reportGeneral, clonesResport,gamesTotalCount, gamesTotalSize, gameGroups, bestVers, gamesToRemove)

    if outputFolder:
        _moveFiles(outputFolder, gamesToRemove, 0)

    print("Done!")