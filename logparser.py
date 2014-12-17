#!/usr/bin/env python
# encoding: utf-8

import time
import datetime
import commands
import xml.etree.ElementTree as ET


def get_xml(usr=None, pwd=None, who=None, path=None, sdate=None, edate=None):
    try:
        cmd = u'svn log'
        if path:
            cmd += u' {0}'.format(path)
        if usr:
            cmd += u' --username {0}'.format(usr)
        if pwd:
            cmd += u' --password {0}'.format(pwd)
        if sdate and edate:
            cmd += u' -r {%s}:{%s}'%(sdate, edate)
        cmd += u' --xml'
        cmd += u' --search {0}'.format(who or usr)
        print cmd
        return commands.getstatusoutput(cmd)
    except Exception as e:
        print e
        return None


def parse_xml(stdout):
    if not stdout:
        return

    root = ET.fromstring(stdout)
    for log in root.findall('logentry'):
        yield log.get('revision'), log.find('author').text, log.find('date').text, log.find('msg').text


def get_date_period(bdays):
    sdate =((datetime.datetime.now()-datetime.timedelta(days=bdays)).strftime("%Y-%m-%d"))
    edate = time.strftime("%Y-%m-%d")
    return sdate, edate


def cmdline(arg):
    from optparse import OptionParser
    parser = OptionParser(usage="usage: %prog", version="%prog 0.0.3")
    parser.add_option('-u', "--username", dest='username', metavar='USER',
            default=None, help='username of your svn repo')
    parser.add_option('-p', "--password", dest='password', metavar='PSWD',
            default=None, help='password of your svn repo')
    parser.add_option('-w', "--who", dest='who', metavar='WHO',
            default=None, help='whose log you want to see, if its None, then use usrname as default')
    parser.add_option('-d', "--repo-path", dest='path', metavar='PATH',
            default=None, help='path of your svn repo which you want to get log')
    parser.add_option('-s', "--start-date", dest='sdate', metavar='SDATE',
            default=None, help='start date')
    parser.add_option('-e', "--end-date", dest='edate', metavar='EDATE',
            default=None, help='end date')
    parser.add_option('-b', "--before-days", dest='bdays', type="int", metavar='BDATE',
            default=None, help='how many days before today')
    return parser.parse_args(arg)



if __name__ == '__main__':
    import sys
    import os.path as osp

    if len(sys.argv) == 1:
        print 'type {0} -h to get help'.format(osp.basename(sys.argv[0]))
        sys.exit(1)

    options, args = cmdline(sys.argv)
    sdate=options.sdate
    edate=options.edate
    
    if not sdate and not edate and options.bdays:
        sdate, edate = get_date_period(options.bdays)
    print sdate, edate
    _, xml_str = get_xml(
        usr=options.username, 
        pwd=options.password,
        who=options.who,
        path=options.path,
        sdate=sdate,
        edate=edate
    )
    for version, author, date, msg in parse_xml(xml_str):
        print version, author, date, msg
