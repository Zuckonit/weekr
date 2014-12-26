#!/usr/bin/env python
# encoding: utf-8

import os
import os.path as osp
import platform
import time
import commands
import xml.etree.ElementTree as ET
try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict

OS_SYSTEM = platform.system()
IS_WINDOWS = OS_SYSTEM == "Windows"
if not IS_WINDOWS:
    from pwd import getpwuid


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
        if not IS_WINDOWS:
            author = getpwuid(os.stat(filename).st_uid).pw_name
        else:
            author = None
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
                yield date, msg, self.who or self.usr or author or 'unkown', rev
