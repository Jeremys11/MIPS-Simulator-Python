

#write stage - no hazards

#5 types of operation based on instruction

MAIN_CYCLE_TIME = 3
MAIN_BLOCKS = 4


class Instruction:
    def __init__(self):
        self.fullInst = ""
        self.Inst = ""
        self.destination = ""
        self.source1 = ""
        self.source2 = ""
        self.source2Alt = ""
        self.source1FU = ""
        self.source2FU = ""
        self.source1Ready = False
        self.source2Ready = False


        self.position = 0
        self.fetch = 0
        self.issue = 0
        self.read = 0
        self.execute = 0
        self.write = 0
        self.raw = "N"
        self.rawNow = "Y" #used to move to next stage
        self.waw = "N"
        self.wawNow = "N" #used to move to next stage
        self.struct = "N"
        self.structNow = "N" #used to move to next stage


        #Tell if instruction is one using register
        self.using_register = False

        #Remove from issue stage into read stage
        self.removeFromIssue = False

        #Remove from read stage into execute stage
        self.removeFromRead = False

        #Remove from execute into write stage
        self.removeFromExecute = False
        self.inExecute = False

        #Remove from write to no longer in pipeline
        self.removeFromPipeline = False

        #Icache runtime
        self.evaluatedICache = False
        self.fetchRuntime = 1

        #Dcache runtime
        self.evaluatedDCache = False
        self.executeRuntime = 0


        #Keeping one step per cycle
        self.ignoreRead = False
        self.ignoreExecute = False
        self.ignoreWrite = False

    def config(self,fullInst,instName,destination="",source1="",source2=""):
        self.fullInst = fullInst
        self.Inst = instName
        self.destination = destination
        self.source1 = source1
        self.source2 = source2


    def setPos(self, pos):
        self.position = pos