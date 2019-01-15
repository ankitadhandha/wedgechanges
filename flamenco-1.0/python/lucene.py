# Copyright (c) 2004-2006 The Regents of the University of California.

"""Python-side interface to the Lucene search engine."""

import os

DIR='/projects/flamenco/lucene'
PATHS=['.', 'lucene-1.2.jar']

CLASSPATH=':'.join([os.path.join(DIR, path) for path in PATHS])
JAVA='java -cp ' + CLASSPATH

class Lucene:
    def __init__(self, indexpath):
        program = JAVA + ' Search'
        self.writer, self.reader = os.popen2(program + ' ' + indexpath)
        status = self.reader.readline()
        if not status.startswith('+'):
            raise RuntimeError, 'failed to start Lucene: ' + status
        self.cache = {}

    def search(self, query):
        if query in self.cache:
            print '---- cached:', query
            return self.cache[query]
        print "---- lucene:", query
        self.writer.write(query + '\n')
        self.writer.flush()
        status = self.reader.readline()
        if not status.startswith('+'):
            raise RuntimeError, 'Lucene query failed: ' + status
        results = self.reader.readline().split()
        print "---- results:", len(results)
        self.cache[query] = results
        return results
