import os
import os.path as path
import pathlib
from enum import Enum


class ConvertFileReturn(Enum):
    ConversionError = 0
    UnknownFileFormat = 1
    Success=20

def _convertToChd(filePath:str, outputDir:str) ->ConvertFileReturn:
    currentFolder:str = os.getcwd()
    command:str= '%s/tools/chdman.exe createcd -i "%s" -o "%s"' %(currentFolder,filePath, outputDir)
    print(command)
    result = os.system(command)

    ConvertFileReturn.Success if result == 0 else ConvertFileReturn.ConversionError

def _convertBinCue(filePath:str, outputDir:str) -> ConvertFileReturn:
    result = ConvertFileReturn.Success

    fileName, ext = path.splitext(filePath)
    ext=ext[1:].lower()
    if ext != "bin" or ext != "cue":
        return ConvertFileReturn.UnknownFileFormat
    else:
        if ext==bin:
            #Try to check if we have a cue associated
            cueFileName =fileName+".cue"
            if path.exists(cueFileName):
                result = _convertToChd(cueFileName, outputDir)
            else:
                result = _convertToChd(filePath, outputDir)

            if result is not ConvertFileReturn.Success:
                print("[ERROR] %s could not be converted" % cueFileName)

    return result

def _convertCcdImg(path):
    pass


def _convertIso(filePath, outputPath):
    fileName:str = path.basename(filePath)
    fileName,ext = path.splitext(fileName)
    outputFilePath=path.join(outputPath, fileName+".chd")
    result = _convertToChd(filePath, outputFilePath)
    pass


def _convertFile(filePath:str, outputFilePath:str) -> ConvertFileReturn:
    if not os.path.exists(outputFilePath):
        os.makedirs(outputFilePath)

    fileName, ext = path.splitext(filePath)
    ext = ext[1:].lower()
    if ext == "" or ext == None:
        return ConvertFileReturn.UnknownFileFormat
    else:
        if ext=="cue":
            _convertBinCue(filePath, outputFilePath)
            pass
        if ext=="ccd":
            _convertCcdImg(filePath, outputFilePath)
            pass
        if ext=="img":
            _convertCcdImg(filePath, outputFilePath)
            pass
        if ext=="bin":
            _convertBinCue(filePath, outputFilePath)
            pass
        if ext=="iso":
            _convertIso(filePath,outputFilePath)
            pass
        else:
            return ConvertFileReturn.UnknownFileFormat


def _getImageFiles(searchPath:pathlib.Path):
    filesGenerator = searchPath.glob("*")

    validExtensions = ["iso", "bin", "cue", "img", "ccd", "sub"]
    imgExts = ["iso","img","bin"]
    imgTrackListExts = ["cue", "ccd"]

    validFiles = []
    nonUsableFiles= []


    for file in filesGenerator:
        absPath: str = str(file)
        fileName, ext = path.splitext(absPath)
        ext=ext[1:]
        if ext.lower() not in validExtensions:
            nonUsableFiles.append(absPath)
        elif ext.lower() in validExtensions:
            validFiles.append(absPath)

    gameGroups = []

    while len(validFiles) > 0:
        if len(validFiles) == 1:
            group = []
            group.addGame(validFiles[0])
            gameGroups.append(group)
            break;

        file = validFiles[0]

        fileName, ext = path.splitext(file)

        group = []
        group.append(file)
        for index in range(1, len(validFiles)):
            choice, ext = path.splitext(validFiles[index])
            if choice == fileName:
                group.append(validFiles[index])

        gameGroups.append(group)

        for file in group:
            validFiles.remove(file)

    return gameGroups

def _getFilePoints(filePath:str):
    filename, ext = path.splitext(filePath)
    ext=ext[1:].lower()
    if ext == "cue":
        return 100
    elif ext == "ccd":
        return 70
    elif ext == "bin" or ext == "iso":
        return 40
    elif ext == "img":
        return 30
    elif ext == "sub":
        return 0
    else:
        raise Exception("Unknown extension %s" % ext)
def _getBestFileFormatForConversion(group:[]):
    bestVers:[] = []

    bestVer:str = None
    bestVerPoints:int = 0
    for file in group:
        points:int = _getFilePoints(file)
        if points>bestVerPoints:
            bestVer = file
            bestVerPoints = points

    assert bestVer!=None

    return bestVer

def convert(args):
    sourceFiles=args.source_files
    outputFolder=args.output_folder
    deleteOriginal=args.delete_original

    bestVers:[]=[]
    if path.exists(sourceFiles):
        if path.isdir(sourceFiles):
            print("Generating image file groups...")
            groups = _getImageFiles(sourceFiles)
            print("Calculating best file versions...")
            for group in groups:
                bestVers.append(_getBestFileFormatForConversion(group))

            assert(len(groups) == len(bestVers))

            print("We are going to convert %s games" % len(bestVers))
            print("===================================")
            for bestVer in bestVers:
                print(bestVer)

            for bestVer in bestVers:
                print("Converting file %s" % bestVer)
                _convertFile(bestVer, str(outputFolder))
        else:
            pass


