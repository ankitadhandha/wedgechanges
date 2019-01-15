# For this example, we display the name and photo of each Nobel Prize
# winner as the item.

from BaseCollection import BaseCollection
from html import *

class Collection(BaseCollection):
    PAGE_TITLE = 'Nobel Prize Winners'
    PAGE_HEADING = 'Nobel Prize Winners'
    PAGE_SUBHEADING = '1901 to 2004'

    def __init__(self, db):
        self.db = db

        # Always show all the facets.
        self.facetlist = db.facetlist

        # Don't show the attributes that contain URLs.
        self.attrlist = [
            attr for attr in db.attrlist
            if attr not in ['biography', 'lecture', 'history', 'photo']]

    def itemdisplay(self, item, request):
        metadata = self.db.metadata(item)
        if metadata['birthyear'] or metadata['deathyear']:
            lifespan = [metadata['birthyear'], '-', metadata['deathyear']]
        else:
            lifespan = []
        links = []
        if metadata['biography']:
            links += [br, link(metadata['biography'], 'Biography')]
        if metadata['lecture']:
            links += [br, link(metadata['lecture'], 'Nobel Lecture')]
        if metadata['history']:
            links += [br, link(metadata['history'], 'History')]
        return [img(metadata['photo']), br,
                metadata['name'], br, lifespan, links]

    def itemlisting(self, item, index, link=None, query=None, **args):
        metadata = self.db.metadata(item)
        listing = [img(metadata['photo']), br,
                   abbrev(metadata['name'], 20), br,
                   metadata['birthyear'], '-', metadata['deathyear']]
        if link:
            listing = link(listing, query=query, index=index)
        return listing
