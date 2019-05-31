#!/usr/bin/env python3
from freq import *
import argparse
import signal
import sys

parser = argparse.ArgumentParser()
parser.add_argument('infile', nargs='?', type=argparse.FileType('r'), default=sys.stdin)
parser.add_argument("-v", "--verbose", action="store_true", help = "Show score and freq count")
args = parser.parse_args()

def score(line):
    return len(line) * sum(freq.probability(line))/2

def signal_handler(sig, frame):
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGPIPE,signal.SIG_DFL) 

freq = FreqCounter()
freq.ignorechars = ""
freq.ignore_case = False
freq.load("freqtable2018.freq")
filecontent = args.infile.readlines()
for eachline in sorted(filecontent, key = score, reverse=True):
    if args.verbose:
       print(score(eachline), freq.probability(eachline), end="")
    print(eachline,end="")
