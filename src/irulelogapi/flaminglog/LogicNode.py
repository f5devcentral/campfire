class BasicLogicNode:
    def __init__(self):
        self.fieldname = None
        self.value = None
    def eval_comparison(self, checkDict):
        valBool = False
        actualValue = None
        if((self.fieldname == 'remote') | (self.fieldname == 'local')):
            d = checkDict[self.fieldname]
            tempList = [d['ip'],d['port'],d['routdomain']]
            actualValue = d['ip'] + ':' + d['port'] + ':' + d['routdomain']
            valBool = (actualValue == self.value)

        elif(self.fieldname == 'flow'):
            dRemote = checkDict['remote']
            remoteVal = [dRemote['ip'],dRemote['port'],dRemote['routdomain']]
            remoteVal = ':'.join(remoteVal)

            dlocal = checkDict['local']
            localVal = [dlocal['ip'],dlocal['port'],dlocal['routdomain']]
            localVal = ':'.join(localVal)

            flowVal = remoteVal + '-' + localVal

            valBool = (flowVal == self.value)

        else:
            actualValue = checkDict[self.fieldname]
            valBool = (actualValue == self.value)

        return valBool


class LogicNode:
    def __init__(self):
        self.children = []
        self.operators = []

    def add_children(self, contentList):
        #structures basic queries into children of ComplexLogicNode
        eventExists = False
        for item in contentList:
            childNode = BasicLogicNode()
            tempList = item.split('==')
            childNode.fieldname = tempList[0]
            childNode.value = tempList[1]
            self.children.append(childNode)


    def eval_logic(self, checkDict):
        """
        Evalutes whether the passed dict matches the complex logic of the
        LogicNode
        """
        result = True
        #gets individual evaluations from children
        passList = []
        for child in self.children:
            myVal = child.eval_comparison(checkDict)
            passList.append(child.eval_comparison(checkDict))

        #if only one child returns the only boolean available
        if(len(passList) == 1):
            result = passList[0]

        #TODO: Combine following cases possibly
        #print(passList)
        #gets resutl if only 2 simple logics
        elif(len(passList) == 2 and len(self.operators) == 1):

            result = self.operators[0](passList[0], passList[1])
        else:
            #combines all children logic using the operators
            firstCheck = True
            opIndex = 0
            for i in range(0,len(passList)):
                if(firstCheck):
                    firstCheck = False
                    result = self.operators[opIndex](passList[0], passList[1])
                    i+=1
                else:
                    result = self.operators[opIndex](result,passList[i])
                    opIndex += 1
        """
        print('----------------------')
        print(result)
        """
        return result

