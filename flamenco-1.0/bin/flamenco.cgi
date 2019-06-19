#!/usr/bin/env python

# This CGI script can be placed anywhere that a webserver will execute it.
# Access to all Flamenco instances is provided through this one script.
# Ka-Ping Yee <ping@sims.berkeley.edu>, September 21, 2005

# --------------------------------------------------------------------------
# The following line should specify the Flamenco installation directory.

FLAMENCO_DIR = '/usr/local/flamenco'

# --------------------------------------------------------------------------

import sys, os, time, cgitb
cgitb.enable()

thisfile = os.path.basename(__file__)
INSTANCES_DIR = os.path.join(FLAMENCO_DIR, 'instances')
path = os.environ.get('PATH_INFO', '').replace('/', ' ').split()
instance = path and path[0] or ''
os.environ['PATH_INFO'] = '/' + '/'.join(path[1:])

def exists(instance):
    instdir = os.path.join(INSTANCES_DIR, instance)
    return os.path.isdir(instdir)

def running(instance):
    instdir = os.path.join(INSTANCES_DIR, instance)
    pidfile = os.path.join(instdir, 'appserverpid.txt')
    if os.path.isfile(pidfile):
        pid = open(pidfile).read().strip()
        for line in os.popen('ps -o pid -p %s' % pid, 'r'):
            if line.strip() == pid:
                return 1
    return 0

def quit(*text):
    print 'Content-Type: text/html\n\n'
    print '''<head>
    <title>WEDGE - Web Enabled Directed Graph Engine</title>
    <style>
body { font-family: lucida grande, verdana, sans-serif; margin: 0; }
div.logo { border: 1px solid gray; }
img { padding: 1em; background-color: #fff; }
h1, h2 { padding: 16px; color: #fd4; background: #248; margin: 0; }
h1 a, h2 a { color: #fd4; }
h1 { font-size: 24px; padding-bottom: 0; }
h2 { font-size: 10px; font-weight: normal; padding-top: 0; }
div.container { font-size: 12px; padding: 16px; }
div { font-size: 12px; padding: 16px; }
pre { padding-left: 32px; }
</style>
<link rel="shortcut icon" href="https://dockerresourcesforwedge.s3.amazonaws.com/favicons/favicon.ico">
</head>
<div class="logo">
<img src="https://dockerresourcesforwedge.s3.amazonaws.com/logo/_logo_wedge_w201_h60_.png" alt="Wedge logo">
</div>
<div>%s</div>''' % '\n'.join(text)
    sys.exit(0)

try:
    sys.path.insert(1, os.path.join(FLAMENCO_DIR, 'python'))
    import MySQLdb
except:
    quit('''The MySQLdb module for Python could not be loaded.  Flamenco
            needs this module in order to work.  Please reinstall Flamenco
            or <a href="http://sf.net/projects/mysql-python/">download the
            module from SourceForge</a>.''')

if instance:
    launchable = os.access(os.path.join(
        INSTANCES_DIR, instance, 'flamenco-%s' % instance), os.X_OK)
    if exists(instance):
        if not running(instance):
            if not launchable:
                quit('The %r instance is not running ' % instance,
                     'and autostart is not enabled for this instance.')
            server = os.path.join(FLAMENCO_DIR, 'bin', 'flamenco-server')
            os.system('%s "%s" &' % (server, instance))
            for i in range(15):
                time.sleep(1)
                if running(instance):
                    break
        if running(instance):
            WEBWARE_DIR = os.path.join(FLAMENCO_DIR, 'webware')
            sys.path.insert(1, WEBWARE_DIR)
            from WebKit.Adapters import CGIAdapter
            CGIAdapter.main(os.path.join(INSTANCES_DIR, instance))
        else:
            LOG_PATH = os.path.join(INSTANCES_DIR, instance, 'log.txt')
            log = '<p>Check the log file at %r for more details. ' % LOG_PATH
            try:
                loglines = os.popen('tail -25 "%s"' % LOG_PATH).read()
                loglines = loglines.replace('&', '&amp;').replace('<', '&lt;')
                log += 'Here are the last few lines: <pre>%s</pre>' % loglines
            except:
                pass
            quit('The %r instance failed to start. %s' % (instance, log))
    else:
        quit('There is no Flamenco instance named %r.' % instance)
else:
    items = []
    if not os.path.isdir(INSTANCES_DIR):
        quit('The instance directory %r is missing.' % INSTANCES_DIR)
    
    instances_dir1 = os.listdir(INSTANCES_DIR)
    instances_dir1.sort()
    
    for instance in instances_dir1: #os.listdir(INSTANCES_DIR):
        dir = os.path.join(INSTANCES_DIR, instance)
        #url = '%s/%s/Flamenco' % (thisfile, instance)
        url = '%s/Wedge' % (instance)
        if os.path.isdir(dir):
            if os.access(os.path.join(dir, 'flamenco-%s' % instance), os.X_OK):
                items.append('<li><a href="%s">%s</a>' % (url, instance))
                if not running(instance):
                    items.append('(not running, click to start)')
            elif running(instance):
                items.append('<li><a href="%s">%s</a>' % (url, instance))
            else:
                items.append('<li>%s (not running, not startable)' % instance)
    if items:
        quit('Choose a Flamenco instance:', '<ul>%s</ul>' % '\n'.join(items))
    else:
        quit('There are no Flamenco instances yet. ',
             'To create one, use the command:',
             '<pre>%s/bin/flamenco import</pre>' % FLAMENCO_DIR)
