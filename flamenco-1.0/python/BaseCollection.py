# Copyright (c) 2004-2006 The Regents of the University of California.

"""The base collection class.

This class defines the default display for a collection.  To customize the
interface for a particular collection, define a subclass named Collection."""

import os
from html import *

class BaseCollection:
    luceneindex = None # path to lucene index directory

    USER_PERSONALIZATION = 1
    IMAGE_COLLECTION = 1

    # Each facet box in the sidebar lists its terms in two columns if all
    # terms are at most this length, or one column if any term is longer.
    MIDDLEGAME_COLUMN_WIDTH = 32

    # Change these values to customize the page layout.
    ITEMS_PER_GROUP = 4
    ITEMS_PER_ROW = 4
    ITEMS_PER_HISTORY_ROW = 4
    ITEMS_PER_GROUPED_PAGE = 99
    ITEMS_PER_UNGROUPED_PAGE = 40
 
    # These strings appear in the Flamenco interface.
    PAGE_TITLE = 'Generic Collection'
    PAGE_HEADING = 'Main Heading'
    PAGE_SUBHEADING = 'Subheading'
    
    ITEM_NOUN = 'item'
    ITEM_NOUN_PLURAL = 'items'
    GROUP_NOUN = 'group'
    GROUP_NOUN_PLURAL = 'groups'

    RECENTLY_VIEWED_ITEMS = 'Recently Viewed Items'
    SAVED_ITEMS_AND_GROUPS = 'Saved Items and Groups'

    NEW_SEARCH = 'start a new search'

    MIDDLEGAME_TOO_MANY_ITEMS = '''
        The current query selects %(items)s in %(groups)s,
        which could be too many to show at once.
        If you are sure you want to see them all, you can %(link)s,
        'or select a more specific subcategory of "%(category)s" below.'''
    MIDDLEGAME_TOO_MANY_ITEMS_LINK = 'proceed to see the entire category'
    MIDDLEGAME_REFINE = 'Refine your search within these categories:'
    MIDDLEGAME_TERMS = 'These terms define your current search. '
    MIDDLEGAME_REMOVE = 'Click the %(button)s to remove a term.'
    MIDDLEGAME_GROUPBY_TOOLTIP = \
        'arrange results in groups according to subcategories in '
    MIDDLEGAME_GROUPBY = '(group results)'
    MIDDLEGAME_GROUPED_BY = ' (grouped by %s)'
    MIDDLEGAME_VIEW_UNGROUPED = 'view ungrouped items'
    MIDDLEGAME_UNGROUPED_SORTED = ' (ungrouped, sorted by %s)'
    MIDDLEGAME_SORT = 'sort by: '
    MIDDLEGAME_UNGROUPED = ' (ungrouped)'
    MORE = 'more'
    NUM_MATCHES = ' (%d matches)...'
    MATCH_CATEGORIES = '"%s" appears in these category names:'
    HISTORY_EMPTY = '(empty)'
    HISTORY_ITEM_HISTORY = 'Item History'
    HISTORY_SAVED_ITEMS = 'Saved Items'
    HISTORY_USER_HISTORY = 'User History'
    HISTORY_MOST_RECENT = '(most recent displayed first)'
    HISTORY_CREATE_GROUP = 'Create New Group'
    HELP_RETURN_MY_FLAMENCO = 'Click here to return to My Flamenco'
    HELP_HISTORY_DESCRIPT = 'This section of the Flamenco interface allows you to browse your saved ', ITEM_NOUN_PLURAL,' and searches. Also, since a log is kept of all viewed items, you may view these as well. The different sections are described in greater detail below.'
    HELP_GROUP_NAME = 'Group Name'
    HELP_SAVE_DESCRIPT = 'The ', HISTORY_SAVED_ITEMS, ' section allows you to save ' + ITEM_NOUN_PLURAL, ' for later access. Groups are provided as storage containers to help provide organization. These groups can be created either from My Flamenco or when you save an item. Use the buttons to manage your saved ', ITEM_NOUN_PLURAL, '. ', ITEM_NOUN_PLURAL.capitalize(), ' can also be moved into groups from your ', ITEM_NOUN, ' history repository, which is displayed to the right, with orange background.'
    HISTORY_SEARCH_SAVED = 'Saved Searches'
    HISTORY_SEARCH_NAME = 'Search name'
    HELP_SEARCH_DESCRIPT = 'The Saved Searches section allows you to save searches for later access. When a search is saved, you will be prompted for a name. The default name is simply the list of terms associated with your search. When viewing your saved searches three sample ', ITEM_NOUN_PLURAL, ' are shown for each search. To perform the search again, simply click on the search name.'
    HISTORY = 'History'
    HISTORY_DATE_VIEWED = 'Date Viewed'
    HELP_HISTORY = 'The ', HISTORY_ITEM_HISTORY, ' section keeps a log of all ', ITEM_NOUN_PLURAL, ' you have viewed in the past, grouped by date viewed.'
    HELP_HEADER = 'This section of the Flamenco interface allows you to browse your saved ', ITEM_NOUN_PLURAL, ' and searches. Also, since a log is kept of all viewed ', ITEM_NOUN_PLURAL, ', you may view these as well. For an explanation of how to fully utilize these features, click '
    HISTORY_VIEWBAR_VIEW = 'View: '
    HISTORY_SEARCH_DELETE = 'Delete Saved Search'
    HISTORY_SEARCH_RENAME = 'Rename Saved Search'
    HISTORY_SEARCH_RUN = 'Run This Search'
    HISTORY_SEARCH_TERMS = 'Search Terms:'
    HISTORY_SAMPLE = 'Sample '
    HISTORY_SEARCH_SAMPLE = 'Three sample items are shown for each search. If a search yielded less than 3 results, then those results are shown.'
    HISTORY_GROUPS_CURRENT = 'Current Groups:'
    HISTORY_RENAME_GROUPS = 'Renaming Group'
    HISTORY_GROUPS_OLD = 'Old Group Name:'
    HISTORY_GROUPS_NEW = 'New Group Name:'
    HISTORY_SEARCHES_CURRENT = 'Current Searches:'
    HISTORY_SEARCH_RENAMING = 'Renaming Search'
    HISTORY_SEARCH_OLD = 'Old Search Name:'
    HISTORY_SEARCH_NEW = 'New Search Name:'
    HISTORY_SAVE_GROUP_SELECT = '''
        Select a group in which to save this item.
        To create a new group, select the last bubble and
        enter the name for the new group.'''
    HISTORY_SEARCH_SAVE_PROMPT = 'Flamenco will save this search as '
    MIDDLEGAME_REFINE_SEARCH = 'Refine search with terms describing this item:'
    MIDDLEGAME_SEE_ALL = 'See all items in related categories:'
    ENDGAME_MORE_GENERAL = 'more general categories'
    ENDGAME_ITEM_INFO = 'information about this item'
    ENDGAME_LINK_RELATED = 'Select any link to see items in a related category.'
    ENDGAME_CURRENT_SEARCH = 'Current search:'

    HISTORY_FAVORITE_ITEM_LIMIT = 15

    # Picture files for the toolbar.
    PIC_URL_BASE = 'http://flamenco.sims.berkeley.edu/pics/'
    SAVE_IMAGE_SRC = PIC_URL_BASE + 'saveimage.gif'
    SAVE_SEARCH_SRC = PIC_URL_BASE + 'savesearch.gif'
    SAVE_GREY_SRC = PIC_URL_BASE + 'save_grey.gif'
    MANAGE_GAME_SRC = PIC_URL_BASE + 'history_settings.gif'
    MANAGE_GAME_GREY_SRC = PIC_URL_BASE + 'history_settings_grey.gif'
    NEW_SEARCH_SRC =  PIC_URL_BASE + 'newsearch.gif'
    RETURN_SEARCH_SRC = PIC_URL_BASE + 'returntosearch.gif'
    RETURN_SEARCH_GREY_SRC = PIC_URL_BASE + 'returntosearch_grey.gif'
    LOGOUT_SRC = PIC_URL_BASE + 'logout.gif'
    LOGOUT_GREY_SRC = PIC_URL_BASE + 'logout_grey.gif'

    SAVE_IMAGE_ALT = 'Save Image'
    SAVE_SEARCH_ALT = 'Save Search'
    MANAGE_GAME_ALT = 'My Flamenco'
    NEW_SEARCH_ALT = 'New Search'
    RETURN_SEARCH_ALT = 'Return to Search'
    LOGOUT_ALT = 'Logout'
    GREY_ALT = 'Not accessible from this page'

    # Picture files for previewing the interface.
    PREVIEW_OPENING1_SRC = PIC_URL_BASE + 'preview_opening1.gif'
    PREVIEW_OPENING2_SRC = PIC_URL_BASE + 'preview_opening2.gif'
    PREVIEW_OPENING3_SRC = PIC_URL_BASE + 'preview_opening3.gif'
    PREVIEW_MIDDLE1_SRC = PIC_URL_BASE + 'preview_middle1.gif'
    PREVIEW_MIDDLE2_SRC = PIC_URL_BASE + 'preview_middle2.gif'
    PREVIEW_MIDDLE3_SRC = PIC_URL_BASE + 'preview_middle3.gif'
    PREVIEW_END1_SRC = PIC_URL_BASE + 'preview_end1.gif'
    PREVIEW_END2_SRC = PIC_URL_BASE + 'preview_end2.gif'
    PREVIEW_END3_SRC = PIC_URL_BASE + 'preview_end3.gif'
    
    # Other picture files.
    SAVE_SMALL_SRC = PIC_URL_BASE + 'save_small.gif'
    CANCEL_SMALL_SRC = PIC_URL_BASE + 'cancel_small.gif'
    LEFT_ARROW_SRC = PIC_URL_BASE + 'leftarrow.gif'
    RIGHT_ARROW_SRC = PIC_URL_BASE + 'rightarrow.gif'
    X_SRC = PIC_URL_BASE + 'x.gif'
    RENAME_GROUP_SRC = PIC_URL_BASE + 'renamegroup6.gif'
    COPY_HERE_SRC = PIC_URL_BASE + 'copyhere6.gif'
    DELETE_SELECTED_SRC = PIC_URL_BASE + 'deleteselected6.gif'
    DELETE_GROUP_SRC = PIC_URL_BASE + 'deletegroup6.gif'

    DELETE_SEARCH_SRC = PIC_URL_BASE + 'deletesavedsearch.gif'
    RENAME_SEARCH_SRC = PIC_URL_BASE + 'renamesavedsearch.gif'

    CREATE_SRC = PIC_URL_BASE + 'login.gif'
    LOGIN_SRC = PIC_URL_BASE + 'login.gif'
    SUBMIT_SRC = PIC_URL_BASE + 'submit.gif'
    CANCEL_SRC = PIC_URL_BASE + 'cancel.gif'
    ARROW_UP_SRC = PIC_URL_BASE + 'uparrow.gif'
    ARROW_DOWN_SRC = PIC_URL_BASE + 'downarrow.gif'

    LEFT_ARROW_ALT = "Previous"
    RIGHT_ARROW_ALT = "Next"
    X_ALT = "click to remove"

    def __init__(self, db):
        self.db = db
        self.facetlist = db.facetlist
        self.attrlist = db.attrlist

    def queryinfo_terms(self, facet, ids):
        return [(self.db.name(facet, id), (facet, id, 0)) for id in ids]

    def itemdisplay(self, item, request, **attrs):
        return 'Item %s' % item

    def itemlisting(self, item, index=None, link=None, history=None,
                    mini=0, imageonly=0, **args):
        if history:
            listing = link('Item %s' % item, item=item, **args)
        else:
            listing = link('Item %s' % item, index=index, **args)
        return center(listing)
