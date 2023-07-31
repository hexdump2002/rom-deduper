import csv
import functools
import glob
import os
import re
import shutil
import zipfile
import functools
from PIL import Image

from typing import List, Dict

class Game:
    def __init__(self,gamePath:str, comparableGameName:str, gameImgPath:str=None):
        self.gamePath: str = gamePath
        self.comparableGameName: str = comparableGameName
        self.gameImgPath: str = gameImgPath
        pass

    def getFileName(self):
        return os.path.basename(self.gamePath)


filesPath = 'C:\\Users\\juanjo\\Desktop\\zx\\games\\*\\*'
screensPath = 'C:\\Users\\juanjo\\Desktop\\zx\\screens\\in-game\\*\\*'

files = list(glob.iglob(filesPath, recursive=True))
imgs = list(glob.iglob(screensPath, recursive=True))

def  _getNameToCompare(name:str, removeCharsFromStartCount:int):
    name = name[removeCharsFromStartCount:]
    name = os.path.splitext(os.path.basename(name))[0]
    nameNoExt: str = os.path.splitext(name)[0]
    parts = nameNoExt.split("(")

    comparableName = parts[0]
    comparableName = re.split(r'Part\d', comparableName)[0]
    comparableName = re.split(r'V\d',  comparableName)[0]
    comparableName = re.split(r'Demo\b', comparableName)[0]
    comparableName = re.split(r'Intro\b', comparableName)[0]

    comparableName = re.sub(r'(SideA|SideB)', "", comparableName)
    comparableName = re.sub(r'(48k|128k|48K|128K)', "", comparableName)
    comparableName = re.sub(r'(48|128|)',"",comparableName)
    comparableName = re.sub(r'_\d', "", comparableName)
    comparableName = re.sub(r'_', "", comparableName)

    return comparableName

def _calculateDuplicates(fileItems: dict) -> List[List[str]]:
    print("Calculating duplicates...")
    fileItems=fileItems.copy()

    gameGroups = []

    for key in fileItems.keys():
        keyItems = hashedFiles[key]

        while len(keyItems) > 0:
            if len(keyItems) == 1:
                group = []
                group.append(keyItems[0])
                gameGroups.append(group)
                break;

            file = keyItems[0]

            fileName = _getNameToCompare(file,0)
            group = []
            group.append(file)
            for index in range(1, len(keyItems)):
                choice = _getNameToCompare(keyItems[index],0)
                if fileName == choice:
                    group.append(keyItems[index])

            gameGroups.append(group)

            for game in group:
                keyItems.remove(game)

    return gameGroups

def _doesZipContainsMoreThanOneLoadableFile(pathToZipFile:str):
    with zipfile.ZipFile(pathToZipFile, 'r') as zipObj:
        filesInZip:[str] = zipObj.namelist()
        #Get root files only
        reg = re.compile(r'(.tap|.z80|.dsk|.tzx)$',re.IGNORECASE)
        filesInZip = list(filter(lambda s: reg.search(s),filesInZip))
        return len(filesInZip)!=1

def _getLoadableFilesInZip(pathToZipFile:str):
    with zipfile.ZipFile(pathToZipFile, 'r') as zipObj:
        filesInZip:[str] = zipObj.namelist()
        reg = re.compile(r'(.tap|.z80|.dsk|.tzx)$',re.IGNORECASE)
        filesInZip = list(filter(lambda s: reg.search(s),filesInZip))
        return filesInZip


def _getRatingForZipGame(fullGamePath:str):
    gameNameWitExt = os.path.splitext(os.path.basename(fullGamePath))[0]
    parts = os.path.splitext(gameNameWitExt);

    #if("demo" in str.lower(fullGamePath)):
    #    print("pepe")

    ext = parts[-1]
    points:int = 0;
    if ext == ".z80":
        points = 10
    elif ext == ".tzx":
        points = 20
    elif ext ==".tap":
        points = 30
    elif ext =='.mgt':
        points = 0
    elif ext =='.dsk':
        points = 50
    else:
        print("Discarting game by ext for %s" % gameNameWitExt)
        return 0

    if '128' in gameNameWitExt:
        points += 100

    if re.findall(r"Demo\b",gameNameWitExt):
        points -=200

    #Try to get always normal version
    if 'different' in gameNameWitExt:
        points -= 5

    return points

def _getBestVersionsForGroup(group:List[str], partCheck:bool = True) -> List[Game]:

    games:List[Game] = []

    if 'gameover' in str.lower(group[0]):
        print("hello")

    if partCheck:
        #Try to get always a full file without part in it
        withoutPartFiles = list(filter(lambda s: not re.search(r'Part\d',s), group))
        if len(withoutPartFiles)>0:
            group = withoutPartFiles
        else:
            #Our game is all divided in parts, ussually it will be just 2 or 3. Take into account that there can be several
            #versions of same part, so we must re... check for best version for every part
            dict = {}
            for i in range(0,5):
                parts = list(filter(lambda s:  re.search(r'Part%s'%i, s), group))
                if len(parts)>0:
                    bestPart = _getBestVersionsForGroup(parts, False)
                    assert len(bestPart) == 1
                    games.extend(bestPart)
            return games

    bestVer = group[0]
    bestVerRating = _getRatingForZipGame(bestVer)

    # print("*Checking: %s -> %s" % (bestVer,bestVerRating))
    restOfFiles: List[str] = group[1:]
    for file in restOfFiles:
        currentVerRating = _getRatingForZipGame(file)
        # print("*Checking: %s -> %s" % (game.absPath, currentVerRating))
        if currentVerRating > bestVerRating:
            bestVer = file
            bestVerRating = currentVerRating

    # print("Selected: %s with %s" % (bestVer.absPath, bestVerRating))

    game:Game = Game(bestVer, _getNameToCompare(bestVer,0), None)

    return [game]

def writeZipFilesToAnotherZip(src_zip, dst_zip, file_subset_list):
    with zipfile.ZipFile(src_zip, "r", compression=zipfile.ZIP_DEFLATED) as src_zip_archive:
        with zipfile.ZipFile(dst_zip, "w", compression=zipfile.ZIP_DEFLATED) as dst_zip_archive:
            for zitem in src_zip_archive.namelist():
                if zitem in file_subset_list:
                    # warning, may blow up memory
                    dst_zip_archive.writestr(zitem,src_zip_archive.read(zitem))
def exportGames(gamesOutputFolder:str, imgsOutputFolder:str, games:List[Game]):
    for game in games:
        moreThanOnFile = _doesZipContainsMoreThanOneLoadableFile(game.gamePath)
        if moreThanOnFile:
            # Open zip and export files and compress them
            filesToUnzip = _getLoadableFilesInZip(game.gamePath)
            print("From file %s we are unzipping -> %s. We will rename fiels acording to images too..." % (game.gamePath, filesToUnzip))

            for fileToUnzip in filesToUnzip:
                print("# Unzipping file %s",fileToUnzip)
                targetFile: str = os.path.join(gamesOutputFolder, os.path.basename(fileToUnzip)+".zip")
                writeZipFilesToAnotherZip(game.gamePath, targetFile, [fileToUnzip])

            if game.gameImgPath is not None:
                for fileToUnzip in filesToUnzip:
                    targetFile: str = os.path.join(imgsOutputFolder, os.path.basename(fileToUnzip) + ".png")
                    print("# Exporting picture for file %s as %s" % (fileToUnzip, targetFile))
                    img = Image.open(game.gameImgPath)
                    img.save(targetFile, 'png', optimize=True, quality=100)
        else:
            fileName:str = game.getFileName()
            #char:str = str.lower(fileName[0:1])
            if not os.path.exists(gamesOutputFolder):
                os.makedirs(gamesOutputFolder)
            exportPath = os.path.join(gamesOutputFolder, fileName)
            print("# Exporting file %s", exportPath)
            shutil.copyfile(game.gamePath, exportPath)

            if game.gameImgPath is not None:
                print("# Exporting image file %s", exportPath)
                fileName: str = game.getFileName()
                fileName = os.path.splitext(fileName)[0]
                if not os.path.exists(imgsOutputFolder):
                    os.makedirs(imgsOutputFolder)
                targetImage = os.path.join(imgsOutputFolder, os.path.basename(fileName)+".png")
                img = Image.open(game.gameImgPath)
                img.save(targetImage, 'png', optimize=True, quality=100)
            else:
                print("File %s has no image to export..." % fileName);


def _findImageFromCompareName(compareName:str, imgFiles:List):
    for imgFile in imgFiles:
        file = str.lower(os.path.basename(imgFile))
        if str.startswith(file,str.lower(compareName)):
            return imgFile
    return None
def fillScreenshotImgForGames(outputFolder:str, games:List[Game], imgFiles:List[str]):
    imgs:[] = []

    for game in games:
        compareName:str = game.comparableGameName
        gameImgFile = _findImageFromCompareName(compareName, imgFiles)
        game.gameImgPath = gameImgFile
        if game.gameImgPath == None:
            print("Game %s has no img associated." % game.gamePath)

def _serializeGroups(gropus:[]):
    with open("groups.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(gropus)

def _deserializeGroups() -> List[List[str]]:
    data: List[List[str]] = []
    reader = csv.reader(open('groups.csv'))
    for row in reader:
        data.append(row)
    return data

hashedFiles= {}
hashedImgs = {}

validExts = [".tap",".z80",".dsk",".tzx"]

# hash imgs and files
for file in files:
    name = os.path.basename(file)
    gameNameWitExt = os.path.splitext(os.path.basename(file))[0]
    ext = os.path.splitext(gameNameWitExt)[-1];

    if ext not in validExts:
        print("File %s is of a non valid extension. Skipeed." % gameNameWitExt)
        continue;

    char = str.lower(name[0])

    if not char in hashedFiles:
        hashedFiles[char] = []

    hashedFiles[char].append(file)

# hash imgs and files
for img in imgs:
    char = str.lower(img[0])

    if not char in hashedImgs:
        hashedImgs[char] = []

    hashedImgs[char].append(img)

groups: List[List[str]] =[]

groups = []
#groups = _calculateDuplicates(hashedFiles)

#serialize groups if not exist
if not os.path.exists(os.path.join(os.getcwd(),"groups.csv")):
    groups = _calculateDuplicates(hashedFiles)
    _serializeGroups(groups)
else:
    groups = _deserializeGroups()


bestVers:List[Game]=[]

for group in groups:
    gameBestVers:List[Game]= _getBestVersionsForGroup(group)

    gameBestVerStr: str = "["
    for bestVer in gameBestVers:
        gameBestVerStr += bestVer.gamePath + ","
    gameBestVerStr += ']'

    #Make sure we are not returning mixed parts games with no parts (A games is or not a game made of parts)
    results = [x for x in gameBestVers if re.search(r'Part\d', x.getFileName()) == True]

    if (len(results)>0 and (len(results) != len(bestVers) or len(results) == 1)):
        print("[BAD MULTIFILE] %s -> %s" % (group, gameBestVerStr))
    else:
        results = [x for x in gameBestVers if _doesZipContainsMoreThanOneLoadableFile(x.gamePath) == True]


        if len(results) > 0:
            print("* %s -> %s" % (group,gameBestVerStr))
        else:
            print("%s -> %s" % (group, gameBestVerStr))

        bestVers.extend(gameBestVers)


fillScreenshotImgForGames("C:\\Users\\juanjo\\Desktop\\exportedImages", bestVers, imgs)

exportGames("C:\\Users\\juanjo\\Desktop\\exported", "C:\\Users\\juanjo\\Desktop\\exportedImages", bestVers)

'''
for img in imgs:
    imgName: str = os.path.splitext(os.path.basename(img))[0]
    imgNameNoExtension: str = os.path.splitext(imgName)[0]

    groups = {}
    for file in files:
        fileName: str = os.path.splitext(os.path.basename(img))[0]
        matchingFiles:[] = []
        if fileName.startswith(imgNameNoExtension) in file:
            matchingFiles.append(file)

    if len(matchingFiles) > 0:
        groups[imgName] = matchingFiles
        print("%s matched %s" % (imgName, matchingFiles))
'''

