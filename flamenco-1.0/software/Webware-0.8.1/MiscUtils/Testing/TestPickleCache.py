"""
def readPickleCache(filename, pickleVersion=1, source=None, verbose=None):
	PickleCacheReader().read(filename, pickleVersion, source, verbose)

def writePickleCache(data, filename, pickleVersion=1, source=None, verbose=None):
	PickleCacheWriter().write(data, filename, pickleVersion, source, verbose)
"""

from FixPath import progDir
from os.path import join
from PickleCache import *


class TestPickleCache:

	def run(self, iters=1):
		sys.setcheckinterval(10000)  # keep the code sequence tight for the 'source is newer' test
		print 'Testing PickleCache...'
		for iter in range(iters):
			self.test()
		print 'Success.'

	def test(self):
		sourcePath = self.sourcePath = join(progDir, 'foo.dict')
		picklePath = self.picklePath = PickleCache().picklePath(sourcePath)
		self.remove(picklePath) # make sure we're clean

		data = self.data = {'x': 1}
		self.writeSource()
		try:
			# no pickle cache yet
			assert readPickleCache(sourcePath) is None
			self.writePickle()

			# correct
			assert readPickleCache(sourcePath)==data, repr(readPickleCache(sourcePath))

			# wrong pickle version
			assert readPickleCache(sourcePath, pickleVersion=2)==None
			self.writePickle()  # restore

			# wrong data source
			assert readPickleCache(sourcePath, source='notTest')==None
			self.writePickle()  # restore

			# wrong python version
			try:
				saveVersion = sys.version_info
				sys.version_info = (sys.version_info[0]+1,) + sys.version_info[1:]
				assert readPickleCache(sourcePath)==None
				self.writePickle()  # restore
			finally:
				sys.version_info = saveVersion

			# source is newer
			self.remove(picklePath)
			self.writePickle()
			import time; time.sleep(1)  # I think it's creepy that on Linux we have to sleep 1 in order for one file to looker newer than the other...
			self.writeSource()
			assert readPickleCache(sourcePath)==None
			self.writePickle()  # restore
		finally:
			self.remove(sourcePath)
			self.remove(picklePath)

	def remove(self, filename):
		try:
			os.remove(filename)
		except OSError:
			pass

	def writeSource(self):
		open(self.sourcePath, 'w').write(str(self.data))

	def writePickle(self):
		assert not os.path.exists(self.picklePath)
		writePickleCache(self.data, self.sourcePath, pickleVersion=1, source='test')
		assert os.path.exists(self.picklePath)


if __name__=='__main__':
	TestPickleCache().run(iters=3)
