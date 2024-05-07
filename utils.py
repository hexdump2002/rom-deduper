from enum import Enum
import re

class FindOptions(Enum):
    WORD = 0
    REGEX= 1

def findWords(searchWords:[[]], text, trueIfAll=False):

    found = False
    for search in searchWords:
        word = search[0]
        matchFound = False
        if search[1]==FindOptions.WORD:
            result = re.search(rf'\b{word}\b',text, re.IGNORECASE)
            matchFound = result is not None
        elif search[1]==FindOptions.REGEX:
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