#!/usr/bin/env python
# encoding: utf-8

import sys
import os.path as osp
import time
import datetime
from weekr.core.logparser import SVNLogParser, GITLogParser, TodoLogParser



def get_date_period(bdays):
    sdate =((datetime.datetime.now()-datetime.timedelta(days=bdays)).strftime("%Y-%m-%d"))
    edate = time.strftime("%Y-%m-%d")
    return sdate, edate


def get_parser_class(vst):
    if vst == 'svn':
        return SVNLogParser
    elif vst == 'git':
        return GITLogParser
    elif vst == 'tomato':
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
