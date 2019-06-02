#!/usr/bin/env python3
from freq import *
import argparse
import signal
import sys

parser = argparse.ArgumentParser()
parser.add_argument('infile', nargs='?', type=argparse.FileType('r'), default=sys.stdin)
parser.add_argument('-f','--freq_table',default = "freqtable2018.freq", required=False,help='Specify the frequency table to use. Default is freqtable2018.freq',dest='freqtable')

parser.add_argument("-v", "--verbose", action="count", help = "Show details of how sort order is determined.")
parser.add_argument('-s','--case_sensitive',action='store_true',required=False,help='Consider case in calculations. Default ignores case.',dest='case_sensitive')
parser.add_argument('-e','--exclude',default = "\n\t~`!@#$%^&*()_+-;", required=False,help='Specify a full list of characters to ignore from the tabulations.',dest='exclude')
parser.add_argument('-a','--add_exclude',default = "", required=False,help='Provide a list of characters to add to default ignored characters.',dest='additional')
parser.add_argument('-n','--numeric',action='store_true',required=False,help='Convert input to number for sorting.',dest='numeric')
parser.add_argument('-c','--cut',nargs=2,help='Specify a delimer and field value to cut a substring for the target of your search. Example -c "/" 3 will use the value between the 3rd and 4th "/" for sorting.',dest='cut')
parser.add_argument('-S','--substring',nargs=2,help='Slice out a substring given the starting and stoping position. If cut is used this is performed after cut. Example -S 10,13 would only use the string comprised of characters 10,11 and 12 to determine the sort order.',dest='slice')
parser.add_argument('-r','--reverse',action='store_true',required=False,help='Reverses the sort order with highest frequency values last',dest='reverse')
parser.add_argument('-N','--no_length',action='store_true',required=False,help='Do not consider length of string when determining sort order',dest='length')
parser.add_argument('-l','--line',action='store_true',required=False,help='Include the line number where the string was located in the output.',dest='line')

args = parser.parse_args()

def score(line):
    if args.cut:
        try:
            line = line.split(args.cut[0])[int(args.cut[1])]
        except IndexError:
            line = ""
        except:
            raise(Exception("Unable to process -c cut options."))
        if args.verbose: print("Now sorting on {}".format(line))
    if args.slice:
        try:
            line = line[int(args.slice[0]):int(args.slice[1])]
        except:
            raise(Exception("Unable to process -S substring options."))
        if args.verbose: print("Now sorting on {}".format(line))
    if args.numeric:
        try:
            return float(line)
        except:
            raise(Exception("The value {} can not be treated as numeric. Try without -n.".format(line)))
    line_len = len(line) if not args.length else 1
    return line_len * sum(freq.probability(line))/2

def signal_handler(sig, frame):
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGPIPE,signal.SIG_DFL) 

freq = FreqCounter()

freq.load(args.freqtable)
if args.additional:
    args.exclude += args.additional
freq.ignorechars = args.exclude
freq.ignore_case = not args.case_sensitive
if args.verbose and args.verbose > 1:
   freq.verbose = True
filecontent = args.infile.readlines()
for eachline in sorted(filecontent, key = score, reverse=not args.reverse):
    if args.verbose:
       print(score(eachline), freq.probability(eachline), end=" ")
    if args.line:
       print("Found on line {} :".format(filecontent.index(eachline)), end=" ")
    print(eachline,end="")
