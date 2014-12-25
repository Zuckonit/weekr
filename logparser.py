#!/usr/bin/env python
# encoding: utf-8

import os
import os.path as osp
from pwd import getpwuid
import time
import datetime
import commands
import xml.etree.ElementTree as ET
try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict



class Command(object):

    def __init__(self, cmd):
        self.__cmd = cmd

    @property
    def cmdline(self):
        return self.__cmd

    def run(self):
        try:
            status, stdout = commands.getstatusoutput(self.cmdline)
            return status, stdout
        except:
            return None, None


class LogParser(object):

    def __init__(self, usr=None, pwd=None, who=None, path=None, sdate=None, edate=None):
        self.usr = usr
        self.pwd = pwd
        self.who = who
        self.path = path
        self.sdate = sdate
        self.edate = edate

    def getcmd(self):
        pass

    def yield_log(self):
        raise NotImplementedError

    def get_log_by_date(self):
        """
        group by date
        {
            'date1': [(rev, author, msg), (rev, author, msg)],
            'date2': [(rev, author, msg), (rev, author, msg)]
        }
        """
        logs = OrderedDict()
        for rev, author, date, msg in self.yield_log():
            if date in logs:
                logs[date].append((rev, author, msg))
            else:
                logs[date] = [(rev, author, msg)]
        return logs


class SVNLogParser(LogParser):

    def __init__(self, usr=None, pwd=None, who=None, path=None, sdate=None, edate=None):
        super(SVNLogParser, self).__init__(usr=usr, pwd=pwd,
                who=who, path=path, sdate=sdate, edate=edate)

    def getcmd(self):
        cmd = u'svn log'
        if self.path:
            cmd += u' {0}'.format(self.path)
        if self.usr:
            cmd += u' --username {0}'.format(self.usr)
        if self.pwd:
            cmd += u' --password {0}'.format(self.pwd)
        if self.sdate and self.edate:
            cmd += u' -r {%s}:{%s}'%(self.sdate, self.edate)
        cmd += u' --xml'
        cmd += u' --search {0}'.format(self.who or self.usr)
        return Command(cmd)

    def yield_log(self):
        _, stdout = self.getcmd().run()
        if not stdout:
            return

        root = ET.fromstring(stdout)
        for log in root.findall('logentry'):
            rev = log.get('revision')
            author = log.find('author').text
            date = log.find('date').text[:10]
            msg = log.find('msg').text
            yield rev, author, date, msg


class GITLogParser(LogParser):

    def __init__(self, usr=None, pwd=None, who=None, path=None, sdate=None, edate=None):
        super(GITLogParser, self).__init__(usr=usr, pwd=pwd,
                who=who, path=path, sdate=sdate, edate=edate)

    def getcmd(self):
        cmd = u'git log'
        if self.path:
            cmd = cmd + u' {0}'.format(self.path)
        if self.sdate:
            cmd = cmd + u' --after="{0}"'.format(self.sdate)
        if self.edate:
            cmd = cmd + u' --before="{0}"'.format(self.edate)
        cmd += u' --date="short" --pretty=format:"%T,%cd, %s"'
        cmd += u' --committer {0}'.format(self.who or self.usr)
        return Command(cmd)

    def yield_log(self):
        cmd = self.getcmd()
        _, stdout = cmd.run()
        if not stdout:
            return

        for line in stdout.split('\n'):
            rev, date, msg = line.split(',')
            yield rev, self.who or self.usr , date, msg


class TodoLogParser(LogParser):
    """
    GTD: my `vim-airline-todo` plugin
    """
    def __init__(self, usr=None, pwd=None, who=None, path=None, sdate=None, edate=None):
        super(TodoLogParser, self).__init__(usr=usr, pwd=pwd,
                who=who, path=path, sdate=sdate, edate=edate)
    
    @staticmethod
    def get_file_info(filename):
        if not filename or not osp.isfile(filename):
            return None, None, None, None
        mtime = osp.getmtime(filename)       
        ltime = time.localtime(mtime)
        date  = time.strftime('%Y-%m-%d', ltime)
        msg   = osp.basename(filename)
        author= getpwuid(os.stat(filename).st_uid).pw_name
        rev   = 0
        return rev, author, date, msg

    def yield_filenames(self, ignore_hide_file=True, ignore_prefix=(), ignore_suffix=()):
        """other params may be useful in future"""
        path = osp.expanduser(self.path)
        path = osp.abspath(path)
        if not path or not osp.isdir(path):
            return

        for root, dirs, fnames in os.walk(path):
            for f in fnames:
                if ignore_hide_file and f.startswith('.'):
                    continue
                if f.endswith(ignore_suffix):
                    continue
                if f.startswith(ignore_prefix):
                    continue
                
                yield osp.join(root, f)

    def yield_log(self, ignore_hide_file=True, ignore_prefix=(), ignore_suffix=()):
        tasks = self.yield_filenames(ignore_hide_file, ignore_prefix, ignore_suffix)
        for t in tasks:
            rev, author, date, msg = self.get_file_info(t)
            if self.sdate <= date <= self.edate:
                yield date, msg, self.who or author, rev



def get_date_period(bdays):
    sdate =((datetime.datetime.now()-datetime.timedelta(days=bdays)).strftime("%Y-%m-%d"))
    edate = time.strftime("%Y-%m-%d")
    return sdate, edate


def get_parser_class(vst):
    if vst == 'svn':
        return SVNLogParser
    elif vst == 'git':
        return GITLogParser
    elif vst == 'todo':
        return TodoLogParser
    return None


def cmdline(arg):
    from optparse import OptionParser
    parser = OptionParser(usage="usage: %prog", version="%prog 0.0.3")
    parser.add_option('-u', "--username", dest='username', metavar='USER',
            default=None, help='username of your repo')
    parser.add_option('-p', "--password", dest='password', metavar='PSWD',
            default=None, help='password of your repo')
    parser.add_option('-w', "--who", dest='who', metavar='WHO',
            default=None, help='whose log you want to see, if its None, then use usrname as default')
    parser.add_option('-t', "--version-control-type", dest='vtype', metavar='TYPE',
            default="svn", help='your version control system')
    parser.add_option('-d', "--repo-path", dest='path', metavar='PATH',
            default=None, help='path of your repo which you want to get log')
    parser.add_option('-s', "--start-date", dest='sdate', metavar='SDATE',
            default=None, help='start date')
    parser.add_option('-e', "--end-date", dest='edate', metavar='EDATE',
            default=None, help='end date')
    parser.add_option('-b', "--before-days", dest='bdays', type="int", metavar='BDATE',
            default=None, help='how many days before today')
    return parser.parse_args(arg)



if __name__ == '__main__':
    import sys

    if len(sys.argv) == 1:
        print 'type {0} -h to get help'.format(osp.basename(sys.argv[0]))
        sys.exit(1)

    options, args = cmdline(sys.argv)
    sdate = options.sdate
    edate = options.edate
    vsc   = options.vtype
    if vsc is None:
        print 'version control system [0]: no supported yet'.format(vsc)
        sys.exit(1)
    if not sdate and not edate and options.bdays:
        sdate, edate = get_date_period(options.bdays)


    Parser = get_parser_class(vsc)

    parser = Parser(
        usr=options.username,
        pwd=options.password,
        who=options.who,
        path=options.path,
        sdate=sdate,
        edate=edate
    )

    print 'parse by line......'
    for version, author, date, msg in parser.yield_log():
        print version, author, date, msg

    print 'parse by date......'
    print parser.get_log_by_date()
