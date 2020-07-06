import operator
from . import LogicNode
import re

def check_filter_str(inputStr):
    """
    Returns True if filter string is ok, False if not
    """
    if(not(isinstance(inputStr, str))):
        return False

    acceptedFields = ['remote', 'local', 'flow', 'eventval', 'irule']

    inputList = inputStr.split('|')
    myList = []
    for index, item in enumerate(inputList):
        inputList[index] = item.split('&')
        myList += inputList[index]


    for item in myList:
        if(item.count('(') != 1):
            return False
        if(item.count(')') != 1):
            return False
        if(item.count('=') != 2):
            return False

        item = item.replace('(', '')
        item = item.replace(')', '')

        equivList = item.split('==')
        if(equivList[0] not in acceptedFields):
            return False

        if((equivList[0] == 'remote') or (equivList[0] == 'local')):
            if(equivList[1].count(':') != 2):
                return False

        if(equivList[0] == 'flow'):
            if(equivList[1].count('-') != 1):
                return False
            splitVal = equivList[1].split('-')
            for val in splitVal:
                if(val.count(':') != 2):
                    return False

        return True


def _filter_data(myList, queryNode):
    """
    Filters data of a list based on the given query node
    Parameters
    ----------
    myList: List[Dictionary]
        Contains all the data to be filtered.
    queryNode: LogicNode
        Contains the query statement in a form that can be evaluated against
        each item
    Return
    ----------
    Boolean:
        Indicates whether the given list has passed the query
    """
    parentCheck = False
    #checks every child
    deleteList = []

    #checks all items
    for index, item in enumerate(myList):

        #reset eventBool on each event
        checkBool = False
        #if any children of current item pass the filter

        if(_filter_data(item['nest'], queryNode)):
            checkBool = True
        else:
            #checks occurrence against all query requirements
            checkBool = queryNode.eval_logic(item['info'])
        """
        #if any children pass the parent also passes the filter
        if(checkBool):
            parentCheck = True
        #delete item from current list if it or no children matched query
        else:
            deleteList.append(index)
        """

        """
        if(checkBool):
            parentCheck = True
        else:
            deleteList.append(index)
        """

        if(checkBool):
            parentCheck = True
        else:
            deleteList.append(index)
    #deletes all non matching items starting with the highest index
    for i in reversed(deleteList):
        del myList[i]

    return parentCheck

def _parse_query(queryStr):
    """
    Parses the given string and puts it into a LogicNode
    Parameters
    ----------
    queryStr: String
        Defines the filters that will be parsed
    Return
    ----------
    LogicNode:
        A custom structure which organizes the parsed queryStr into an object
        which can evaluate it
    """
    mainNode = LogicNode.LogicNode()
    queryStr = queryStr.replace(' ','')
    
    logicList, myOPList = _break_query(queryStr)

    #converts operator strings to actual operators
    convertOp = {
                '&':operator.and_,
                '|':operator.or_,
                '^':operator.xor
    }

    for item in myOPList:
        mainNode.operators.append(convertOp[item])
    
    #adds the simple comparisons to the LogicNode
    mainNode.add_children(logicList)
    return mainNode


def _break_query(queryStr):
    """
    Splits the query string based on pairs of parenthesis. Parses out
    combinational logic operators
    Parameters
    ----------
    queryStr: String
        Defines the filters that will be parsed
    Return
    ----------
    Tuple (List[String],List[String]):
        Returns a Tuple of 2 List[String]. The first contains all the basic
        logic statments, the second contains all the combinatorial operators
    """
    logicStatements = []
    opList = []

    #TODO: Add check for balanced parenthesis


    if('(' in queryStr and ')' in queryStr):

        currentPairLevel = 0 #indicates the current nest level of parens
        pairSearchLevel = 0 #level of open paren that match is being found for
        openPairIndex = 0 #the index of the open parenthesis in queryStr
        closePairIndex = 0 #index of close parenthesis in queryStr
        outerOpenFound = False
        indexPairs = []
        for index, char in enumerate(queryStr):

            if(char=='('):
                currentPairLevel += 1
                #if first open parenthesis
                if(not outerOpenFound):
                    openPairIndex = index
                    pairSearchLevel = currentPairLevel
                    outerOpenFound = True
            elif(char==')'):
                #if the parenthesis is at the same nest level as the open
                if(currentPairLevel == pairSearchLevel):
                    closePairIndex = index
                    indexPairs.append([openPairIndex,closePairIndex])
                    outerOpenFound = False
                currentPairLevel -= 1

        #used the positions of the parenthesis to pull sliced from the query
        for index, pair in enumerate(indexPairs):
            logicStatements.append(queryStr[(pair[0]+1):pair[1]])

            #if not the last parenthesis pair then get operator after it
            if not(index == len(indexPairs)-1):
                opList.append(queryStr[pair[1]+1])
    
    return logicStatements, opList





























