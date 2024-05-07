from utils import findWords, FindOptions
from typing import List
import re

'''
def _getStandardRating(name):
    points = 0

    name = name.lower()

    isJap=False
    if findWords([["europe", FindOptions.WORD], ["eur", FindOptions.WORD], ["\(E\)", FindOptions.REGEX]], name): points += 50
    if findWords([["japan", FindOptions.WORD], ["jap", FindOptions.WORD], ["\(J\)", FindOptions.REGEX]], name):   points += 10; isJap=True
    if findWords([["usa", FindOptions.WORD], ["\(U\)", FindOptions.REGEX], ["australia", FindOptions.WORD]], name): points += 30
    if findWords([["world", FindOptions.WORD]], name): points += 20
    if findWords([["beta", FindOptions.WORD]], name): points -=30
    if findWords([["\(proto.*?\)", FindOptions.REGEX]], name): points -= 50
    if findWords([["spain", FindOptions.WORD]], name): points += 100
    if findWords([["\[!\]", FindOptions.REGEX]], name): points += 40
    if findWords([["\[b\d{0,2}\]", FindOptions.REGEX]], name): points -= 40
    if findWords([["\[h\d{0,2}\]", FindOptions.REGEX]], name): points -= 100
    if findWords([["\(UE\)", FindOptions.REGEX], ["\(EU\)", FindOptions.REGEX]], name): points+=50
    if findWords([["\(UJ\)", FindOptions.REGEX], ["(JU)", FindOptions.REGEX]], name): points += 30
    if findWords([["\[a\d{0,2}(?![-\w])\]", FindOptions.REGEX]], name): points-=10
    if findWords([["\[o\d{0,2}(?![-\w])\]", FindOptions.REGEX]], name): points -= 10 #Overdump

    if findWords([["\[t\-eng.*?\]", FindOptions.REGEX]], name):
        points += 50
    elif findWords([["\[t\-spa.*?\]", FindOptions.REGEX]], name): points += 60
    elif findWords([["\[t\-.*?\]", FindOptions.REGEX]], name):
        if isJap:
            points += 40
        else:
            points -=40

    if findWords([["partial", FindOptions.REGEX]], name):
        points-=10

    if findWords([["\[t\d{0,2}(?![-\w])\]", FindOptions.REGEX]], name): points -= 20 #No trainers please

    return points
'''

def buildAllSearchTermsCases(searchTerm:str) -> str:
    return f"\(\s*{searchTerm}\s*\)|\(\s*{searchTerm}\s*|,\s*{searchTerm}\s*|\s*{searchTerm}\s*\)"

def searchAnyGameMetadataToken(searchTerms: List[str], text:str):
    finalRegExStr:str = ""

    i=0
    for searchTerm in searchTerms:
        if i!=0:
            finalRegExStr+="|"

        #If a [x] is passed we will add it directly because it is a rom flag
        if(searchTerm.startswith("\[")):
            finalRegExStr+=searchTerm
        else:
            finalRegExStr+=buildAllSearchTermsCases(searchTerm)

    return  re.search(rf'{finalRegExStr}',text, re.IGNORECASE)

def searchAllGameMetadataToken(searchTerms: List[str], text:str):

    for searchTerm in searchTerms:
        finalRegExStr: str = ""

        # If a [x] is passed we will add it directly because it is a rom flag
        if (searchTerm.startswith("\[")):
            finalRegExStr = searchTerm
        else:
            finalRegExStr = buildAllSearchTermsCases(searchTerm)

        result = re.search(rf'{finalRegExStr}',text, re.IGNORECASE)

        if result is None:
            return False

    return True

def DSFilesRating(name:str) -> int:
    points = 0

    name = name.lower()

    isJap=False

    # Check if we can get a spanish one if not european english if not english...
    if searchAnyGameMetadataToken(["es", "spain"], name):
        points += 1000
    else:
        if searchAllGameMetadataToken(["europe","en"],name):
            points+= 900 # If europe and en exist for this game
        elif searchAnyGameMetadataToken(["usa","U","australia"],name):
            points +=800
        elif searchAnyGameMetadataToken(["en"], name):
            points += 700
        elif searchAnyGameMetadataToken(["europe"],name):
            # we have an european rom but that has no es or en. Get the shortest
            # rom name (we hope to get just the ones with europe and no languages
            points+=600-len(name)
        elif searchAnyGameMetadataToken(["japan","jap","J"],name):
            points +=500

    # b stands for bad dump. and it can be [b] or [b1], [b2].. [bn]
    if searchAnyGameMetadataToken(["beta","proto", "demo", "kiosk","\[b\d*\]"], name): points -=1000
    if searchAnyGameMetadataToken(["rev"],name): points +=100

    return points

def DSValidateGame(name:str ):
    name = name.lower()

    avoidables = ["/my ","barbie", "ds download station", "dreamer series", "drawn to life", "dora ","/disney ",
        "/diva girls", "/club penguin","/clever kids","/charm girls","/bratz","ds spirits","/[BIOS]","ZhuZhu",
        "winx club","(France)", "(Germany)", "(German)", "(Korea)", "Tokuten Ryoku","TOEIC","spongebob","smart girl","smart boy","petz","/paws",
        "monster high","/mon coach","/maru goukaku","/maji de manabu","/littlest pet shop","/let's",
        "/lernen","/layton"]

    for avoidable in avoidables:
        avoidable = avoidable.lower()
        if avoidable.startswith("/"):
            if name.startswith(avoidable[1:]) == True:
                return False
        else:
            if avoidable in name:
                return False

    return True