from modules.cache import Icache, Dcache
from modules.helper import Instruction, MAIN_CYCLE_TIME, MAIN_BLOCKS
import copy

class Pipeline:

    def __init__(self):


        #Cache
        self.m_Icache = Icache()
        self.m_Dcache = Dcache()
        self.m_Dcache.config(4,4)

        self.numInsts = -1

        #2 tuple - location of destination of branch instructions - source line
        self.BranchHere = {}
        self.numBranches = 1
        self.justJumped = False

        #Regular Register - want 2 tuples - name - source line
        self.Branches = {}
        self.Integer = {}
        self.Transfer = {}

        #registers for holding integers in scoreboard
        self.integerRegOccupied = False

        #For LW and L.D
        self.loadRegOccupied = False

        #FP Registers and information
        self.numFPAddr = 0
        self.FPAddr = []
        self.FPAddrTime = 0

        self.numFPDiv = 0
        self.FPDiv = []
        self.FPDivTime = 0

        self.numFPMul = 0
        self.FPMul = []
        self.FPMulTime = 0

        self.FPAddrRefill = 0
        self.FPDivRefill = 0
        self.FPMulRefill = 0

        #Counter
        self.cycle = 0

        #When false, pipeline stops
        self.running = True

        #Insttruction in these stages go here
        self.Fetch = []
        self.Issue = []
        self.Read = []
        self.Execute = []
        self.Write = []

 
        #All instructions from file
        self.allInstructions = []

        #Next instruction to go into pipeline/current instruction
        self.consideredLine = []
        self.consideredLineNum = 0

        #Keep track after branching
        self.numAllInsts = 0

        #Collection of Instruction objects as they enter pipeline
        self.programProgress = []


    #Finish readInst
    def readInst(self, lines):
        parsedInst = None
        lineNumber = -1
        tempInst = Instruction()

        for line in lines:
            self.numInsts = self.numInsts + 1 #number of instructions 
            lineNumber += 1
            line = line.strip()

            if len(line) == 0:
                continue
            symbol = ''


            #Branch destination
            parsedInst = line.upper().split(":")
            if len(parsedInst) == 2:
                symbol = parsedInst[0].strip()
                self.BranchHere[symbol] = lineNumber
                parsedInst = [parsedInst[1].strip()]
            parsedInst = parsedInst[0].replace('\n', '')
    

            #Getting instructions for pipeline
            parsedLine = parsedInst.split(' ')

            #Getting rid of commas
            for item in range(len(parsedLine)):
                parsedLine[item] = str(parsedLine[item]).replace(',','')

            #Removing spaces
            for j in range(len(parsedLine)-1, -1, -1):
                if(parsedLine[j] == str('')):
                    parsedLine.remove(parsedLine[j])

            #Assigning registers from parsedLine
            if len(parsedLine) == 1:
                tempInst.config(line,parsedLine[0])
            if(len(parsedLine) == 2):
                tempInst.config(line,parsedLine[0],parsedLine[1])
            if len(parsedLine) == 3:
                tempInst.config(line,parsedLine[0],parsedLine[1],parsedLine[2])
                if "(" in parsedLine[2]:
                    temp = parsedLine
                    temp2 = temp[2].split("(")
                    temp3 = temp2[1].split(")")
                    tempInst.source2Alt = temp3[0]
            if len(parsedLine) == 4:
                tempInst.config(line,parsedLine[0],parsedLine[1],parsedLine[2],parsedLine[3])

            self.allInstructions.append(copy.deepcopy(tempInst))


    #this is here for formality
    def readData(self, lines):
        return

        
    def readConfig(self, lines):
        for line in lines:
            unit = line.replace('\n', '').split(':')
            conf = unit[1][1:].split(",")
            unit = unit[0]

            # Setup Cache and FP registers
            if unit == "I-Cache":
                self.m_Icache.config(int(conf[0]), int(conf[1]))
            elif unit == "FP Multiplier":
                self.numFPMul = int(conf[0])
                self.FPMulRefill = int(conf[0])
                self.FPMulTime = int(conf[1])
            elif unit == "FP divider":
                self.numFPDiv = int(conf[0])
                self.FPDivRefill = int(conf[0])
                self.FPDivTime = int(conf[1])
            elif unit == "FP adder":
                self.numFPAddr = int(conf[0])
                self.FPAddrRefill = int(conf[0])
                self.FPAddrTime = int(conf[1])
            else:
                return

    #Read files from command line
    def readFiles(self, fileNames):

        #Read Inst
        linesInst = []
        with open(fileNames[1], 'r') as file:
            for line in file:
                linesInst.append(line)

        #Read Data
        linesData = []
        with open(fileNames[2], 'r') as file1:
            for line in file1:
                linesData.append(line)

        #Read Config
        linesConfig = []
        with open(fileNames[3], 'r') as file2:
            for line in file2:
                linesConfig.append(line)


        #Parsing
        self.readInst(linesInst)
        self.readData(linesData)
        self.readConfig(linesConfig)

    #Open file for writing
    def readyOutput(self, fileName):
        self.result = fileName
        return

    def FetchStage(self):

        #ICache lookup not done
        if (self.Fetch[0]).evaluatedICache == False:

            result = self.m_Icache.getItem(self.Fetch[0].fullInst)
            self.m_Icache.requests = self.m_Icache.requests + 1
            self.Fetch[0].evaluatedICache = True

            #lookup success - cache hit
            if(result == True):
                self.Fetch[0].fetchRuntime = 0
                self.m_Icache.hits = self.m_Icache.hits + 1

            #lookup fail - cache miss
            else:
                if(self.cycle == 0):
                    self.Fetch[0].fetchRuntime = 1 + (MAIN_BLOCKS*MAIN_CYCLE_TIME)
                else:
                    self.Fetch[0].fetchRuntime = (MAIN_BLOCKS*MAIN_CYCLE_TIME)
                self.m_Icache.misses = self.m_Icache.misses + 1


                if(len(self.m_Icache.actualCache) < 16):
                    #Adding instructions to cache
                    if(self.numInsts - self.consideredLineNum >= 3):
                        self.m_Icache.actualCache.append(copy.deepcopy((self.allInstructions[self.consideredLineNum]).fullInst))
                        self.m_Icache.actualCache.append(copy.deepcopy((self.allInstructions[self.consideredLineNum+1]).fullInst))
                        self.m_Icache.actualCache.append(copy.deepcopy((self.allInstructions[self.consideredLineNum+2]).fullInst))
                        self.m_Icache.actualCache.append(copy.deepcopy((self.allInstructions[self.consideredLineNum+3]).fullInst))
                    if(self.numInsts - self.consideredLineNum == 2):
                        self.m_Icache.actualCache.append(copy.deepcopy((self.allInstructions[self.consideredLineNum]).fullInst))
                        self.m_Icache.actualCache.append(copy.deepcopy((self.allInstructions[self.consideredLineNum+1]).fullInst))
                        self.m_Icache.actualCache.append(copy.deepcopy((self.allInstructions[self.consideredLineNum+2]).fullInst))
                    if(self.numInsts - self.consideredLineNum == 1):
                        self.m_Icache.actualCache.append(copy.deepcopy((self.allInstructions[self.consideredLineNum]).fullInst))
                        self.m_Icache.actualCache.append(copy.deepcopy((self.allInstructions[self.consideredLineNum+1]).fullInst))
                    if(self.numInsts - self.consideredLineNum == 0):
                        self.m_Icache.actualCache.append(copy.deepcopy((self.allInstructions[self.consideredLineNum]).fullInst))

                else:
                    #Remove from cache
                    for i in range(self.m_Icache.blockSize):
                        self.m_Icache.actualCache.pop(0)

                    if(self.numInsts - self.consideredLineNum >= 3):
                        self.m_Icache.actualCache.append(copy.deepcopy((self.allInstructions[self.consideredLineNum]).fullInst))
                        self.m_Icache.actualCache.append(copy.deepcopy((self.allInstructions[self.consideredLineNum+1]).fullInst))
                        self.m_Icache.actualCache.append(copy.deepcopy((self.allInstructions[self.consideredLineNum+2]).fullInst))
                        self.m_Icache.actualCache.append(copy.deepcopy((self.allInstructions[self.consideredLineNum+3]).fullInst))
                    if(self.numInsts - self.consideredLineNum == 2):
                        self.m_Icache.actualCache.append(copy.deepcopy((self.allInstructions[self.consideredLineNum]).fullInst))
                        self.m_Icache.actualCache.append(copy.deepcopy((self.allInstructions[self.consideredLineNum+1]).fullInst))
                        self.m_Icache.actualCache.append(copy.deepcopy((self.allInstructions[self.consideredLineNum+2]).fullInst))
                    if(self.numInsts - self.consideredLineNum == 1):
                        self.m_Icache.actualCache.append(copy.deepcopy((self.allInstructions[self.consideredLineNum]).fullInst))
                        self.m_Icache.actualCache.append(copy.deepcopy((self.allInstructions[self.consideredLineNum+1]).fullInst))
                    if(self.numInsts - self.consideredLineNum == 0):
                        self.m_Icache.actualCache.append(copy.deepcopy((self.allInstructions[self.consideredLineNum]).fullInst))

        #ICache lookup done
        if(self.Fetch[0].fetchRuntime <= 0 and (len(self.Issue) == 0)):
            #Get next instruction to Fetch
            self.Fetch[0].fetch = self.cycle
            self.Issue.append(copy.deepcopy(self.Fetch[0]))
            self.Fetch.clear()
            self.consideredLineNum = self.consideredLineNum + 1
            self.numAllInsts = self.numAllInsts + 1
        else:
            self.Fetch[0].fetchRuntime = self.Fetch[0].fetchRuntime - 1
            

    #Stalls from WAW - stalls from structural hazards
    #J and HLT resolved here
    def IssueStage(self):

        if(self.Issue[0].fetch != self.cycle):
            #J and HLT
            if self.Issue[0].Inst == ("J"):
                self.Issue[0].issue = self.cycle
                self.consideredLineNum = self.BranchHere[self.Issue[0].destination]
                self.justJumped = True
                return
            if self.Issue[0].Inst == ("HLT"):
                temp = False
                for j in range(len(self.Read)):
                    if self.Read[j].Inst in ["BNE","BEQ"]:
                        temp = True
                if(temp == False):
                    self.Issue[0].issue = self.cycle
                    self.running = False
                return

            #just move jump to read
            if(self.Issue[0].Inst in ["BNE","BEQ"]):
                self.Issue[0].issue = self.cycle
                self.Read.append(copy.deepcopy(self.Issue[0]))
                self.Issue.clear()
                return

            #just move store to read
            if(self.Issue[0].Inst in ["SW","S.D"]):
                self.Issue[0].issue = self.cycle
                self.Read.append(copy.deepcopy(self.Issue[0]))
                self.Issue.clear()
                return

            #Checking for "WAW"
            self.Issue[0].wawNow = "N"
            for j in range(len(self.consideredLine)):
                if (self.consideredLine[j].position < self.Issue[0].position):
                    if(self.Issue[0].destination == (self.consideredLine[j].destination)):
                        self.Issue[0].waw = "Y"
                        self.Issue[0].wawNow = "Y"


            #Assigning Functional Units
            if(self.Issue[0].using_register == False):

                #Load Register occupy
                if((self.Issue[0].Inst in ["LW","L.D"]) and 
                (self.loadRegOccupied == False)):
                    self.loadRegOccupied = True
                    self.Issue[0].using_register = True
                    self.Issue[0].structNow = "N"

                elif((self.Issue[0].Inst in ["L.D","LW"]) and 
                (self.loadRegOccupied == True)):
                    self.Issue[0].struct = "Y"
                    self.Issue[0].structNow = "Y"

                #Integer Register occupy
                if((self.Issue[0].Inst in ["LI","LUI","DADD","DADDI","DSUB","DSUBI","AND","ANDI","OR","ORI"]) and
                (self.integerRegOccupied == False)):
                    self.integerRegOccupied = True
                    self.Issue[0].using_register = True
                    self.Issue[0].structNow = "N"

                elif((self.Issue[0].Inst in ["LI","LUI","DADD","DADDI","DSUB","DSUBI","AND","ANDI","OR","ORI"]) and 
                (self.integerRegOccupied == True)):
                    self.Issue[0].struct = "Y"
                    self.Issue[0].structNow = "Y"

                #FP Adder register occupy
                elif ((self.Issue[0].Inst in ["ADD.D","SUB.D"]) and (self.numFPAddr > 0)):
                    self.numFPAddr = self.numFPAddr - 1
                    self.Issue[0].using_register = True
                    self.Issue[0].structNow = "N"

                elif ((self.Issue[0].Inst in ["ADD.D","SUB.D"]) and (self.numFPAddr <= 0)):
                    self.Issue[0].struct = "Y"
                    self.Issue[0].structNow = "Y"

                #FP Mul register occupy
                elif ((self.Issue[0].Inst == ("MUL.D")) and (self.numFPMul > 0)):
                    self.numFPMul = self.numFPMul - 1
                    self.Issue[0].using_register = True
                    self.Issue[0].structNow = "N"

                elif ((self.Issue[0].Inst == ("MUL.D")) and (self.numFPMul <= 0)):
                    self.Issue[0].struct = "Y"
                    self.Issue[0].structNow = "Y"

                #FP Div register occupy
                elif ((self.Issue[0].Inst == ("DIV.D")) and (self.numFPDiv > 0)):
                    self.numFPDiv = self.numFPDiv - 1
                    self.Issue[0].using_register = True
                    self.Issue[0].structNow = "N"

                elif ((self.Issue[0].Inst == ("DIV.D")) and (self.numFPDiv <= 0)):
                    self.Issue[0].struct = "Y"
                    self.Issue[0].structNow = "Y"

                else:
                    return

            #Move into Read stage
            if((self.Issue[0].using_register == True) and (self.Issue[0].wawNow == "N") and (self.Issue[0].structNow == "N")):
                self.Issue[0].issue = self.cycle
                self.Read.append(copy.deepcopy(self.Issue[0]))
                self.Issue.clear()


    
    #Stalls from RAW
    def ReadStage(self):

        #Keeping up with cycles
        for i in range(len(self.Read)):
            self.Read[i].ignoreRead = False

        for i in range(len(self.Read)):
            if(self.Read[i].issue == self.cycle):
                self.Read[i].ignoreRead = True


        for i in range((len(self.Read))):

            if(self.Read[i].ignoreRead == False):
                self.Read[i].rawNow = "N"

                #Checking for RAW
                for j in range(len(self.consideredLine)):

                    #Branch instruction resolution
                    if((self.consideredLine[j].position < self.Read[i].position) and (self.Read[i].Inst in ["BEQ","BNE"])):
                        if(self.Read[i].source1 == (self.consideredLine[j].destination)):
                            self.Read[i].raw = "Y"
                            self.Read[i].rawNow = "Y"
                        if(self.Read[i].destination == (self.consideredLine[j].destination)):
                            self.Read[i].raw = "Y"
                            self.Read[i].rawNow = "Y"


                    #RAW with immediates
                    if ((self.consideredLine[j].position < self.Read[i].position) and 
                    (self.Read[i].Inst in ["DADDI","DSUBI","ANDI","ORI","LI","LUI","BEQ","BNE"])):
                        if(self.Read[i].source1 == (self.consideredLine[j].destination)):
                            self.Read[i].raw = "Y"
                            self.Read[i].rawNow = "Y"
                        if(self.Read[i].destination == (self.consideredLine[j].destination)):
                            self.Read[i].raw = "Y"
                            self.Read[i].rawNow = "Y"


                    #RAW with other loads and stores
                    if ((self.consideredLine[j].position < self.Read[i].position) and 
                    (self.Read[i].Inst in ["LW","L.D","SW","S.D"])):
                        if(self.Read[i].source1 == (self.consideredLine[j].destination)):
                            self.Read[i].raw = "Y"
                            self.Read[i].rawNow = "Y"
                        if(self.Read[i].source2Alt == (self.consideredLine[j].destination)):
                            self.Read[i].raw = "Y"
                            self.Read[i].rawNow = "Y"
                        if(self.Read[i].destination == (self.consideredLine[j].destination)):
                            self.Read[i].raw = "Y"
                            self.Read[i].rawNow = "Y"

                    #RAW
                    if ((self.consideredLine[j].position < self.Read[i].position) and
                    (self.Read[i].Inst in ["DADD","DSUB","AND","OR","ADD.D","MUL.D","DIV.D","SUB.D"])):
                        if(self.Read[i].source1 == (self.consideredLine[j].destination)):
                            self.Read[i].raw = "Y"
                            self.Read[i].rawNow = "Y"
                        if(self.Read[i].source2 == (self.consideredLine[j].destination)):
                            self.Read[i].raw = "Y"
                            self.Read[i].rawNow = "Y"
                        if(self.Read[i].destination == (self.consideredLine[j].destination)):
                            self.Read[i].raw = "Y"
                            self.Read[i].rawNow = "Y"

                if((self.Read[i].rawNow == "N") and (self.Read[i].Inst in ["BEQ","BNE"])):
                    if(self.numBranches > 0):
                        self.Read[i].read = self.cycle
                        self.consideredLineNum = self.BranchHere[self.Read[i].source2]
                        self.numBranches = self.numBranches - 1
                        self.justJumped = True
                        return
                    else:
                        self.Read[i].read = self.cycle
                        self.programProgress.append(copy.deepcopy(self.Read[i]))
                        self.Read.remove(self.Read[i])
                        self.justJumped = False


        #Remove from read stage and move to write stage
        for i in range(len(self.Read) - 1 , -1, -1):
            if(self.Read[i].ignoreRead == False):
                if self.Read[i].rawNow == "N":
                    self.Read[i].read = self.cycle
                    self.Execute.append(copy.deepcopy(self.Read[i]))
                    self.Read.remove(self.Read[i])

    #Dcahce checks here 
    #Stalls from dcache misses
    def ExecuteStage(self):

        for i in range(len(self.Execute)):

            if(self.Execute[i].inExecute == False):

                #Dcache lookup not done
                if((self.Execute[i].evaluatedDCache == False) and (self.Execute[i].Inst in ["LW","SW"] )):

                    if(self.Execute[i].inst == "SW"):
                        self.Execute[i].executeRuntime = 1
                        self.m_Dcache.hits = self.m_Dcache.hits + 1
                        self.m_Dcache.requests = self.m_Dcache.requests + 1
                        self.Execute[i].evaluatedDCache = True
                        self.Execute[i].inExecute = True

                    else:
                        result = self.m_Dcache.getItem(self.Execute[i].fullInst)
                        self.m_Dcache.requests = self.m_Dcache.requests + 1
                        self.Execute[i].evaluatedDCache = True
                        self.Execute[i].inExecute = True

                        #Dcache hit
                        if(result == True):
                            self.Execute[i].executeRuntime = 1
                            self.m_Dcache.hits = self.m_Dcache.hits + 1
                            self.Execute[i].inExecute = True

                        #Dcache miss
                        else:
                            self.Execute[i].executeRuntime = 1 + 1*(MAIN_BLOCKS*MAIN_CYCLE_TIME)
                            self.m_Dcache.misses = self.m_Dcache.misses + 1
                            self.m_Dcache.actualCache.append(copy.deepcopy(self.Execute[i].fullInst))

                #Dcache lookup not done
                elif((self.Execute[i].evaluatedDCache == False) and (self.Execute[i].Inst in ["L.D","S.D"] )):


                    if(self.Execute[i].Inst == "S.D"):
                        self.Execute[i].executeRuntime = 2
                        self.m_Dcache.hits = self.m_Dcache.hits + 2
                        self.Execute[i].inExecute = True
                        self.m_Dcache.requests = self.m_Dcache.requests + 2
                        self.Execute[i].evaluatedDCache = True

                    else:
                        result = self.m_Dcache.getItem(self.Execute[i].fullInst)
                        self.m_Dcache.requests = self.m_Dcache.requests + 2
                        self.Execute[i].evaluatedDCache = True
                        self.Execute[i].inExecute = True

                        #Dcache hit
                        if(result == True):
                            self.Execute[i].executeRuntime = 2
                            self.m_Dcache.hits = self.m_Dcache.hits + 2
                            self.Execute[i].inExecute = True

                        #Dcache miss
                        else:
                            self.Execute[i].executeRuntime = 2 + 2*(MAIN_BLOCKS*MAIN_CYCLE_TIME)
                            self.Execute[i].inExecute = True
                            self.m_Dcache.misses = self.m_Dcache.misses + 2
                            self.m_Dcache.actualCache.append(copy.deepcopy(self.Execute[i].fullInst))

                elif(self.Execute[i].Inst in ["LI","LUI","DADD","DADDI","DSUB","DSUBI","AND","ANDI","OR","ORI"]):
                    self.Execute[i].executeRuntime = 1
                    self.Execute[i].inExecute = True

                elif(self.Execute[i].Inst in ["ADD.D","SUB.D"]):
                    self.Execute[i].executeRuntime = self.FPAddrTime
                    self.Execute[i].inExecute = True

                elif(self.Execute[i].Inst == ("MUL.D")):
                    self.Execute[i].executeRuntime = self.FPMulTime
                    self.Execute[i].inExecute = True

                elif(self.Execute[i].Inst == ("DIV.D")):
                    self.Execute[i].executeRuntime = self.FPDivTime
                    self.Execute[i].inExecute = True

                else:
                    pass

            #Execution progressing
            if(self.Execute[i].executeRuntime > 0):
                self.Execute[i].executeRuntime = self.Execute[i].executeRuntime - 1

            #Execution done
            else:
                self.Execute[i].execute = self.cycle
                self.Execute[i].removeFromExecute = True
        
        #Remove from Execute - move to write
        for i in range(len(self.Execute) -1, -1, -1):
            if(self.Execute[i].removeFromExecute == True):
                self.Write.append(copy.deepcopy(self.Execute[i]))
                self.Execute.remove(self.Execute[i])

    
    def WriteStage(self):


        #Keeping up with cycles
        for i in range(len(self.Write)):
            self.Write[i].ignoreWrite = False

        for i in range(len(self.Write)):
            if(self.Write[i].execute == self.cycle):
                self.Write[i].ignoreWrite = True

        for i in range(len(self.Write)):

            if(self.Write[i].ignoreWrite == False):


                if(self.Write[i].Inst in ["LW","L.D"]):
                    self.loadRegOccupied = False
                elif(self.Write[i].Inst in ["LI","LUI","DADD","DADDI","DSUB","DSUBI","AND","ANDI","OR","ORI"]):
                    self.integerRegOccupied = False

                elif(self.Write[i].Inst in ["ADD.D","SUB.D"]):
                    self.numFPAddr = self.numFPAddr + 1

                elif(self.Write[i].Inst == ("MUL.D")):
                    self.numFPMul = self.numFPMul + 1

                elif(self.Write[i].Inst == ("DIV.D")):
                    self.numFPDiv = self.numFPDiv + 1

                else:
                    pass

        tempList = []

        for i in range(len(self.Write) -1, -1, -1):
            if(self.Write[i].ignoreWrite == False):
                tempList.append(self.Write[i].position)
                self.Write[i].write = self.cycle
                self.programProgress.append(copy.deepcopy(self.Write[i]))
                self.Write.remove(self.Write[i])

        for j in range(len(self.consideredLine) -1, -1, -1):
            if ((self.consideredLine[j].position) in (tempList)):
                self.consideredLine.remove(self.consideredLine[j])

        tempList.clear()


    #Main body of program
    def simulate(self):

        while(self.running == True):        

            #HLT resolved here
            #J Resolved here
            if len(self.Issue) != 0:
                self.IssueStage()

            #Icacche lookup here
            if len(self.Fetch) == 0:
                self.Fetch.append(copy.deepcopy(self.allInstructions[self.consideredLineNum]))
                self.Fetch[0].setPos(self.numAllInsts)

                self.consideredLine.append(copy.deepcopy(self.allInstructions[self.consideredLineNum]))
                self.consideredLine[-1].setPos(self.numAllInsts)
                self.FetchStage()
            else:
                self.FetchStage()

            if((self.running == True) and (self.justJumped == False)):

                #Conditional Branches resolved here
                if len(self.Read) != 0:
                    self.ReadStage()

                if(self.justJumped == False):
                    #DCache lookup here
                    if len(self.Execute) != 0:
                        self.ExecuteStage()


                    if len(self.Write) != 0:
                        self.WriteStage()

                #Branching
                else:
                    self.numFPAddr = self.FPAddrRefill
                    self.numFPDiv = self.FPDivRefill
                    self.numFPMul = self.FPMulRefill
                    self.loadRegOccupied = False
                    self.integerRegOccupied = False

                    for i in range(len(self.Write) -1, -1, -1):
                        self.programProgress.append(copy.deepcopy(self.Write[i]))
                        self.Write.remove(self.Write[i])

                    for i in range(len(self.Read) -1, -1, -1):
                        self.programProgress.append(copy.deepcopy(self.Read[i]))
                        self.Read.remove(self.Read[i])

                    for i in range(len(self.Execute) -1, -1, -1):
                        self.programProgress.append(copy.deepcopy(self.Execute[i]))
                        self.Execute.remove(self.Execute[i])

                    for i in range(len(self.Issue) -1, -1, -1):
                        self.numAllInsts -= 1
                        self.m_Icache.requests -= 1
                        self.m_Icache.hits -= 1
                        self.programProgress.append(copy.deepcopy(self.Issue[i]))
                        self.Issue.remove(self.Issue[i])

                    for i in range(len(self.Fetch) -1, -1, -1):
                        if(self.Fetch[i].fetchRuntime > 0):
                            self.Fetch[i].fetch = self.cycle + self.Fetch[i].fetchRuntime
                            self.cycle = self.cycle + self.Fetch[i].fetchRuntime
                        else:
                            self.Fetch[i].fetch = self.cycle
                            #self.cycle = self.cycle + 1
                        self.programProgress.append(copy.deepcopy(self.Fetch[i]))
                        self.Fetch.remove(self.Fetch[i])

                    self.consideredLine.clear()
                    self.numAllInsts += 1
                    self.justJumped = False


            #Unconditional Jump or HLT
            else:
                self.numFPAddr = self.FPAddrRefill
                self.numFPDiv = self.FPDivRefill
                self.numFPMul = self.FPMulRefill
                self.loadRegOccupied = False
                self.integerRegOccupied = False

                for i in range(len(self.Write) -1, -1, -1):
                    self.programProgress.append(copy.deepcopy(self.Write[i]))
                    self.Write.remove(self.Write[i])

                for i in range(len(self.Read) -1, -1, -1):
                    self.programProgress.append(copy.deepcopy(self.Read[i]))
                    self.Read.remove(self.Read[i])

                for i in range(len(self.Execute) -1, -1, -1):
                    self.programProgress.append(copy.deepcopy(self.Execute[i]))
                    self.Execute.remove(self.Execute[i])

                for i in range(len(self.Issue) -1, -1, -1):
                    self.programProgress.append(copy.deepcopy(self.Issue[i]))
                    self.Issue.remove(self.Issue[i])

                for i in range(len(self.Fetch) -1, -1, -1):
                    if(self.Fetch[i].fetchRuntime > 0):
                        self.Fetch[i].fetch = self.cycle + self.Fetch[i].fetchRuntime
                        self.cycle = self.cycle + self.Fetch[i].fetchRuntime
                    else:
                        self.Fetch[i].fetch = self.cycle
                        #self.cycle = self.cycle + 1
                    self.programProgress.append(copy.deepcopy(self.Fetch[i]))
                    self.Fetch.remove(self.Fetch[i])

                self.consideredLine.clear()
                self.numAllInsts += 1
                self.justJumped = False


            self.justJumped = False
            self.cycle = self.cycle + 1

        #Sorting and cleaning up
        self.programProgress.sort(key=lambda x:(x.position))
        for i in range(len(self.programProgress)-1, -1, -1):
            if(i != 0):
                if (self.programProgress[i-1].position == self.programProgress[i].position):
                    if(self.programProgress[i] == "HLT"):
                        self.programProgress.remove(self.programProgress[i])
                    else:
                        self.programProgress.remove(self.programProgress[i-1])

        #Writing to file
        with open(self.result, 'w') as result:
            for i in range(len(self.programProgress)):
                        line = (str(self.programProgress[i].position) + ' ' + self.programProgress[i].fullInst + ' ' + str(self.programProgress[i].fetch) + ' ' + str(self.programProgress[i].issue) + ' ' + 
                        str(self.programProgress[i].read) + ' ' +  str(self.programProgress[i].execute) + ' ' +  str(self.programProgress[i].write) + ' ' +
                        str(self.programProgress[i].raw) + ' ' + str(self.programProgress[i].waw) + ' ' + str(self.programProgress[i].struct)
                        )
                        result.write(line + '\n')


            line = ("Dcache Requests:" + ' ' + str(self.m_Dcache.requests) + '\n' + "Dcahce hits:" + ' ' + str(self.m_Dcache.hits))
            result.write(line + '\n')
            line = ("Icache Requests:" + ' ' + str(self.m_Icache.requests) + '\n' + "Icahce hits:" + ' ' + str(self.m_Icache.hits))
            result.write(line + '\n')
