#!/usr/bin/env python3
#freq_server.py by Mark Baggett
#Twitter @MarkBaggett
#github http://github.com/MarkBaggett/
#This scripts runs a web server to provide a callable API to use frequency tables.
#
#Start the server passing it a port and a frequecy table.  For example:
#python freq_server.py 8080 english_lowercase.freq
#
#Now you can query the API to measure the character frequency of its characters.  
#wget http://127.0.0.1:8080/?cmd=measure\&tgt=measurethisstring
#
#You can also mark a string as normal.  NOTE: There is a performance impact to updating via the API.  Use CLI freq.py to update tables instead.
#wget http://127.0.0.1:8080/?cmd=normal\&tgt=UpdateFreqWithTheseChars&weight=10
#
#Thanks to @securitymapper for Testing & suggestions

from __future__ import print_function
from freq import *
import six
if six.PY2:
    import BaseHTTPServer
    import SocketServer
    import urlparse
else:
    import http.server as BaseHTTPServer
    import socketserver as SocketServer
    import urllib.parse as urlparse
import threading
import re
import argparse
import os
import resource


class freqapi(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.server.verbose: self.server.safe_print("Currently %s threads are active." % (threading.activeCount()))
        if self.server.verbose: self.server.safe_print("Memory usage: %s (kb)" % resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        self.send_response(200)
        self.send_header('Content-type','text/plain')
        self.end_headers()
        (ignore, ignore, urlpath, urlparams, ignore) = urlparse.urlsplit(self.path)
        cmdstr = tgtstr = None
        if self.server.verbose: self.server.safe_print(urlparams)
        legit_urls = r"[\/](measure|measure1|measure2|normal|{0})[\/].*?".format( "|".join(tables))
        cmd_regex = r"[\/](measure|measure1|measure2|normal{0})[\/].*$".format( "|".join(tables))
        tgtstr_regex = r"[\/](measure|measure1|measure2|normal|{0})[\/](.*)$".format( "|".join(tables))
        if re.search(legit_urls, urlpath):
            if self.server.verbose: self.server.safe_print("REST API CALL", urlpath)
            cmdstr = re.search(cmd_regex, urlpath)
            tgtstr = re.search(tgtstr_regex, urlpath)
            if not cmdstr or not tgtstr:
                help_str = 'API Documentation \nhttp://%s:%s/measure/<string> \nhttp://%s:%s/normal/<string> \n' % (self.server.server_address[0], self.server.server_address[1],self.server.server_address[0], self.server.server_address[1],self.server.server_address[0], self.server.server_address[1])
                self.wfile.write(help_str.encode("Latin-1"))
                return
            params = {}
            params["cmd"] = cmdstr.group(1)
            params["tgt"] = tgtstr.group(2)
        else:
            if self.server.verbose: self.server.safe_print("STANDARD API CALL", urlpath)
            cmd_regex = r"cmd=(?:measure|measure1|measure2|normal{0})".format( "|".join(tables))
            cmdstr=re.search(cmd_regex,urlparams)
            tgtstr =  re.search("tgt=",urlparams)
            if not cmdstr or not tgtstr:
                help_str = 'API Documentation\nhttp://%s:%s/?cmd=measure&tgt=<string> \nhttp://%s:%s/measure/<string> \nhttp://%s:%s/?cmd=normal&tgt=<string>&weight=<weight> \n' % (self.server.server_address[0], self.server.server_address[1],self.server.server_address[0], self.server.server_address[1],self.server.server_address[0], self.server.server_address[1])
                self.wfile.write(help_str.encode("LATIN-1"))
                return
            params={}
            try:
                for prm in urlparams.split("&"):
                    key,value = prm.split("=")
                    params[key]=value
            except:
                self.wfile.write('<html><body>Unable to parse the url. </body></html>'.encode("LATIN-1"))
                return
        if params["cmd"] == "normal":
            self.server.safe_print("cache cleared")
            try:
                self.server.cache_lock.acquire()
                self.server.cache ={}
            finally:
                self.server.cache_lock.release()
            try:
                self.server.fc_lock.acquire()
                weight = int(params.get("weight","1"))
                self.server.fc.tally_str(params["tgt"], weight=weight)
                self.server.dirty_fc = True
            finally:
                self.server.fc_lock.release()
            self.wfile.write('<html><body>Frequency Table updated</body></html>'.encode("LATIN-1")) 
        elif params["cmd"][:7] == "measure":
            if params["tgt"] in self.server.cache:
                if self.server.verbose: self.server.safe_print ("Query from cache:", params["tgt"])
                measure =  self.server.cache.get(params["tgt"])
            else:
                if self.server.verbose: self.server.safe_print ( "Added to cache:", params["tgt"])
                measure = self.server.fc.probability(params["tgt"])
                try:
                    self.server.cache_lock.acquire()
                    self.server.cache[params["tgt"]]=measure
                finally:
                    self.server.cache_lock.release()
                if self.server.verbose>=2: self.server.safe_print ( "Server cache: ", str(self.server.cache))
            if params["cmd"].endswith("1"):
                measure = measure[0]
            elif params["cmd"].endswith("2"):
                measure = measure[1]
            self.wfile.write(str(measure).encode("LATIN-1"))
        elif any([x.startswith(params["cmd"]) for x in freqtables]):
            if params["tgt"] in self.server.cache:
                if self.server.verbose: self.server.safe_print ("Query from cache:", params["tgt"])
                measure =  self.server.cache.get(params["tgt"])
            else:
                if self.server.verbose: self.server.safe_print ( "Added to cache:", params["tgt"])
                measure = self.server.fcs[params["cmd"]].probability(params["tgt"])
                try:
                    self.server.cache_lock.acquire()
                    self.server.cache[params["tgt"]]=measure
                finally:
                    self.server.cache_lock.release()
                if self.server.verbose>=2: self.server.safe_print ( "Server cache: ", str(self.server.cache))
            if params["cmd"].endswith("1"):
                measure = measure[0]
            elif params["cmd"].endswith("2"):
                measure = measure[1]
            self.wfile.write(str(measure).encode("LATIN-1"))
            return

    def log_message(self, format, *args):
        return

class ThreadedFreqServer(SocketServer.ThreadingMixIn, BaseHTTPServer.HTTPServer):
    def __init__(self, *args,**kwargs):
        self.fcs = {}
        self.fc = FreqCounter()
        self.cache = {}
        self.cache_lock = threading.Lock()
        self.screen_lock = threading.Lock()
        self.verbose = False
        self.fc_lock = threading.Lock()
        self.dirty_fc = False
        self.exitthread = threading.Event()
        self.exitthread.clear()
        BaseHTTPServer.HTTPServer.__init__(self, *args, **kwargs)

    def safe_print(self,*args,**kwargs):
        try:
            self.screen_lock.acquire()
            print(*args,**kwargs)
        finally:
            self.screen_lock.release()

    def save_freqtable(self,save_path,save_interval):
        if self.verbose: self.safe_print ( "Save interval reached.")
        if self.dirty_fc:
            if self.verbose: self.safe_print ("Frequency counter changed.  Saving to disk.",save_path)
            try:
                self.fc_lock.acquire()
                self.fc.save(save_path)
                self.dirty_fc = False
            finally:
                self.fc_lock.release()
        else:
            if self.verbose: self.safe_print ("Frequency counter not changed.  Not Saving to disk.")
        #Reschedule yourself
        if not self.exitthread.isSet():
            self.timer = threading.Timer(60*save_interval, self.save_freqtable, args = (save_path,save_interval))
            self.timer.start()

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument('-ip','--address',required=False,help='IP Address for the server to listen on.  Default is 127.0.0.1',default='127.0.0.1')
    parser.add_argument('-s','--save_interval',type=float,required=False,help='Number of minutes to wait before trying to save frequency table updates. Default is 10 minutes.  Set to 0 to never save.',default=10)
    parser.add_argument('port',type=int,help='You must provide a TCP Port to bind to')
    parser.add_argument('freq_table',nargs="*", help='You must provide the frequency table name (optionally including the path)')
    parser.add_argument('-v','--verbose',action='count',default=0,required=False,help='Print verbose output to the server screen.  -vv is more verbose.')

    #args = parser.parse_args("-s 1 -vv 8081 english_lowercase.freq".split())
    args = parser.parse_args()
    
    #split paths and filenames on frequency tables
    freqtables = list(map(lambda x:x[1], map(os.path.split, args.freq_table)))
    tables = freqtables
    tables += [x+"1" for x in freqtables]
    tables += [x+"2" for x in freqtables]

    #Setup the server.
    server = ThreadedFreqServer((args.address, args.port), freqapi)

    #Load Each of the Frequency Table
    for eachtable in args.freq_table:
        path,tablename = os.path.split(eachtable)
        server.fcs[tablename] = FreqCounter()
        try:
            server.fcs[tablename].load(eachtable)
        except:
            err = "********** Unable to load Frequency table {0}. ************".format(eachtable)
            raise(Exception(err))
            del server.fcs[eachtable]

    #setup default freq_table
    server.fc = server.fcs[freqtables[0]]
    server.verbose = args.verbose

    #Schedule the first save interval unless save_interval was set to 0.
    if args.save_interval:
        server.timer = threading.Timer(60 *args.save_interval, server.save_freqtable, args = (args.freq_table[0], args.save_interval))
        server.timer.start()
 
    #start the server
    print('Server is Ready. http://%s:%s/?cmd=measure&tgt=astring' % (args.address, args.port))
    print('[?] - Remember: If you are going to call the api with wget, curl or something else from the bash prompt you need to escape the & with \& \n\n')
    while True:
        try:
            server.handle_request()
        except KeyboardInterrupt:
            break
        
    server.safe_print("Control-C hit: Exiting server...")
    server.safe_print("Web API Disabled...")
    if args.save_interval and server.dirty_fc:
        server.safe_print("The Frequency counter has changed since the last save interval. Saving final update.")
        server.exitthread.set()
        server.timer.cancel()
        try:
            server.fc_lock.acquire()
            server.fc.save(args.freq_table[0])
            server.fc_lock.release
        except:
            server.safe_print("[!] An error occured during the final save.")
    elif args.save_interval:
        server.safe_print( "No Changes made since last file save.  Canceling scheduled save...")
        server.timer.cancel()
    server.safe_print("Server has stopped.")
    

