## freq
This is a repository for `freq.py` and `freq_server.py`.

### Background:
While sitting in SANS SEC511 I listened to [`@sethmisenar`](https://twitter.com/sethmisenar) laement the difficulty in using existing tools to detect DGA (Domain Generation Algorithm) hostnames often used by malware.  There are lots of AI based tools out there that do this but some are rather complex. I thought I could quickly write a tool that would work.  In about 30 minutes I threw together some old code I had lying around from a SQL Injection tool I worked on and I had a working proof of concept.  `freq.py` was born and it worked pretty well.  A year later [`@securitymapper`](https://twitter.com/securitymapper) had me wrap it in a web interface so he could query it from a SIEM and then the tool took off.  It turns out to be a pretty effective technique and gained some popularity and wide use!   This is a rewrite of the tool that incorporates some lessons learned and performance enhancements.

### Recent Improvements:
- Only one table is required for case sensitve or insensitive lookups. The tables are all case sensitive.  You can turn off and on case sensitivity and the .probability lookups will do what is needed to make them case insensitive.
- Ignored characters with `--exclude` option.  Like `--ignore_case`, the characters are only ignored in the calculations of the probability. They are not ignored in the building of the table.
- Speed.  Like I said.  It was a proof of concept and never really built with any performance in mind.  This fixes that.
- Accuracy.  Some errors in calulations were identified by Pepe Berta (thanks!).  This fixes those and several others.  If you find others let me know.
- Two calculations - I've added a second frequency score that I've calculated differently.  It will requires some testing to see if it is more useful than the previous number in detecting random hosts.
- Multiple freq tables can be passed and loaded on the CLI then processed in the url.  For example: `python3 freq_server.py 9000 files.freq dns.freq`  Then query the url with the table name instead of measure like this `http://127.0.0.1:9000/dns.freq/hostname` or `http://127.0.0.1:9000/dns.freq1/hostname` for just measurement 1.


### Version Compatibility:
`freq.py` will work in either Python2 or Python3.  The web server `freq_server.py` will also be updated in the future.

### System-level Service Startup:
A systemd startup file is provided, although you will likely need to adjust paths to the script and `freqtable2018.freq` file. The provided sample assumes you've cloned this repository to /usr/local/share/freq/. Enable with something like the following, again substituting the appropriate paths:

```
$ sudo systemctl enable /usr/local/share/freq/systemd/freq.service
$ sudo systemctl start freq.service
```

### To Do:
