import json
import os
import subprocess

def _dump_to_folded(
        myList, 
        filehandle, 
        currentName,
        separateTrace,
        nameIndex = 0):
    """
    Dumps the contents of the list to a .folded file
    """

    for item in myList:
        if(item['info']['occtype'] == 'VAR_MOD'):
            #do not add 'VAR_MOD to trace
            pass
        else:

            currentName[nameIndex] = item['info']['occtype']
            idNum = item['ID'].split('.')[-1]
            #print(idNum)
            if(separateTrace):
                currentName[nameIndex] += '.' + idNum
            currentName[nameIndex] += '-' + item['info']['occvalue']
            #print(currentName[nameIndex])
            dataLine = ""
            dataLine = ';'.join(currentName[:nameIndex + 1])
            dataLine += ' ' + str(item['info']['realexectime']) + '\n'
            filehandle.write(dataLine)
            _dump_to_folded(
                    item['nest'],
                    filehandle, 
                    currentName, 
                    separateTrace,
                    nameIndex + 1
            )

def _byte_comp_help(index, item, parentList, parentDict):
    """
    Splits up execution time computation for bytecode
    """
    rawExecTime = 0
    realExecTime = 0
    if(index == len(parentList)-1):
        #if is last child
        if(parentDict is None):
            rawExecTime = 0 #set to 0 so it doesn't interefere with other items
            realExecTime = 1 #set to 1 so it actual exists on flamegraph
        else:
            #realtime = rawTime = parent exit - self entry
            rawExecTime = (int(parentDict['info']['exittime']) -
                int(item['info']['entrytime']))
            realExecTime = rawExecTime
    else:
        #if not last child
        #realtime = rawtime = next sibling entry - self entry
        rawExecTime = (int(parentDict['nest'][index + 1]['info']['entrytime']) -
            int(item['info']['entrytime']))
        realExecTime = rawExecTime

    item['info']['rawexectime'] = rawExecTime
    item['info']['realexectime'] = realExecTime

def _compute_exectimes(myList, parentDict=None):
    """Computes times needed for the .folded file used by the flamegraph"""
    lastCheck = len(myList)-1
    childTimeSum = 0
    for index, item in enumerate(myList):

        isNotByte = False
        if(item['info']['occtype'] == 'BYTECODE'):

            if(len(item['nest']) > 0):
                #if has children
                #print("BYTE WITH CHILDREN")
                if(item['nest'][-1]['info']['occtype'] == 'VAR_MOD'):
                    #if the last child is of type VAR_MOD
                    _byte_comp_help(index, item, myList, parentDict)
                else:
                    item['info']['rawexectime'] = (
                        int(item['nest'][-1]['info']['exittime']) -
                        int(item['info']['entrytime']))
                    item['info']['realexectime'] = (
                        int(item['nest'][0]['info']['entrytime']) -
                        int(item['info']['entrytime']))
            else:
                #if no children
                _byte_comp_help(index, item, myList, parentDict)

        elif(item['info']['occtype'] == 'VAR_MOD'):
            #dont need to calculate for VAR_MOD
            pass

        else:
            isNotByte = True
            item['info']['rawexectime'] = (int(item['info']['exittime']) -
                int(item['info']['entrytime']))

        _compute_exectimes(item['nest'], item)

        if(isNotByte):
            #print('------------------')
            #print(item['info']['occtype'])
            #if type is not bytecode
            #compute sum of child exec times
            childSum = 0
            for child in item['nest']:
                if(child['info']['occtype'] != 'VAR_MOD'):
                    #print(child['info']['occtype'])
                    childSum += int(child['info']['rawexectime'])

            # realexectime = self raw exec time - sum children raw exec times
            item['info']['realexectime'] = item['info']['rawexectime'] - childSum

def _make_folded(contentVar, foldedName, separateTrace):

    if(isinstance(contentVar, list)):
        mainList = contentVar
    else:
        with open(contentVar,'r') as f:
            mainList = json.load(f)

    _compute_exectimes(mainList)

    currentName = [None, None, None, None, None, None]
    foldhandle = open(foldedName, 'w+')
    _dump_to_folded(mainList, foldhandle, currentName, separateTrace)
    foldhandle.close()


def _get_flame_path(folderWanted):

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
    finalPath = './' + finalPath + folderWanted
    return finalPath



def _create_flamegraph(inputFile, outputFile, optionsList):

    
    flameCmd = _get_flame_path('/FlameGraph/') + 'flamegraph.pl'

    inputHandle = open(inputFile, 'r')
    outputHandle = open(outputFile, 'w+')

    flameCmd = [flameCmd] + optionsList
    makeFlameProcess = subprocess.Popen(
            flameCmd,
            stdout=outputHandle,
            stdin=inputHandle
    )
    makeFlameProcess.wait()

    inputHandle.close()
    outputHandle.close()


    return makeFlameProcess.returncode


def _create_diff_flamegraph(
        inputFile1,
        inputFile2,
        outputFile,
        diffOptions,
        flameOptions,
        makeOnlyDiff = False):


    if(makeOnlyDiff):
        flamePath = _get_flame_path('/flamegraphdiff/')
    else:
        flamePath = _get_flame_path('/FlameGraph/')

    flameCmd = flamePath + 'flamegraph.pl'
    diffCmd = flamePath + 'difffolded.pl'
    halfFoldHandle = open('static/halfFold.folded', 'w+')

    diffCmd = [diffCmd] + diffOptions + [inputFile1, inputFile2]

    makeDiffProcess = subprocess.Popen(
            diffCmd,
            stdout=halfFoldHandle
    )
    makeDiffProcess.wait()
    halfFoldHandle.close()
    

    halfFoldHandle = open('static/halfFold.folded', 'r')
    outputHandle = open(outputFile, 'w+')
    flameCmd = [flameCmd] + flameOptions
    makeFlameProcess = subprocess.Popen(
            flameCmd,
            stdout=outputHandle,
            stdin=halfFoldHandle
    )
    makeFlameProcess.wait()
    halfFoldHandle.close()
    outputHandle.close()


    return makeFlameProcess.returncode


def _connect_svgs(diff1, diff2, diffonly):

    toolPath = _get_flame_path('/flamegraphdiff/graphs/')

    connectCmd = toolPath + 'generate_dfg_report.sh'
    connectCmdList = [connectCmd, diff1, diff2, diffonly, '.']

    connectProcess = subprocess.Popen(
            connectCmdList,
    )
    connectProcess.wait()
    
    return connectProcess.returncode


def _print_times(rootList):
    """Prints out all occurrences with their times"""

    for item in rootList:

        if(item['info']['occtype'] == 'VAR_MOD'):
            print("VAR_MOD")
        else:
            print(item['info']['occtype'] + ", " +
                    str(item['info']['rawexectime']) + ', ' +
                    str(item['info']['realexectime']))
        _print_times(item['nest'])
