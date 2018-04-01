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
        if self.parent.ignore_case and (key.islower() or key.isupper()):
            return  self._pairs[key.lower()] + self._pairs[key.upper()]
        else:
            return self._pairs[key]            
         
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
        if self.ignore_case and (twoletters[0].islower() or twoletters[0].isupper()):
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
            


def main():
    import argparse
    import os
    parser=argparse.ArgumentParser()
    parser.add_argument('-m','--measure',required=False,help='Measure likelihood of a given string',dest='measure')
    parser.add_argument('-n','--normal',required=False,help='Update the table based on the following normal string',dest='normal')
    parser.add_argument('-f','--normalfile',required=False,help='Update the table based on the contents of the normal file',dest='normalfile')
    parser.add_argument('-p','--print',action='store_true',required=False,help='Print a table of the most likely letters in order',dest='printtable')
    parser.add_argument('-c','--create',action='store_true',required=False,help='Create a new empty frequency table',dest='create')
    parser.add_argument('-t','--toggle_case_sensitivity',action='store_true',required=False,help='Ignore case in all future frequecy tabulations',dest='toggle_case')
    parser.add_argument('-M','--max_prob',required=False,default=40,type=int,help='Defines the maximum probability of any character combo. (Prevents "qu" from overpowering stats) Default 40',dest='max_prob')
    parser.add_argument('-w','--weight',type=int,default = 1, required=False,help='Affects weight of promote, update and update file (default is 1)',dest='weight')
    parser.add_argument('-e','--exclude',default = "\n\t~`!@#$%^&*()_+-", required=False,help='Provide a list of characters to ignore from the tabulations.',dest='exclude')
    parser.add_argument('freqtable',help='File storing character frequencies.')

    args=parser.parse_args()

    fc = FreqCounter()
    if args.create and os.path.exists(args.freqtable):
        print("Frequency table already exists. "+args.freqtable)
        sys.exit(1)

    if not args.create:
        if not os.path.exists(args.freqtable):
           print("Frequency Character file not found. - %s " % (args.freqtable))
           return
        fc.load(args.freqtable)

    if args.printtable: fc.printtable()
    if args.normal: fc.tally_str(args.normal, args.weight)
    if args.toggle_case:  fc.ignorecase = not fc.ignorecase
    if args.normalfile:
        try:
            filecontent = open(args.normalfile).read()
        except Exception as e:
            print("Unable to open file. " + str(e))
            sys.exit(1)
        fc.tally_str(filecontent)
    if args.measure: print(fc.probability(args.measure, args.max_prob))
    fc.save(args.freqtable)

if __name__ == "__main__":
    main()
