# Copyright (c) 2004-2006 The Regents of the University of California.

from Page import Page
from app import users, tasks
from html import *

def findorcreate(store, name):
    if name in store:
        return store.index(name)
    else:
        id = store.new()
        store[id].name = name
        return id

class Main(Page):
    def metatag(self):
        return 'name="robots" content="noindex,nofollow"'
    
    def title(self):
        return 'Welcome to the Longitudinal Browser study'

    def body(self, out):
        if self.form.get('flush'):
            import app; reload(app)
        import components; reload(components)
        #out.write(self.login())
        out.write(self.interfaces())

    def login(self):
        usercell = ['User name: ', input(type='text', name='username')]
        if self.form.get('action') == 'clear':
            del self.session.userid, self.session.taskid
        if self.form.get('username') and self.form.action == 'set':
            self.session.userid = findorcreate(users, self.form.username)
        if 'userid' in self.session:
            usercell += [br, 'Current user: ',
                         strong(users[self.session.userid].name),
                         ' (%d)' % self.session.userid]
        taskcell = ['Task name: ', input(type='text', name='taskname')]
        if self.form.get('taskname') and self.form.action == 'set':
            self.session.taskid = findorcreate(tasks, self.form.taskname)
        if 'taskid' in self.session:
            taskcell += [br, 'Current task: ',
                         strong(tasks[self.session.taskid].name),
                         ' (%d)' % self.session.taskid]
        submit = [input(type='submit', name='action', value='set'),
                  input(type='submit', name='action', value='clear')]
        return [p, 'Enter a user name and task name to begin a session:',
                form(tablew(trt(td(usercell), td(taskcell), td(submit))))]

    def interfaces(self):
        return [p, 'To begin using the interface, ',
                tablew(tr(td(nbsp)),
                       tr(td(tablew(
            #tr(tdc(link('Flamenco?manage=7', 'Log in')))))))]
            tr(tdc(link('Wedge?manage=7', 'Log in')))))))]
