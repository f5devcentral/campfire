class NestNode:

    def __init__(self):
        self.parent = None  #will be single dict, None at top level
        self.children = []  #list of dicts
        self.ID = None
        self.info = None
        self.level = 0  #top level is 0, EVENT would be lvl 1
