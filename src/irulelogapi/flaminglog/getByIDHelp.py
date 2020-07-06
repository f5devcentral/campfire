#helper methods for get by ID


import re

def _parse_id(idStr):
    """
    Parses the given id into a list and returns the list
    """

    parsedID = [None,None,None,None,None,None,None]

    tempParse = [None,None,None,None,None,None,None,None,None]
    idStr = idStr.split('.')
    for i in range(0,len(idStr)):
        tempParse[i] = idStr[i]
    
    parsedID[0] = (".".join(tempParse[0:3]))
    
    for i in range(3,len(tempParse)):
        parsedID[i-2] = tempParse[i]

    return parsedID
