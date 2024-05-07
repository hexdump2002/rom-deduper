import argparse
import fnmatch
import os.path
import pathlib

import shutil
import os.path as p
import sys
import time
from typing import List, Dict, Callable

import xml.etree.ElementTree as ET
from fuzzywuzzy import fuzz


class GameFile:

    def __init__(self, absPath:str, comparableFileName:str, extraData:Dict={}):
        self.absPath = absPath
        self.baseName = os.path.basename(absPath)
        self.comparableFileName = comparableFileName
        self.extraData = extraData

class GameGroup:

    def __init__(self, gameRatingFunc):
        self.games:List[GameFile] = []
        self.gameRatingFunc:Callable[[str],int] = gameRatingFunc

    def addGame(self, game:GameFile):
        self.games.append(game)


    def getBestVersion(self) -> GameFile:
        assert len(self.games) > 0

        bestVer:GameFile = self.games[0]

        bestVerRating = self.gameRatingFunc(bestVer.baseName)
        #print("*Checking: %s -> %s" % (bestVer,bestVerRating))

        restOfFiles:List[GameFile] = self.games[1:]
        for game in restOfFiles:
            currentVerRating = self.gameRatingFunc(game.baseName)
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
    name=name.replace("'","_") #do this because some sets come with these two symbols to diferentiate versions
    parts = name.split("(")
    return parts[0].strip()

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
            print("# Total games to remove: %s Total space saved: %s" % (totalFileCount - len(gameGroups), _convertBytesToMBStr(totalFileSize - bestVersSize)))

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

def _calculateDuplicates(games:List[GameFile],gameRaterFunc:Callable[[str],int]) -> List[GameGroup]:
    print("Calculating duplicates...")
    clonedGameList = [];
    clonedGameList.extend(games)
    games=clonedGameList

    gameGroups = []

    while len(games) > 0:
        if len(games) == 1:
            group = GameGroup(gameRaterFunc)
            group.addGame(games[0])
            gameGroups.append(group)
            break;

        file = games[0]

        fileName = file.comparableFileName
        group = GameGroup(gameRaterFunc)
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

def dedupFolder(args, gameRaterFunc: Callable[[str],int], validGame: Callable[[str],bool]):
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
            fileName = os.path.basename(absPath)
            name =  _getNameToCompare(fileName, compareRemoveCharCount)
            if validGame(fileName):
                games.append(GameFile(absPath, name))
            else:
                print(f"Discarting game {absPath} because function game validator said so")
                pass

    totalFileSize = _calculateSizeOfFilesInBytes(games)

    totalFileCount: int = len(games)

    if totalFileCount == 0:
        print("Could not find any file to process.")
        print("Done.")
        exit(0)

    if args.delete_output_folder and os.path.exists(outputPath):
        print("Deleting output folder %s" % outputPath)
        shutil.rmtree(outputPath)

    gameGroups = _calculateDuplicates(games,gameRaterFunc)
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

def _removeGamesFromXML(parentNode, gamesToRemove:List):
    for game in gamesToRemove:
        parentNode.remove(game.extraData['node'])

def _handleInconsistenciesFound(gamesNotInSyncWithRomFolder:[], xmlTree, gameListPath:str):
    exitProgram:bool = False
    exit: bool = False
    xmlRootNode = xmlTree.getroot();
    while not exit:
        text="The gamelist.xml file contains %s games that are not pressent in rom folder. Press L to list inconsistencies or Y or N to continue (Y/N/Q/L)" % len(gamesNotInSyncWithRomFolder)
        data = input(text)
        if data == 'y' or data == 'Y':
            _removeGamesFromXML(xmlRootNode, gamesNotInSyncWithRomFolder)
            xmlTree.write(str(gameListPath))
            exit = True
        elif data == 'n' or data == 'N':
            print("Continuing withou removing inconsistencies from gamelist")
            exit = True
        elif data == 'q' or data == 'Q':
            exitProgram = True
            exit = True
        elif data == 'l' or data == 'L':
            print("Listing inconsistencies...")
            for game in gamesNotInSyncWithRomFolder:
                print(game.absPath)

    return exitProgram

def dedupGameList(args, fileRatingFunc):
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

    gamesNotInSyncWithRomFolder: List = []

    games = []
    for element in elements:
        path = element.find("path").text
        name = element.find("name").text
        path = os.path.join(romFolder,os.path.basename(path))

        if not os.path.exists(path):
            gamesNotInSyncWithRomFolder.append(GameFile(path, name, extraData={"node": element}))
        else:
            games.append(GameFile(path, name, extraData={"node": element}))

    if len(gamesNotInSyncWithRomFolder)>0:
        exitProgram = _handleInconsistenciesFound(gamesNotInSyncWithRomFolder, tree,gameList)
        if exitProgram:
            return

    totalFileCount: int = len(games)

    if totalFileCount == 0:
        print("Could not find any rom to process in %s." % romFolder)
        return

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

    if len(gamesToRemove) > 0:
        if outputFolder:
            print("Moving duplicates to %s" % outputFolder)
            _moveFiles(outputFolder, gamesToRemove, 0)

        print("Removing entries from gamelist %s" % gameList)
        _removeGamesFromXML(root, gamesToRemove)
        tree.write(gameList)

    else:
        print("No duplicates to move. Everything seems clean.")

