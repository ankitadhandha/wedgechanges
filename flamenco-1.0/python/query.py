# Copyright (c) 2004-2006 The Regents of the University of California.

def sorted(list):
    copy = list[:]
    copy.sort()
    return copy

class Query:
    """Query objects.

    All queries in this interface are expressed as a set of terms, where
    each term is a 3-tuple (facet, value, leaf).  'facet' is a facet
    identifier, 'value' is an ID in that facet, and 'leaf' is a flag
    indicating whether the term must be a leaf-node match."""

    # ------------------------------------------------------- serialization
    def __init__(self, db, terms=[], words=[], text=''):
        self.db = db
        self.terms = terms[:]
        self.words = words[:]
        for part in text.split('/'):
            if ':' in part:
                [facet, values] = part.split(':')
                for value in values.split(','):
                    if value:
                        leaf = (value[:1] == '*')
                        if leaf: value = value[1:]
                        if value[:1] == "'" == value[-1:]: value = value[1:-1]
                        else: value = int(value)
                        self.terms.append((facet, value, leaf))
            else:
                if part: self.words.append(part)
        self.terms.sort()
        self.words.sort()

    def __repr__(self): return '<Query %s>' % self.serialize()
    def __str__(self): return self.serialize()

    def serialize(self):
        values = {}
        for facet, value, leaf in self.terms:
            values.setdefault(facet, []).append((value, leaf))
        return '/'.join([
            facet + ':' + ','.join([(leaf and '*' or '') +
                                    (type(value) == type('') and 
                                        ("'" + str(value) + "'") or str(value))
                                    for value, leaf in sorted(values[facet])])
            for facet in sorted(values.keys())] + sorted(self.words))

    # --------------------------------------------------------- examination
    def __len__(self): return len(self.terms + self.words)

    def getterms(self): return self.terms
    def getwords(self): return self.words

    # -------------------------------------------------------- manipulation
    def __add__(self, term):
        if term in self.terms: return self.copy()
        if type(term) is type(''):
            words = self.words[:]
            if term not in words: words.append(term)
            return Query(self.db, self.terms, words)
        else:
            f, value, leaf = term
            if type(value) is type(''):
                newterms = [t for t in self.terms if t != term]
            else:
                path = self.db.path(f, value)
                newterms = [t for t in self.terms
                            if t[0] != f or t[1] not in path]
            return Query(self.db, newterms + [term], self.words)

    def __sub__(self, term):
        words = [w for w in self.words if w != term]
        terms = [t for t in self.terms if t != term]
        return Query(self.db, terms, words)

    def copy(self):
        return Query(self.db, self.terms, self.words)
