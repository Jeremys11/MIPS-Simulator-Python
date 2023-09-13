#icache 
#directly mapped
#blocks and block size in config file

#dcache
#2-way set associative
#4, 4 word blocks
#LRU replacement
#Write back strategy - write allocate policy

import math

class Cache:
    def __init__(self):
        self.size = 0
        self.blocks = 0
        self.blockSize = 0
        self.sets = 0

        self.requests = 0
        self.hits = 0
        self.misses = 0

        self.hitTime = 1

        self.actualCache = []


    def config(self, blocks, blockSize):
        self.blocks = blocks
        self.blockSize = blockSize
        self.sets = blocks / blockSize

        

    def getItem(self, requested):
        if requested in self.actualCache:
            return True
        else:
            return False
 


class Icache(Cache):
    def __init__(self):
        Cache.__init__(self)

    def getAddress(self, address):
        return (address / self.blockSize) % self.blocks


class Dcache(Cache):
    def __init__(self):
        Cache.__init__(self)

    def getAddress(self, address):
        return address % self.blocks