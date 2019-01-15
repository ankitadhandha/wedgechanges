# Copyright (c) 2004-2006 The Regents of the University of California.


"""Edit this template to yield the Collection.py file for an instance."""

from BaseCollection import BaseCollection
from html import *

class Collection(BaseCollection):
    # These are some commonly customized parameters.  For the complete set
    # of all parameters and methods, see the definition of BaseCollection.

    # Change these values to customize the page title and heading.
    PAGE_TITLE = 'Generic Collection'
    PAGE_HEADING = 'Main Heading'
    PAGE_SUBHEADING = 'Subheading'

    # Change these values to customize the page layout.
    ITEMS_PER_GROUP = 4
    ITEMS_PER_ROW = 4
    ITEMS_PER_HISTORY_ROW = 4
    ITEMS_PER_GROUPED_PAGE = 99
    ITEMS_PER_UNGROUPED_PAGE = 40

    # When customizing the following functions, you may find these useful:
    #
    #     self.db.attrlist - a list of the attribute identifiers
    #     self.db.facetlist - a list of the facet identifiers
    #     self.db.name(attr) - get the displayable name of an attribute
    #     self.db.name(facet) - get the displayable name of a facet
    #     self.db.name(facet, id) - get displayable name of a category
    #     self.db.metadata(item) - get all the metadata about an item
    #
    # The metadata dictionary returned by self.db.metadata(item) contains
    # key-value pairs for all the attributes and facets.  Each attribute
    # appears with the attribute identifier as the key and a string as the
    # value.  Each facet appears with the facet identifier as the key and
    # a list of category IDs as the value.

    # facetlist and attrlists select which facets and attributes are shown.
    def __init__(self, db):
        self.db = db # Don't change this.
        self.facetlist = db.facetlist # Display all facets.
        self.attrlist = db.attrlist # Display all attributes.

    # Change this function to customize the display of items in listings.
    #     item - identifier of the item to display
    #     query - query that generated the result set
    #     index - numeric index of the item in the result set
    #     link - call this with arguments (content, query=query, index=index)
    #            to create a link to a page of details on a single item
    def itemlisting(self, item, index, link=None, query=None, **args):
        metadata = self.db.metadata(item)
        listing = metadata[self.db.attrlist[0]] # Show the first attribute.
        if link:
            listing = link(listing, query=query, index=index)
        return listing

    # Change this function to customize the display of single-item pages.
    #     item - identifier of the item to display
    #     request - information about the HTTP request
    #     request.remoteAddress() - IP address of the requesting client
    def itemdisplay(self, item, request, *args, **kw):
        metadata = self.db.metadata(item)
        fieldtext = ['%s: %s' % (attr, metadata[attr])
                     for attr in self.db.attrlist]
        return br.join(fieldtext)
