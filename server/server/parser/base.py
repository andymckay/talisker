import glob
import os
import re
import StringIO
import sys

import pstats


class Stats(pstats.Stats):
    def __init__(self, *args, **kw):
        pstats.Stats.__init__(self, *args, **kw)
        self.stream = StringIO.StringIO()
        
    def print_stats(self, *amount):
        data = {
            'lines': [],
            'total_calls': self.total_calls,
            'total_time': '%.3f' % self.total_tt
        }
        for bits in self.get_print_list(amount)[1]:
            line = {
                'filename_short': os.path.basename(bits[0]),
                'filename_full': bits[0],
                'line': bits[1],
                'func': bits[2] 
            }
            cc, nc, tt, ct, callers = self.stats[bits]
            line.update({
               'number': nc,
               'total': '%.5f' % tt,
               'cumulative': '%.5f' % ct,
            })
            data['lines'].append(line)

        return data


class Request(object):
    def __init__(self, filename, stat, time):
        self.stat = stat
        self.filename = filename
        self.time = float(time[:-2])/1000
    
    def all(self):
        data = self.stat.print_stats()
        data['name'] = self.filename
        data['count'] = 1
        return data


class RequestCollection(object):
    def __init__(self, key):
        self.key = key
        self.stats = []
        self.stat = None
        self.filename = self.key
        
    def add(self, filename, time):
        stat = Stats(filename)
        self.stats.append(Request(self.filename, stat, time))
        if not self.stat:
            self.stat = stat
        else:
            self.stat.add(filename)

    def all(self):
        data = self.stat.print_stats()
        data['name'] = self.filename
        data['count'] = len(self.stats)
        return data

    def summary(self):
        return {'request': self.key,
                'count': len(self.stats),
                'times': [s.time for s in self.stats]}


class Collection(object):
    def __init__(self, directory, blacklist=None):        
        self.requests = {}
        self.directory = directory
        self.files = []
        self.blacklist = [ re.compile(b) for b in blacklist if blacklist ]
        self.update()
                
    def listing(self):
        res = sorted([(len(v.stats), k) for k, v in self.requests.items()])
        res.reverse()
        return res
        
    def update(self):
        flag = False
        if not self.directory.endswith(os.sep):
            self.directory = self.directory + os.sep
        for filename in glob.glob('%s*.prof' % self.directory):
            for b in self.blacklist:
                if b.match(filename[len(self.directory):]):
                    os.remove(filename)
                    continue
            if os.path.exists(filename) and filename not in self.files:
                try:
                    data = os.path.basename(filename).rsplit('.', 4)
                    self.requests.setdefault(data[0], RequestCollection(data[0]))
                    self.requests[data[0]].add(filename, data[1])
                    self.files.append(filename)
                except (IOError, ValueError, EOFError):
                    print "Failed with:", filename
                    print sys.exc_value
                
                flag = True
        return flag

if __name__=='__main__':
    col = Collection('/tmp/output/')
    print col.listing()
    for request in col.requests.values():
        print request.key
        print
        print request.summary()
        print request.all()