# COMKit
#
# This plug-in for WebKit for Python allows COM objects such as ADO to be
# used in free-threading mode in a threaded app server.  See Appendix D of
# the fine book Python Programming on Win32 by Mark Hammond and Andy
# Robinson for details.
#
# To use COM, simply set EnableCOM to 1 in your AppServer.config file.
# This causes the app server threads to be configured properly for
# COM free-threading.  Then go ahead and use win32com inside your servlets.

__all__ = []


# This function gets called by the app server during initialization
def InstallInWebKit(appServer):
	# See if enabling COM was requested
	if appServer.setting('EnableCOM', 0):

		# This must be done BEFORE pythoncom is imported -- see the book mentioned above.
		import sys
		sys.coinit_flags = 0

		# See if the win32 extensions are available
		import pythoncom
		# Create a base class for a COM-enabled app server.
		class COMEnabledAppServer:
			def initThread(self):
				# This must be called at the beginning of any thread that uses COM
				import pythoncom
				pythoncom.CoInitializeEx(pythoncom.COINIT_MULTITHREADED)
				
				# Invoke superclass's initThread.  This enables multiple plug-ins
				# to each have their own initThread get called.
				self.__class__.__bases__[0].initThread(self)

			def delThread(self):
				# Invoke superclass's delThread.  This enables multiple plug-ins
				# to each have their own delThread get called.
				self.__class__.__bases__[0].delThread(self)

				# This must be called at the end of any thread that uses COM
				import pythoncom
				pythoncom.CoUninitialize()

		# We mix-in the COMEnabledAppServer, but it's a reverse mix-in:

		# Make COMEnabledAppServer inherit the current app server's class
		COMEnabledAppServer.__bases__ = (appServer.__class__,)

		# Make the current app server point to COMEnabledAppServer
		appServer.__class__ = COMEnabledAppServer

		print 'COM has been enabled.'

		# Note: Python makes "plugging in" possible.
