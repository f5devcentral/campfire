import sys, os
import unittest
import json
import flaminglog.logrule as flaminglog
import subprocess
import random
import copy

def trim_str(inputStr):
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


def get_random_filters(valueDict):

    shuffledDict = copy.deepcopy(valueDict)

    for key in shuffledDict:
        random.shuffle(shuffledDict[key])
        #only retains a random number of values in shuffled dict
        numValues = random.randint(0, len(shuffledDict[key]))
        shuffledDict[key] = shuffledDict[key][:numValues]
    
    return shuffledDict

def get_random_combos(comboList):

    shuffledCombos = copy.deepcopy(comboList)
    random.shuffle(shuffledCombos)
    numToApply = random.randint(0,len(shuffledCombos))

    shuffledCombos = shuffledCombos[:numToApply]

    valueDict = {
            'remote':[],
            'local':[],
            'flow':[],
            'irule':[],
            'eventval':[]
    }

    for combo in shuffledCombos:
        for key in valueDict:
            if(combo[key] is not None):
                if(combo[key] not in valueDict[key]):
                    valueDict[key].append(combo[key])


    for key in valueDict:
        numKeep = random.randint(0,len(valueDict[key]))
        valueDict[key] = valueDict[key][0:numKeep]

    return valueDict

def gather_filter_values(logfile):
    valueDict = {
            'remote':[],
            'local':[],
            'flow':[],
            'irule':[],
            'eventval':[]
    }

    comboList = []
    comboDict = {
            'remote':None,
            'local':None,
            'flow':None,
            'irule':None,
            'eventval':None
    }

    tracerFile = isolate_trace(logfile)

    traceHandle = open(tracerFile, 'r')

    for line in traceHandle:

        comboDict = {
                'remote':None,
                'local':None,
                'flow':None,
                'irule':None,
                'eventval':None
        }

        splitLine = line.split(',')
        occType = splitLine[1]
        occValue = splitLine[3]
        remoteAddr = ':'.join(splitLine[6:9])
        localAddrRout = splitLine[11][:-1]
        localAddr=  ':'.join(splitLine[9:11]) + ':' + localAddrRout
        flowAddrs = remoteAddr + '-' + localAddr

        addressDict = {
                'remote':remoteAddr,
                'local':localAddr,
                'flow':flowAddrs
        }


        #add all exisitng event types to possible values
        if('EVENT' in occType):
            comboDict['eventval'] = occValue
            if(occValue not in valueDict['eventval']):
                valueDict['eventval'].append(occValue)

        #add all existing rules to possible values
        if('RULE' in occType):
            comboDict['irule'] = occValue
            if(occValue not in valueDict['irule']):
                valueDict['irule'].append(occValue)

        #for each address check it already added if not add it to list
        for key in addressDict:
            comboDict[key] = addressDict[key]
            if(addressDict[key] not in valueDict[key]):
                valueDict[key].append(addressDict[key])

        comboList.append(copy.deepcopy(comboDict))
    traceHandle.close()

    return valueDict, comboList





def check_event_line(splitLine, valDict, currentEventBool):
    if(len(splitLine) != 12):
        return False, currentEventBool
    actualVal = splitLine[3]
    myEventBool = False
    lineBool = False
    #if enters event set the eventbool and eval line
    if(splitLine[1] == 'RP_EVENT_ENTRY'):

        for searchVal in valDict['eventval']:
            if(searchVal == actualVal):
                myEventBool = True
                lineBool = True

    #on event exit reset event bool but eval line still
    elif(splitLine[1] == 'RP_EVENT_EXIT'):
        myEventBool = False

        for searchVal in valDict['eventval']:
            #print(splitLine[:4])
            if(searchVal == actualVal):
                lineBool = True

    #if not event just go with what the current eventBool is
    else:
        return currentEventBool, None

    return lineBool, myEventBool

def check_irule_line(splitLine, valDict, currentRuleBool):
    if(len(splitLine) != 12):
        return False, currentRuleBool
    actualVal = splitLine[3]
    myRuleBool = False
    lineBool = False
    #if enters event set the eventbool and eval line
    if('RULE' in splitLine[1]):

        if('ENTRY' in  splitLine[1]):

            for searchVal in valDict['irule']:
                if(searchVal == actualVal):
                    myRuleBool = True
                    lineBool = True

        #on event exit reset event bool but eval line still
        elif('EXIT' in splitLine[1]):
            myRuleBool = False

            for searchVal in valDict['irule']:
                #print(splitLine[:4])
                if(searchVal == actualVal):
                    lineBool = True

    #if not event just go with what the current eventBool is
    else:
        return currentRuleBool, None

    return lineBool, myRuleBool

def filter_log(inputFile, valDict):

    inFile = open(inputFile, 'r')

    positiveFilename = 'apitests/tempfiles/goodlines.txt'
    negativeFilename = 'apitests/tempfiles/badlines.txt'
    goodFile = open(positiveFilename, 'w+')
    badFile = open(negativeFilename, 'w+')

    eventBool = False
    ruleBool = False
    ruleExitPassedRule = False
    savedEvent = None

    for line in inFile:
        remotePass = False
        localPass = False
        flowPass = False
        eventPass = False
        alreadyWritten = False
        shortLine = line[:-1]
        splitLine = shortLine.split(',')


        for key in valDict:

            if(key=='remote'):
                actualVal = splitLine[6:9]
                actualVal = ':'.join(actualVal)
                for searchVal in valDict['remote']:
                    if(searchVal == actualVal):
                        remotePass = True
                if(len(valDict['remote']) == 0):
                        remotePass = True

            if(key=='local'):
                actualVal = splitLine[9:12]
                actualVal = ':'.join(actualVal)
                for searchVal in valDict['local']:
                    if(searchVal == actualVal):
                        localPass = True
                if(len(valDict['local']) == 0):
                        localPass = True


            if(key=='flow'):
                actualVal1 = ':'.join(splitLine[6:9])
                actualVal2 = ':'.join(splitLine[9:12])
                actualVal = actualVal1 + '-' + actualVal2
                for searchVal in valDict['flow']:
                    if(searchVal == actualVal):
                        flowPass = True
                if(len(valDict['flow']) == 0):
                        flowPass = True


            if(key=='eventval'):
                if(len(valDict['eventval']) == 0):
                    eventPass = True

                else:
                    eventPass, tempEventBool = check_event_line(
                            splitLine,
                            valDict,
                            eventBool
                    )

                    if(tempEventBool is not None):
                        eventBool = tempEventBool

            #used to add event entry for irule filter
            if(len(splitLine) == 12):
                if(('EVENT' in splitLine[1]) and eventPass):
                    savedEvent = line

            if(key=='irule'):
                if(len(valDict['irule']) == 0):
                    rulePass = True

                else:
                    rulePass, tempRuleBool = check_irule_line(
                            splitLine,
                            valDict,
                            ruleBool
                    )

                    if(tempRuleBool is not None):
                        ruleBool = tempRuleBool

            #used to add event exit for irule filter
            if(len(splitLine) == 12):
                if(splitLine[1] == 'RP_EVENT_EXIT'):
                    if(ruleExitPassedRule):
                        ruleExitPassedRule = False
                        goodFile.write(line)
                        alreadyWritten = True



        if(localPass
            and remotePass
            and flowPass
            and eventPass
            and rulePass
            and not(alreadyWritten)
        ):

            if(len(valDict['irule']) != 0):
                if(rulePass):
                    if(savedEvent is not None):
                        goodFile.write(savedEvent)
                        savedEvent = None

            if(len(splitLine) == 12):
                if('RULE' in splitLine[1]):
                    if('EXIT' in splitLine[1]):
                        ruleExitPassedRule = True

            goodFile.write(line)
        else:
            badFile.write(line)

    goodFile.close()
    badFile.close()
    inFile.close()

    return positiveFilename, negativeFilename

def get_count(filename):
   
    countDict = {
            'EVENT':0,
            'RULE':0,
            'RULEVM':0,
            'BYTECODE':0,
            'CMDVM':0,
            'CMD':0,
            'VAR_MOD':0
    }

    for key in countDict:
        searchString = '"' + key + '"'
        grepFail = False
        try:
        
            grepCountStr = subprocess.check_output(
                ['grep', '-o', '-i', searchString, filename]
            )
            grepCountStr = grepCountStr.decode('utf-8')

            countStr = subprocess.check_output(
                    ['wc', '-l'],
                    universal_newlines=True,
                    input=grepCountStr
            )
        
        #if grep finds nothing
        except subprocess.CalledProcessError:
            grepFail = True


        #if grep finds nothing set count to 0
        if(grepFail):
            countDict[key] = 0
        else:
            countDict[key] = int(countStr[:-1])

    return countDict


def get_log_count(filename):

    countDict = {
            'EVENT':0,
            'RULE':0,
            'RULEVM':0,
            'BYTECODE':0,
            'CMDVM':0,
            'CMD':0,
            'VAR_MOD':0
    }

    typeNameDict = {
            'EVENT':'RP_EVENT_ENTRY',
            'RULE':'RP_RULE_ENTRY',
            'RULEVM':'RP_RULE_VM_ENTRY',
            'BYTECODE':'RP_CMD_BYTECODE',
            'CMDVM':'RP_CMD_VM_ENTRY',
            'CMD':'RP_CMD_ENTRY',
            'VAR_MOD':'RP_VAR_MOD'
    }


    for key in countDict:
        
        searchString = typeNameDict[key]
        grepFail = False
        try:
        
            grepCountStr = subprocess.check_output(
                ['grep', '-o', '-i', '-E', searchString, filename]
            )
            grepCountStr = grepCountStr.decode('utf-8')

            countStr = subprocess.check_output(
                    ['wc', '-l'],
                    universal_newlines=True,
                    input=grepCountStr
            )
        
        #if grep finds nothing
        except subprocess.CalledProcessError:
            grepFail = True


        #if grep finds nothing set count to 0
        if(grepFail):
            countDict[key] = 0
        else:
            countDict[key] = int(countStr[:-1])

    return countDict


def isolate_trace(inputLog):


    logFile = open(inputLog, 'r')
    tempName = 'apitests/tempfiles/tempFile.txt'
    tracerLog = open(tempName, 'w+')
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
            stdin=logFile,
            stdout=tracerLog
    )
    getTracerProc.wait()
    tracerLog.close()
    logFile.close()
    
    return tempName

def get_levels(filename):

    levelSetter = {
            'EVENT':[],
            'RULE':['EVENT'],
            'RULEVM':['EVENT', 'RULE'],
            'BYTECODE':['EVENT', 'RULE', 'RULEVM'],
            'CMDVM':['EVENT', 'RULE', 'RULEVM', 'BYTECODE'],
            'CMD':['EVENT', 'RULE', 'RULEVM', 'BYTECODE', 'CMDVM'],
            'VAR_MOD':['EVENT', 'RULE', 'RULEVM', 'BYTECODE']
    }

    typeExists = {
            'EVENT':False,
            'RULE':False,
            'RULEVM':False,
            'BYTECODE':False,
            'CMDVM':False,
            'CMD':False,
            'VAR_MOD':False
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

    tempName = isolate_trace(filename)
    tracerLog = open(tempName, 'r')

    for line in tracerLog:
        splitLine = line.split(',')
        tempTypeStr = trim_str(splitLine[1])
        if tempTypeStr in typeExists:
            typeExists[tempTypeStr] = True

    tracerLog.close()
    
    #compute levels for each occurrence type
    for key in typeExists:
        if(typeExists[key]):
            levelDict[key] = 1
            for occ in levelSetter[key]:
                if(typeExists[occ]):
                    levelDict[key] += 1
    return levelDict

def make_verified_json(inputFile, valueDict):

    goodLog, badLog = filter_log(inputFile, valueDict)
    goodName, goodList, goodErrorCode = flaminglog.make_json(goodLog)
    #badName, badList, badErrorCode = flaminglog.make_json(badLog)

    countDict = get_count(goodName)
    levelDict = get_levels(goodLog)
    
    return goodName, countDict, levelDict

def get_names_recurse(currentName, nameList, dataList, nameIndex = 0):

    for item in dataList:
        if(item['info']['occtype'] == 'VAR_MOD'):
            #do not add 'VAR_MOD to trace
            pass
        else:
            currentName[nameIndex] = item['info']['occtype']
            idNum = item['ID'].split('.')[-1]
            currentName[nameIndex] += '-' + item['info']['occvalue']
            nameList.append(currentName[nameIndex])
            
            get_names_recurse(currentName, nameList, item['nest'], nameIndex + 1)


def get_all_occ_names(jsonList):

    nameList = []
    currentName = [None, None, None, None, None, None]

    get_names_recurse(currentName, nameList, jsonList)

    nameDict = {}
    for name in nameList:
        nameDict[name] = False
    return nameDict

def check_names_in_svg(nameDict, inputsvg):

    infile = open(inputsvg, 'r')

    for line in infile:
        for name in nameDict:
            if(name in line):
                nameDict[name] = True

    infile.close()

    for name in nameDict:
        if(not(nameDict[name])):
            return False

    return True


def create_verified_log(rawlog, filterList):

    traceFile = isolate_trace(rawlog)
    
    filterLogName = 'tempfilterlog.txt' 
    traceHandle = open(traceFile, 'r')
    filteredLog = open(filterLogName, 'w+')
    for line in traceHandle:
        splitLine = line.split(',')
        for item in filterList:
            if(item == trim_str(splitLine[1])):
                filteredLog.write(line)

    traceHandle.close()
    filteredLog.close()

    levels = get_levels(filterLogName)
    count = get_log_count(filterLogName)

    outName, outList, errcode = flaminglog.make_json('tempfilterlog.txt')

    return outList, levels, count



def get_random_filter():

    baseFilter = [
            'EVENT',
            'RULE',
            'RULEVM',
            'BYTECODE',
            'CMDVM',
            'CMD',
            'VAR_MOD'
    ]

    random.shuffle(baseFilter)
    randLen = random.randint(0,len(baseFilter))
    baseFilter = baseFilter[0:randLen]

    return baseFilter

def remove_unwanted_lines(inputFile, outputFile, filterTypes):


    grepDict = {
            'EVENT':[',RP_EVENT_ENTRY,',',RP_EVENT_EXIT,'],
            'RULE':[',RP_RULE_ENTRY,',',RP_RULE_EXIT,'],
            'RULEVM':[',RP_RULE_VM_ENTRY,',',RP_RULE_VM_EXIT,'],
            'BYTECODE':[',RP_CMD_BYTECODE,'],
            'CMDVM':[',RP_CMD_VM_ENTRY,',',RP_CMD_VM_EXIT,'],
            'CMD':[',RP_CMD_ENTRY,',',RP_CMD_EXIT,'],
            'VAR_MOD':[',RP_VAR_MOD,']
    }

    grepVDict = {}

    for key in grepDict:
        if key not in filterTypes:
            grepVDict[key] = grepDict[key]

    if(any(grepVDict)):
        grepString = ""

        for key in grepVDict:
            tempStr = '|'.join(grepVDict[key])
            grepString += '|' + tempStr

        #get rid of extra '|' character
        grepString = grepString[1:]

    else:
        return inputFile

    inputFileHandle = open(inputFile, 'r') 
    outputFileHandle = open(outputFile, 'w+')

    grepVProc = subprocess.Popen(
            ['grep', '-v', '-E', grepString],
            stdin=inputFileHandle,
            stdout=outputFileHandle
    )
    grepVProc.wait()

    inputFileHandle.close()
    outputFileHandle.close()

    return outputFile

def get_rule_dict(inputFile, wantedTypes):

    traceName = isolate_trace(inputFile)
    traceHandle = open(traceName, 'r')

    ruleDict = {}
    currentRule = None
    currentRangePair = []

    currentLine = 0
    previousLine = 0

    enterRule = False
    exitRule = False

    for line in traceHandle:

        splitLine = line.split(',')
        occType = splitLine[1]
        occValue = splitLine[3]

        if('RULEVM' == trim_str(occType)):
            currentRule = occValue

            if currentRule not in ruleDict:
                ruleDict[currentRule] = []

            if('ENTRY' in occType):
                currentRangePair = []
                enterRule = True
            elif('EXIT' in occType):
                exitRule = True
                if(len(currentRangePair) == 1):
                    currentRangePair.append(previousLine)
                    ruleDict[currentRule].append(currentRangePair.copy())
            else:
                print("ERROR ELSE CLAUSE")

        else:
            if(('EXIT' not in occType) and ('RULE' not in occType)):
                if(trim_str(occType) in wantedTypes):
                    if(enterRule):
                        enterRule = False
                        currentRangePair.append(currentLine)
                    previousLine = currentLine
                    currentLine += 1
    traceHandle.close()
    return ruleDict


def get_current_rule(index, ruleDict):

    pairMatch = False
    for key in ruleDict:
        for pair in ruleDict[key]:
            if((index >= pair[0]) and (index <= pair[1])):
                pairMatch = True
                return key

    return None


def add_rule_back(inputList, ruleDict, currentIndex=0):

    for item in inputList:

        myRule = get_current_rule(currentIndex, ruleDict)
        item['info']['irule'] = myRule
        currentIndex += 1
        currentIndex = add_rule_back(item['nest'], ruleDict, currentIndex)

    return currentIndex


def adjust_event_rule(logFile, dataList, wantedTypes):

    if(('EVENT' not in wantedTypes)):
        eventDict = get_event_dict(logFile, wantedTypes)
        #print(eventDict)
        add_event_back(dataList, eventDict)

    if(len(wantedTypes) == 1 and ('EVENT' in wantedTypes)):
        pass
    else:
        if(('RULE' not in wantedTypes) and ('RULEVM' not in wantedTypes)):
            ruleDict = get_rule_dict(logFile, wantedTypes)
            #print(ruleDict)
            add_rule_back(dataList, ruleDict)


def get_event_dict(inputFile, wantedTypes):

    traceName = isolate_trace(inputFile)
    traceHandle = open(traceName, 'r')

    eventDict = {}
    currentEvent = None
    currentRangePair = []

    currentLine = 0
    previousLine = 0

    enterEvent = False
    exitEvent = False

    for line in traceHandle:

        splitLine = line.split(',')
        occType = splitLine[1]
        occValue = splitLine[3]

        if('EVENT' == trim_str(occType)):
            currentEvent = occValue

            if currentEvent not in eventDict:
                eventDict[currentEvent] = []

            if('ENTRY' in occType):
                currentRangePair = []
                enterEvent = True
            elif('EXIT' in occType):
                exitEvent = True
                if(len(currentRangePair) == 1):
                    currentRangePair.append(previousLine)
                    eventDict[currentEvent].append(currentRangePair.copy())
            else:
                print("ERROR ELSE CLAUSE")

        else:
            if(('EXIT' not in occType)):
                if(trim_str(occType) in wantedTypes):
                    if(enterEvent):
                        enterEvent = False
                        currentRangePair.append(currentLine)
                    previousLine = currentLine
                    currentLine += 1
    traceHandle.close()
    return eventDict


def get_current_event(index, eventDict):

    pairMatch = False
    for key in eventDict:
        for pair in eventDict[key]:
            if((index >= pair[0]) and (index <= pair[1])):
                pairMatch = True
                return key

    return None


def add_event_back(inputList, eventDict, currentIndex=0):

    for item in inputList:

        myEvent = get_current_event(currentIndex, eventDict)
        item['info']['eventval'] = myEvent
        currentIndex += 1
        currentIndex = add_event_back(item['nest'], eventDict, currentIndex)

    return currentIndex


def get_test_json(inputFile, typeFilter):
    tempName = 'apitests/tempfiles/tempout.txt'
    goodLog = remove_unwanted_lines(inputFile, tempName, typeFilter)
    outName, outList, errCode = flaminglog.make_json(goodLog)

    return outName, outList, errCode, goodLog

def remove_all_temp_files():

    #removes all non test specific temp files
    flaminglog.cleanup()

    #list of temp files generated by tests
    unwantedFiles  = [
            'apitests/tempfiles/testout.png',
            'apitests/tempfiles/goodlines.txt',
            'apitests/tempfiles/badlines.txt',
            'apitests/tempfiles/tempFile.txt',
            'apitests/tempfiles/tempout.txt'
    ]

    #removes all test temporary files
    for filename in unwantedFiles:
        if(os.path.exists(filename)):
            os.remove(filename)


class ResultData():

    def __init__(self):
        self.count = {  'EVENT':0,
                        'RULE':0,
                        'RULEVM':0,
                        'BYTECODE':0,
                        'CMDVM':0,
                        'CMD':0,
                        'VAR_MOD':0
        }
        self.levelFails = []
        self.dataFails = []
        self.dataList = None

class ExpectedData():

    def __init__(self):
        self.count = None
        self.level = None
        self.dataList = None


class CheckStruct():
    dataFormat = ['entrytime', 'occtype', 'virtserver', 'occvalue', 'tmmpid',
            'flowid', 'remote', 'local', 'exittime', 'irule', 'eventval']

    def __init__(self, actualOut, expectedOut):

        self.actual = actualOut
        self.expected = expectedOut

    def fullCheck(self):
        """
        Runs full check of expected v actual
        """
        levelPass, dataPass, lenPass = self.recurseData(
                self.actual.dataList,
                self.expected.dataList
        )
        countPass = True
        for key in self.expected.count:
            if(self.actual.count[key] != self.expected.count[key]):
                countPass = False
        return levelPass, dataPass, countPass, lenPass



    def compareData(self, actDict, expDict):
        """
        Compared the data contained in 2 given occurrences
        """

        dataGood = True
        #check if value in each key is the same
        for key in self.dataFormat:
            #need to combine elements of local and remote into single value
            if((key == 'remote')|(key == 'local')):
                d = actDict['info'][key]
                actValue = d['ip'] + ':' + d['port'] + ':' + d['routdomain']
            
                e = expDict['info'][key]
                expValue = e['ip'] + ':' + e['port'] + ':' + e['routdomain']
                #combined values are compared
                if(actValue != expValue):
                    dataGood = False
            # all other keys are directly compared
            else:
                if(actDict['info'][key] != expDict['info'][key]):
                    dataGood = False
                    #print(key)

        return dataGood

        

    def recurseData(self, actList, expList, currentLevel=0):
        
        currentLevel += 1
        levelBool = True
        dataBool = True
        lenBool = True
        if(len(actList) != len(expList)):
            lenBool = False
            return levelBool, dataBool, lenBool
        for index, item in enumerate(actList):

            #bad level
            if(currentLevel != self.expected.level[item['info']['occtype']]):
                levelBool = False
                self.actual.levelFails.append(item['info']['occtype'])
            
            #bad data
            if(not self.compareData(item, expList[index])):
                dataBool = False
                self.actual.dataFails.append(item['info']['occtype'])
            
            childLevelBool, childDataBool, childLenBool = self.recurseData(
                item['nest'],
                expList[index]['nest'],
                currentLevel
            )
            
            #increment count for the occurrecne type
            self.actual.count[item['info']['occtype']] += 1
            
            #if any children fail pass the failure back up
            if(childLevelBool == False):
                levelBool = False
            if(childDataBool == False):
                dataBool = False
            if(childLenBool == False):
                lenBool = False

        return levelBool, dataBool, lenBool




































