'''
This module is used when the IPython kernel is embedded, to contain all the
code and variables you run.  This is transparent from a user perspective.

You shouldn't really need to know much about it, but it exists so that you don't
accidentally break the SDK by removing all the code it loads in __main__, and
things like that.

NOTE: the IPython `%reset` magic will delete anything loaded in here, so it
doesn't help to import things for future convenience: they won't persist.
'''
