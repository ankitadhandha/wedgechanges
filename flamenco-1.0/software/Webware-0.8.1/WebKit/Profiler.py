"""
Stores some values related to performance. These are usually set by
Launch.py or AppServer.py.

To get profiling going, locate the "runProfile = 0" line towards the
top of WebKit/Launch.py and change the "0" to a "1". When the app
server shuts down it will write Webware/profile.pstats which can be
quickly examined from the command line:

	$ cd Webware
	$ bin/printprof.py profile.pstats

You might also wish to dump the profiling stats on demand (as in, by
clicking or reloading a URL for that purpose). Read further for
details.


The variables in this module are:

profiler
	An instance of Python's profile.Profiler, but only if Launch.py is
	modified to say "runProfile = 1". Otherwise, this is None. You
	could access this from a servlet in order to dump stats:

		from WebKit.Profiler import profiler
		profiler.dump_stats('profile.pstats')

	Or more conveniently:
		from WebKit.Profiler import dumpStats
		dumpStats()

	With some work, you could dump them directly to the page in a
	readable format.

startTime
	The earliest recordable time() when the app server program was
	launched.

readyTime
readyDuration
	The time() and duration from startTime for when the app server
	was ready to start accepting requests. A smaller readyDuration
	makes application reloading faster which is useful when
	developing with AutoReload on.
"""

profiler      = None
startTime     = None
readyTime     = None
readyDuration = None


# Convenience

statsFilename = 'profile.pstats'

def dumpStats():
	profiler.dump_stats(statsFilename)
