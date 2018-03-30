#!/usr/bin/env python3
from __future__ import division
import string
import re
import weakref
import json
from collections import Counter
from collections import defaultdict
from collections import Mapping

class node():
    """ Assigning a weight actually adds that value.  It doesn't set it to that value.
        For example node['c'] = 5    increases the value in node by 5   
"""

    def __init__(self,parent):
        self._pairs = Counter()
        self.parent = parent
        self._countcache = 0
        self._dirtycount = False

    def __getitem__(self,key):
        if not self.parent.ignore_case:
            return self._pairs[key]
        else:
            return  self._pairs[key.lower()] + self._pairs[key.upper()]
        
    def __setitem__(self,key,value):
        self._dirtycount = True
        self._pairs.update([key]*value)

    @property   
    def count(self):
        if self._dirtycount:
           self._cachecount = sum(self._pairs.values())
           self._dirtycount = False
        return self._cachecount

class FreqCounter(dict):
    def __init__(self, *args,**kwargs):
        self._table = defaultdict(lambda :node(self))
        self.ignore_case = False
        self.ignorechars = ""
        
    def __getitem__(self,key):
        return self._table[key]
        
    def __iter__(self):
        return iter(self._table)

    def __len__(self):
        return len(self._table)

    def toJSON(self):
        serial = []
        for key,val in self._table.items():
            serial.append( (key, list(val._pairs.items())) )
        return json.dumps((self.ignore_case, self.ignorechars, serial)) 

    def fromJSON(self,jsondata):
        args = json.loads(jsondata)
        if args:
            self.ignore_case = args[0]
            self.ignorechars = args[1]
            for outerkey,val in args[2]:
                self._table[outerkey] = node(self)
                for letter,count in val:
                   self._table[outerkey][letter] = count
        
    def tally_str(self,line,weight=1):
        """tally_str() accepts two parameters.  A string and optionally you can specify a weight."""
        allpairs = re.findall(r"..", line)
        allpairs.extend(re.findall(r"..",line[1:]))
        for eachpair in allpairs:
            self[eachpair[0]][eachpair[1]] = weight

  
    def probability(self,line,max_prob=40):
        """This function tells you how probable the letter combination provided is giving the character frequencies. Ex .probability("test") returns ~%35 """
        allpairs = re.findall(r"..", line)
        allpairs.extend(re.findall(r"..",line[1:]))
       #probability 1 is the average probability
        probs = []
        for eachpair in allpairs:
            if (eachpair[0] not in self.ignorechars) and (eachpair[1] not in self.ignorechars):
                probs.append(self._probability(eachpair, max_prob))
        probability1 = sum(probs)/ len(probs) * 100
        #probability2 is the Total word probabilty
        totl1 = 0 
        totl2 = 0
        for eachpair in allpairs:
             if (eachpair[0] not in self.ignorechars) and (eachpair[1] not in self.ignorechars):
                 totl1 += self[eachpair[0]].count
                 totl2 += self[eachpair[0]][eachpair[1]]
        probability2 = totl2/totl1 * 100
        return round(probability1,4),round(probability2,4)

    def _probability(self,twoletters, max_prob=40):
        if self[twoletters[0]].count == 0:
            return 0
        if self.ignore_case:
            ignored_tot = sum([self[twoletters[0].lower()][eachlet] for eachlet in self.ignorechars]) + sum([self[twoletters[0].upper()][eachlet] for eachlet in self.ignorechars])
            let2 = self[twoletters[0].lower()][twoletters[1]] + self[twoletters[0].upper()][twoletters[1]]
            let1 = self[twoletters[0].lower()].count + self[twoletters[0].upper()].count
            return let2/(let1-ignored_tot)
        else:
            ignored_tot = sum([self[twoletters[0]][eachlet] for eachlet in self.ignorechars])
            return self[twoletters[0]][twoletters[1]] / (self[twoletters[0]].count - ignored_tot)

    def save(self,filename):
        try:
            file_handle =  open(filename, 'wb')
            file_handle.write(self.toJSON().encode("latin1"))
            file_handle.flush()
            file_handle.close()
        except Exception as e:
            print("Unable to write freq file :"+str(e))
            raise(e)

    def load(self,filename):
        try:
            file_handle =  open(filename,"rb") 
            self.fromJSON(file_handle.read().decode("latin1"))
            file_handle.close()
        except Exception as e:
            print("Unable to load freq file :",str(e))
            raise(e)

    @property
    def count(self):
        return sum(map(lambda y:y.count, x._table.values()))
            

