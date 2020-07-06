import copy
import json
import datetime
import os
import subprocess
import re
import operator
from cairosvg import svg2png



from . import NestNode
from . import LogicNode
from . import initHelp
from . import getByIDHelp
from . import svgHelp
from . import queryHelp

def make_json(inputFile, wantedOccList='None'):
    """
    Converts the output trace from the iRule profiler into a JSON formatted
    list. Strucutres and organizes the data in the passed iRule log file. If
    wantedOccList is None all occ-types are kept. Otherwise only those which are
    included in wantedOccList are kept.\n
    Parameters
    ----------
    inputFile: String
        The path aand name of the input iRule log file
    wantedOccList: List[String]
        (Default Value = None) A list of the wanted occ-types. Will keep those
        types which are in the list and filter out all others. Valid inputs in
        the list include: EVENT, RULE, RULEVM, BYTECODE, CMDVM, CMD,VAR_MOD
    Return
    ----------
    outName: String
        The path and name of a JSON file which contains the contents of the
        structured and orgnaized data
    outList: List[Dictionary]
        Contains identical contents to outName but is in list form
    errorCode: int
        Indicated whether the data was successfully converted. If successful
        errorCode=0. Otherwise will output a custom errorCode.

    """

    #if no queryStr is given then returns all content unfiltered
    #handles if wantedOccList is passed as a string with list content
    if(wantedOccList != 'None'):
        if(isinstance(wantedOccList, str)):
            wantedOccList = wantedOccList.replace(' ','')
            wantedOccList = wantedOccList.replace("'","")
            wantedOccList = wantedOccList[1:-1]
            wantedOccList = wantedOccList.split(',')

    if(isinstance(wantedOccList, list)):
        pass

    elif(wantedOccList == 'None'):
        pass

    else:
        typeStr = str(type(wantedOccList))
        errStr = typeStr + (" object is not of type list or str:"
                " wantedOccList must be of type list or str")
        raise Exception(errStr)

    validOccListVals = [
            'EVENT',
            'RULE',
            'RULEVM',
            'BYTECODE',
            'CMDVM',
            'CMD',
            'VAR_MOD'
    ]
    
    #checks that all values wanted are valid
    if(wantedOccList is not 'None'):
        for occ in wantedOccList:
            if(occ not in validOccListVals):
                errStr = occ + ' :is not a valid entry in wantedOccList'
                raise Exception(errStr)

    if(wantedOccList is 'None'):
        wantedOccList = [
                'EVENT',
                'RULE',
                'RULEVM',
                'BYTECODE',
                'CMDVM',
                'CMD',
                'VAR_MOD'
        ]
    

    errorCode = 0
    #initialize variables

    try:
        rawLogHandle = open(inputFile)
    except FileNotFoundError:
        errStr = inputFile + ':was not found'
        raise Exception(errStr)

    logHandle = open('static/plog.txt', 'w+')

    grepList = [ ',RP_EVENT_ENTRY,',
                    ',RP_EVENT_EXIT,',
                    ',RP_RULE_ENTRY,',
                    ',RP_RULE_EXIT,',
                    ',RP_RULE_VM_ENTRY,',
                    ',RP_RULE_VM_EXIT,',
                    ',RP_CMD_VM_ENTRY,',
                    ',RP_CMD_VM_EXIT,',
                    ',RP_CMD_ENTRY,',
                    ',RP_CMD_EXIT,',
                    ',RP_CMD_BYTECODE,',
                    ',RP_VAR_MOD,'
    ]
    grepString = '|'.join(grepList)
    getTracerProc = subprocess.Popen(
            ['grep', '-E', grepString],
            stdin=rawLogHandle,
            stdout=logHandle
    )

    getTracerProc.wait()
    logHandle.close()
    rawLogHandle.close()
    logHandle = open('static/plog.txt')

    beginTraceFound = False
    allDicts = []   #will contain all data in unnested form

    #used to help organize pairs since bytecode doesn't have one
    levelCheckDict = {
            'EVENT':False,
            'RULE':False,
            'RULEVM':False,
            'BYTECODE':False,
            'VAR_MOD':False,
            'CMDVM':False,
            'CMD':False
    }

    #used to organize data from log file
    sampleDict = {
        'entrytime':None,
        'occtype':None,
        'virtserver':None,
        'occvalue':None,
        'tmmpid':None,
        'flowid':None,
        'remote':{'ip':None, 'port':None, 'routdomain':None},
        'local':{'ip':None, 'port':None, 'routdomain':None},
        'exittime':None,
        'rawexectime':None,
        'sumchildren':None,
        'realexectime':None,
        'irule':None,
        'eventval':None
    }

    #creates output file and names it appropriately
    filename = initHelp._generate_filename(wantedOccList)
    f = open(filename, 'w+')
    
    bytecodeLevel = 1
    varLevel = 1

    currentRule = None
    currentEvent = None

    entryExitCount = {
            'EVENT':{'NumEntry':0, 'NumExit':0},
            'RULE':{'NumEntry':0, 'NumExit':0},
            'RULEVM':{'NumEntry':0, 'NumExit':0},
            'CMDVM':{'NumEntry':0, 'NumExit':0},
            'CMD':{'NumEntry':0, 'NumExit':0}
    }

    #iterates through the log file
    for line in logHandle:

        if(("ENTRY" in  line) | ("BYTECODE" in line) | ("VAR_MOD" in line) |
                beginTraceFound):

            beginTraceFound = True
            #parses line, and takes off edge spaces
            traceLine = line.split(':', 3)[3][1:-1]
            checkerDict = sampleDict
            #formats data into dictionary
            commaCount = traceLine.count(',')
            if(commaCount > 11):
                f.close()
                logHandle.close()
                return None, None, 1002
            if(commaCount < 11):
                f.close()
                logHandle.close()
                return None, None, 1003


            initHelp._populate_dict(checkerDict,traceLine)
            
            #sets the irule field of the dictionary for each occurrence
            if('RULE' in checkerDict['occtype']):
                currentRule = checkerDict['occvalue']

            if('EVENT' not in checkerDict['occtype']):
                checkerDict['irule'] = currentRule
            else:
                checkerDict['irule'] = None

            #sets the eventval of the dictionary for each occurrence
            if('EVENT' in checkerDict['occtype']):
                currentEvent = checkerDict['occvalue']
            checkerDict['eventval'] = currentEvent

            tempOccStr = initHelp._trim_occ_str(checkerDict['occtype'])

            levelCheckDict[tempOccStr] = True

            #keeps track of number of entries and exits per type
            if((tempOccStr != 'BYTECODE') and (tempOccStr != 'VAR_MOD')):
                if('ENTRY' in checkerDict['occtype']):
                    entryExitCount[tempOccStr]['NumEntry'] += 1
                if('EXIT' in checkerDict['occtype']):
                    entryExitCount[tempOccStr]['NumExit'] += 1
            

            #only appends formatted dict if part of wanted occurrences
            if(wantedOccList is not 'None'):
                #tempOccStr = initHelp._trim_occ_str(checkerDict['occtype'])
                if(tempOccStr in wantedOccList):
                    allDicts.append(copy.deepcopy(checkerDict))
            else:
                allDicts.append(copy.deepcopy(checkerDict))

    #checks the final entry exit counts, imbalance returns error code 1000
    for key in entryExitCount:
        if(entryExitCount[key]['NumEntry'] != entryExitCount[key]['NumExit']):
            logHandle.close()
            f.close()
            return None, None, 1000
    
    levelSetter = {
            'EVENT':[],
            'RULE':['EVENT'],
            'RULEVM':['EVENT', 'RULE'],
            'BYTECODE':['EVENT', 'RULE', 'RULEVM'],
            'CMDVM':['EVENT', 'RULE', 'RULEVM', 'BYTECODE'],
            'CMD':['EVENT', 'RULE', 'RULEVM', 'BYTECODE', 'CMDVM'],
            'VAR_MOD':['EVENT', 'RULE', 'RULEVM', 'BYTECODE']
    }

    levelDict = {
            'EVENT':None,
            'RULE':None,
            'RULEVM':None,
            'BYTECODE':None,
            'CMDVM':None,
            'CMD':None,
            'VAR_MOD':None
    }

    for key in levelDict:
        if((levelCheckDict[key]) and (key in wantedOccList)):
            levelDict[key] = 1
            for occ in levelSetter[key]:
                if(levelCheckDict[occ] and (occ in wantedOccList)):
                        levelDict[key] += 1

    if(levelDict['BYTECODE'] == 1):
        f.close()
        logHandle.close()
        return None, None, 1004

    #forms nested occurrence structure
    rootNode = NestNode.NestNode()
    dataList, errorCode = initHelp._create_nest(rootNode, allDicts, levelDict, filename)

    
    logHandle.close()
    f.close()
    if(errorCode != 0):
        return None, None, errorCode

    return filename, dataList, errorCode

def cleanup():
    """
    Deletes all files created by the API.
    """

    filesToDelete = [
            'static/myflame1Combined.svg',
            'static/myflame1Separate.svg',
            'static/myflame2Combined.svg',
            'static/myflame2Separate.svg',
            'static/diff1.svg',
            'static/diff2.svg',
            'static/onlydiff.svg',
            'static/myfold1Com.folded',
            'static/myfold1Sep.folded',
            'static/myfold2Com.folded',
            'static/myfold2Sep.folded',
            'static/halfFold.folded',
            'static/plog.txt',
    ]

    #removes all temp logs
    for myfile in os.listdir('StructLogs/'):
        filepath = os.path.join('StructLogs/', myfile)

        try:
            if(os.path.isfile(filepath)):
                os.unlink(filepath)
        except Exception as e:
            print(e)


    for myfile in filesToDelete:
        try:
            if(os.path.exists(myfile)):
                os.remove(myfile)
        except Exception as e:
            print(e)

def remove_png_files(folder = '.'):
    """
    Removed all png files from the given folder. If no folder is specified the
    current working directory will be used\n
    Parameters
    ----------
    folder: String
        (Default Value = '.') The folder from which all .png files will be
        deleted.
    """

    if(folder != '.'):
        folder += '/'

    for myfile in os.listdir(folder):
        filepath = os.path.join(folder, myfile)

        try:
            if(myfile.endswith('.png')):
                os.unlink(filepath)
        except Exception as e:
            print(e)


def make_svg(contentVar1, contentVar2 = None):
    """
    Creates Flame Graphs based on JSON formatted content passed to it. If
    contentVar2 is None then 2 Flame Graphs will be created. One showing a view
    where function calls with the same name are combined into a single box. And
    another where each individual call is separated no matter what and the
    calls are all in chronological order. If another list is passed in
    contentVar2 then 7 different Flame Graphs are created. See README for more
    details.\n
    Parameters
    ----------
    contentVar1: List[Dictionary]
        The JSON formatted content of before set of data if contentVar 2 is
        passed. If contentVar2 is None then it will be the only dataset.
    contentVar2: List[Dictionary]
        (Default Value = None) The JSON formatted content of the after dataset
    Return
    ----------
    exitBool: Boolean
        True if the Flame Graphs were succesfully created. False otherwise
    fileDict: Dictionary
        Each key is the name and path of the generated .svg files. The value of
        each key is the contents of that file as a String. The default value
        with each key is None. If a file is not created in that run of make_svg
        its associated value will be None in fileDict
    """
    
    if(not(isinstance(contentVar1, list))):
        errmsg = "Passed value must be a list"
        raise Exception(errmsg)

    if(contentVar2 is not None):
        if(not(isinstance(contentVar2, list))):
            errmsg = "Passed value must be a list"
            raise Exception(errmsg)

    #compute path to call flamegraph
    cwd = os.getcwd()
    filePath = os.path.dirname(os.path.abspath(__file__))
    cwd = cwd.split('/')
    filePath = filePath.split('/')
    
    finalPath = []
    for item in filePath:
        if item not in cwd:
            finalPath.append(item)
    finalPath = '/'.join(finalPath)
    finalPath = './' + finalPath + '/FlameGraph/'

    flameCmd = finalPath + 'flamegraph.pl'
    diffCmd = finalPath + 'difffolded.pl'

    defaultFlameOptions = ['--minwidth', '0']

    beforeFoldNameCom = 'static/myfold1Com.folded'
    beforeFoldNameSep = 'static/myfold1Sep.folded'
    afterFoldNameCom = 'static/myfold2Com.folded'
    afterFoldNameSep = 'static/myfold2Sep.folded'
    flame1NameSep = 'static/myflame1Separate.svg'
    flame2NameSep = 'static/myflame2Separate.svg'
    flame1NameCom = 'static/myflame1Combined.svg'
    flame2NameCom = 'static/myflame2Combined.svg'
    diff1Name = 'static/diff1.svg'
    diff2Name = 'static/diff2.svg'
    onlyDiffName = 'static/onlydiff.svg'

    fileStrDict = {
            flame1NameSep:None,
            flame2NameSep:None,
            flame1NameCom:None,
            flame2NameCom:None,
            diff1Name:None,
            diff2Name:None,
            onlyDiffName:None,
    }

    exitBool = True
    if(contentVar2 is None):
        #only make normal flamegraph
        foldedName1Com = 'static/myfold1Com.folded'
        foldedName1Sep = 'static/myfold1Sep.folded'

        svgHelp._make_folded(contentVar1, foldedName1Com, False)
        svgHelp._make_folded(contentVar1, foldedName1Sep, True)

        flameExit = svgHelp._create_flamegraph(
                foldedName1Com,
                flame1NameCom,
                defaultFlameOptions
        )

        if(flameExit != 0):
            exitBool = False


        flameExit = svgHelp._create_flamegraph(
                foldedName1Sep,
                flame1NameSep,
                defaultFlameOptions + ['--flamechart']
        )

        if(flameExit != 0):
            exitBool = False

        if(exitBool):
            flameHandle1 = open(flame1NameCom, 'r')
            fileStrDict[flame1NameCom] = flameHandle1.read()
            flameHandle1.close()
            flameHandle1 = open(flame1NameSep, 'r')
            fileStrDict[flame1NameSep] = flameHandle1.read()
            flameHandle1.close()

        else:
            fileStrDict[flame1NameCom] = "Failed to create FlameGraph"
            fileStrDict[flame1NameSep] = "Failed to create FlameGraph"

        return exitBool, fileStrDict

    else:
        makeDiff = True
        #puts content into before and after folded files
        svgHelp._make_folded(contentVar1, beforeFoldNameCom, False)
        svgHelp._make_folded(contentVar1, beforeFoldNameSep, True)
        svgHelp._make_folded(contentVar2, afterFoldNameCom, False)
        svgHelp._make_folded(contentVar2, afterFoldNameSep, True)

        exitCodes = []
        
        #create combined flamegraphs
        code = svgHelp._create_flamegraph(
                beforeFoldNameCom,
                flame1NameCom,
                defaultFlameOptions
        )
        exitCodes.append(code)
       
        code = svgHelp._create_flamegraph(
                afterFoldNameCom,
                flame2NameCom,
                defaultFlameOptions
        )
        exitCodes.append(code)

        #create separated flamegrpahs
        code = svgHelp._create_flamegraph(
                beforeFoldNameSep,
                flame1NameSep,
                defaultFlameOptions + ['--flamechart']
        )
        exitCodes.append(code)
       
        code = svgHelp._create_flamegraph(
                afterFoldNameSep,
                flame2NameSep,
                defaultFlameOptions + ['--flamechart']
        )
        exitCodes.append(code)

        #create differential flamegraphs
        code = svgHelp._create_diff_flamegraph(
                afterFoldNameCom, 
                beforeFoldNameCom,
                diff1Name,
                [],
                ['--minwidth', '0']
        ) 
        exitCodes.append(code)

        code = svgHelp._create_diff_flamegraph(
                beforeFoldNameCom, 
                afterFoldNameCom,
                diff2Name,
                [],
                ['--minwidth', '0']
        )
        exitCodes.append(code)

        code = svgHelp._create_diff_flamegraph(
                beforeFoldNameCom,
                afterFoldNameCom,
                onlyDiffName,
                ['-d'],
                ['--minwidth', '0'],
                True
        )
        exitCodes.append(code)
        """
        code = svgHelp._connect_svgs(
                diff1Name,
                diff2Name,
                onlyDiffName
        )
        """
        for item in exitCodes:
            if(item != 0):
                exitBool = False

        for key in fileStrDict:

            handle = open(key, 'r')
            fileStrDict[key] = handle.read()
            handle.close()

        if not exitBool:
            for key in fileStrDict:
                fileStrDict[key] = 'Failed to create FlameGraph'

        return exitBool, fileStrDict


def filter_json(mainList, queryStr=None):
    """
    Filters the the content of a JSON formatted list based on the critera of a
    passed query string. If queryStr is None then mainList is returned as is
    with no filtering. Otherwise only occurrences that pass the given queryStr
    will be included in the returned list. For an occurrence to pass the query
    it or any of its children must pass the query\n
    Parameters
    ----------
    mainList: List[Dictionary]
        Contains the JSON formatted iRule profiler data that will be filtered
    queryStr: String
        Determines which occurrences will pass the filter. Has a strict format:
        "(fieldname1==value1)operator(fieldname2==value2)..." The following
        fields are supported: [eventval, irule, remote, local, flow]. Remote,
        and local values require the following format: 
        "ipaddr:port:routedomain" Flow values require: "remoteaddr-localaddr"
        Additionally the following operators are supported: [bitwise OR '|', 
        bitwise AND '&'] See README for examples and extended explanation of
        use
    Return
    ----------
    filteredList: List[Dictionary]
        Contains all occurrence dicitonaries that matched the given query

    """
    #used the list if it is given, used the filename if it is given


    if(not(isinstance(mainList, list))):
        errmsg = "Passed value must be a list"
        raise Exception(errmsg)

    #if no queryStr is given then returns all content unfiltered
    if(queryStr == None):
        return mainList
    if(not(queryHelp.check_filter_str(queryStr))):
        errmsg = "INVALID FILTER STRING: " + str(queryStr)
        raise Exception(errmsg)
    
    #pareses the queryStr into a structure usign LogicNode and BasicLogicNode
    queryNode= queryHelp._parse_query(queryStr)
    #print("eBool: " + str(eBool))
    #reduces data to only those occurrences that pass filter
    queryHelp._filter_data(mainList, queryNode)
    #initHelp._print_list(mainList) #quick check for correctness
    return mainList

def load_json(inputFilename):
    """
    Loads json file into a List\n
    Parameters
    ----------
    filename: String
        The name of the JSON file to load
    Return
    ----------
    mainList: List
        Contains contents of the given file in List form
    """
    with open(inputFilename, 'r') as f:
        mainList = json.load(f)
    return mainList

def save_json(myList, outputFilename):
    """
    Dumps the contents of a list to a JSON file.\n
    Parameters
    ----------
    myList: List[Dictionary]
        The list who's data will be saved to the JSON file
    """

    with open(outputFilename, 'w+') as outfile:
        json.dump(myList, outfile)

def svg_to_png(inputFilename, outputFilename):
    """
    Converts a given svg file to a png image file\n
    Parameters
    ---------
    inputFilename: String
        The name and path of the svg file to be converted
    outputFilename: String
        The name and path of the new .png file
    """
    if(os.path.exists):

        with open(inputFilename, 'r') as file:
            data = file.read()

        try:
            if(os.stat(inputFilename).st_size == 0):
                tempHandle = open(outputFilename, 'w+')
                tempHandle.close()
            else:
                svg2png(bytestring=data,write_to=outputFilename)
        except:
            errStr = "FAILED TO CONVERT SVG TO PNG"
            raise Exception(errStr)
    

def handle_error(errorCode):
    """
    Returns a descriptive error message based on a custom error code.\n
    Parameters
    ----------
    errorCode: int
        The error code for which the error message will be returned
    Returns
    ----------
    errorMsg: String
        The error message related to the errorCode
    """


    errorDict = {
            0:"",
            1000:("Invalid Input File: Unequal number of entries/exits in"
                " input log file\n Check: make sure there are equal number of"
                " entries and exits for each occurrence tpye in the log file."),
            1001:("Invalid Input File: Occurrence found at unexpected"
                " level in input file file\n Check: Make sure the hierarchy of"
                " occurrences in the input file is the following: EVENT, RULE,"
                " RULEVM, BYTECODE, CMDVM, CMD. Items can be missing in this"
                " hierarchy but they must be consistently missing throughout"
                " the entire file."),
            1002:("Invalid Input File: One or more entries in input file" 
            " contain a greater than expected number of data fields"),
            1003:("Invalid Input File: One or more entries in input file"
            " contain a smaller than expected number of data fields"),
            1004:("Invalid Type Filter or Input File: BYTECODE must not be lowest level"
                " filtered.\n Check: EVENT, RULE, and/or RULEVM must be"
                " filtered with BYTECODE. Also check that the log file"
                " contains EVENT, RULE, and/or RULEVM"),
    }

    if(errorCode not in errorDict):
        return "ERROR: Undefined error code: " + str(errorCode)

    return errorDict[errorCode]


def parse_filter_dict(inputDict):
    """
    Converts a dictionary containing Lists in String form into valid queryStr
    for filter_json(). Made for the explicit purpose of parsing a string list
    from Flask.\n
    Parameters
    ----------
    inputDict: Dictionary
        Each key should be a valid fieldname from filter_json. Each value
        should be a String representing a list of Strings.
    Returns
    ----------
    outputDict: Dictionary
        Takes the same format as inputDict except each value is a valid queryStr
        for filter_json()
    """
    
    outputDict = {}
    for key in inputDict:
        qVals = inputDict[key]
        qVals = qVals.replace(' ','')
        qVals = qVals[2:-2]
        qVals = qVals.split(',')

        if(qVals[0] == ''):
            qVals = None

        else:
            inputVals = []
            for item in qVals:
                if(key == 'irule'):
                    item = '/' + item.replace('-','/')
                inputVals.append('(' + key + '==' + item + ')')
            qVals = '|'.join(inputVals)

        outputDict[key] = qVals

    return outputDict



def run_multiple_filters(filterDict, inputList):
    """
    Runs filter_json() once for each fieldname in filterDict and runs each field
    for mulitple values. Does the equivalent of an AND combination between each
    different fieldname.\n
    Parameters
    ----------
    filterDict: Dictionary
        Each key should be valid fieldname in filter_json() and each value
        should be a valid queryStr for the given fieldname.
    inputList: List[Dictionary]
        The JSON formatted iRule log data which will be filtered
    Returns
    ----------
    filteredList: List[Dictionary]
        Contains the data from inputList which passed all the filters
    """

    resultList = copy.deepcopy(inputList)
    
    for key in filterDict:
        resultList = filter_json(resultList, filterDict[key])

    return resultList








