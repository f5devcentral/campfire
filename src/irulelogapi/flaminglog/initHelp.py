import copy
import json
from . import NestNode
import datetime


def _populate_dict(inputDict, lineStr):
    """
    Takes a single line of iRules tracer data and splits the individual parts of
    it and places the data into the passed dictionary.
    Parameters
    ----------
    inputDict: Dictionary
        The dictionary which the data will be placed into
    lineStr: String
        The single line of iRules tracer data
    """
    splitData = lineStr.split(",")
    i=0
    for key in inputDict:
        if(key=='remote'):
            for key in inputDict['remote']:
                inputDict['remote'][key] = splitData[i]
                i += 1

        elif (key=='local'):
            for key in inputDict['local']:
                inputDict['local'][key] = splitData[i]
                i += 1

        elif (i >= 12):
            #skips over 'exittime' key, will be filled in later
            break
        
        else:
            inputDict[key] = splitData[i]
            i += 1

def _trim_occ_str(inputStr):
    """
    Trims the superfluous charaters off the occurrence type name to make the
    string shorter and more easily identifiable.
    Parameters
    ----------
    inputStr: String
        The full string that will be trimmed
    Return
    ----------
    tempStr: String
        The new shorter name of the occurrecne type
    """
    inputStr = inputStr.split('_',1)[1]
    if("BYTECODE" in inputStr):
        inputStr = inputStr.split('_')[1]
    elif("VAR" in inputStr):
        return inputStr
    else:
        inputStr = inputStr.rpartition('_')[0]

    inputStr = inputStr.replace("_","")
    return inputStr

def _update_id(currentID, level, numChildren):
    """
    Updates the running occurrence ID
    """
    currentID[level] = numChildren
    tempStr = currentID[0]
    for i in range(1,level+1):
        tempStr = tempStr + '.' + str(currentID[i])
    return tempStr




def _dump_nest(rootNode, resultList, isRoot = True):
    """
    Dumps the contents of a NestNodes (custom class) to a python dictionary.
    Does so by recursing through the children of every node starting with the
    root node.
    Parameters
    ----------
    rootNode: NestNode
        The node at which the information dump will begin
    resultList: List[Dictionary]
        The list which will contain all the top level occurrence dictionaries.
        Those dictionaries then contain a list with all their children and so on
    isRoot: Boolean (Default = True)
        Is used to start the first recursive call differently from the others
    """

    formatDict = {
        "ID":None,
        "info":None,
        "varData":[],
        "nest":[]
    }

    helpIndex = 0
    for child in rootNode.children:
        formatDict['info'] = child.info
        formatDict['ID'] = child.ID

        #trim occtype
        formatDict['info']['occtype'] = _trim_occ_str(formatDict['info']['occtype'])

        #adds new dictionary to list
        resultList.append(copy.deepcopy(formatDict))
        #recurses down another level to next child node
        _dump_nest(child, resultList[helpIndex]['nest'])
        helpIndex += 1


def _create_nest(rootNest, dataList, levelDict, filename):
    """
    Takes the data parsed from the iRule log file and strucutres it into a
    nested format using NestNode (custom class) linked list/tree structure.
    Pairs all entry and exit occurrences into a single NestNode. Then calls
    _dump_nest() to convert the NestNode structure into a list which is then
    dumped to a JSON file.
    Parameters
    ----------
    rootNest: NestNode
        The first node in the NestNode structure
    dataList: List[Dictionary]
        Contains data for every occurrence entry and exit separately. Not
        properly nested with parents and children
    bytecodeLevel: int
        Used to properly navigate the nested strucutre based on which events are
        logged above BYTECODE in the hierarchy.
    varLevel: int
        Used to properly navigate the nested strucutre based on which events are
        logged above VAR_MOD in the hierarchy.
    filename: String
        What the resulting file will be named. Also used to properly assign an
        ID to each occurrence
    """
    errorCode = 0
    currentNode = rootNest
    testD = []
    idStart = filename.rpartition('.')[0]
    currentID = [idStart, 0, 0, 0, 0, 0, 0]

    for dataDict in dataList:
        #print(dataDict)
        if('ENTRY' in dataDict['occtype']):
            nextNode = NestNode.NestNode()
            nextNode.parent = currentNode
            nextNode.level = currentNode.level + 1


            levelKeyStr = _trim_occ_str(dataDict['occtype'])
            if(nextNode.level != levelDict[levelKeyStr]):
                return None, 1001

            nextNode.info = copy.deepcopy(dataDict)
            currentNode.children.append(nextNode)

            #computes ID, does it on ENTRY and BYTECODE only
            nextNode.ID = _update_id(currentID, nextNode.level, len(currentNode.children))
            currentNode = nextNode


        elif('EXIT' in dataDict['occtype']):
            
            if("BYTECODE" in currentNode.info['occtype']):
                #if previous node was bytecode
                currentNode = currentNode.parent
                currentNode.info['exittime'] = dataDict['entrytime']
                currentNode = currentNode.parent

            else:
                currentNode.info['exittime'] = dataDict['entrytime']
                levelKeyStr = _trim_occ_str(dataDict['occtype'])
                if(currentNode.level != levelDict[levelKeyStr]):
                    return None, 1001

                currentNode = currentNode.parent
            
        elif('BYTECODE' in dataDict['occtype']):

            if(currentNode.level < levelDict['BYTECODE']):
                #if previous node was above bytecode in hierarchy
                nextNode = NestNode.NestNode()
                nextNode.parent = currentNode
                nextNode.level = currentNode.level + 1
                nextNode.info = copy.deepcopy(dataDict)
                currentNode.children.append(nextNode)

                nextNode.ID = _update_id(currentID, nextNode.level, len(currentNode.children))
                currentNode = nextNode

                levelKeyStr = _trim_occ_str(dataDict['occtype'])
                if(currentNode.level != levelDict[levelKeyStr]):
                    return None, 1001

            elif(currentNode.level == levelDict['BYTECODE']):
                #if previous node was BYTECODE
                nextNode = NestNode.NestNode()
                nextNode.parent = currentNode.parent
                nextNode.level = currentNode.level
                nextNode.info = copy.deepcopy(dataDict)
                currentNode.parent.children.append(nextNode)

                nextNode.ID = _update_id(currentID, 
                    nextNode.level, len(currentNode.parent.children))
                currentNode = nextNode

                levelKeyStr = _trim_occ_str(dataDict['occtype'])
                if(currentNode.level != levelDict[levelKeyStr]):
                   return None, 1001 

            else:
                #print("BREAKING")
                #if VAR was the last occurrence
                #TODO: Add error hadndling < BYTECODE here
                return None, 1001
                pass
        elif('VAR' in dataDict['occtype']):
            nextNode = NestNode.NestNode()
            nextNode.info = copy.deepcopy(dataDict)
            nextNode.level = currentNode.level + 1
            nextNode.parent = currentNode
            currentNode.children.append(nextNode)

            levelKeyStr = _trim_occ_str(dataDict['occtype'])
            if(nextNode.level != levelDict[levelKeyStr]):
               return None, 1001 

            nextNode.ID = _update_id(currentID, 
                nextNode.level, len(currentNode.children))
            #only append nextNode b/c there is no nesting in VAR type
            
        else:
            #print("TERRIBLE ERROR")
            #TODO: Add error handling here
            pass
    resultList = []
    _dump_nest(rootNest, resultList)
    with open(filename,'w') as outfile:
        json.dump(resultList, outfile)

    return resultList, errorCode

def _generate_filename(wantedOccList = None):
    """
    Generates a unique filename for a JSON file. Filename is based in following
    form: "wantedOcc0.wantedOcc1(date--timestamp).json"
    Parameters
    ----------
    wantedOccList: List[String] (Default = None)
        Contains all the wanted occurrence types. Each of which will be
        prepended to the filename
    """

    directoryName = "StructLogs/"
    wantedStr = ""

    if (wantedOccList is not 'None'):
        wantedStr = "-"
        for occ in wantedOccList:
            wantedStr += ('-'+occ)
        wantedStr = wantedStr[2::]

    myDateTime = str(datetime.datetime.utcnow())
    myDateTime = myDateTime.replace(' ', '--')
    myDateTime = myDateTime.replace(':', '-')

    filename = directoryName + wantedStr+ '(' + myDateTime + ')' + '.json'
    return filename

def _check_nest(rootNode, hNum = 0):
    """
    Prints to the console all of the occurrences as they are properly nested.
    Used to check the validity of NestNode structure
    Parameters
    ----------
    rootNode: NestNode
        The root node in the nest node tree/linked list strucutre
    hNum: int (Default = 0)
        Used to calculate the correct number of \t characters for the print out
    """
    for child in rootNode.children:
        print(("\t"*hNum) + child.info['occtype'] + ", " + child.info['occvalue'] + ", " + str(child.level))
        _check_nest(child, hNum + 1)

def _print_list(myList, level=0):
    """
    Prints contents of list that contains nested dicts
    """

    for item in myList:
        print(("\t"*level) + item['info']['occtype'])
        _print_list(item['nest'], level + 1)



