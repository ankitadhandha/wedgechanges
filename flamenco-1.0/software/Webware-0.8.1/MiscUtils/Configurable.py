import string, sys, os
from types import DictType
from MiscUtils import AbstractError, NoDefault
from WebKit.ImportSpy import modloader
from Funcs import valueForString



class ConfigurationError(Exception):
	pass


class Configurable:
	"""
	Configurable is an abstract superclass that provides configuration
	file functionality for subclasses.

	Subclasses should override:

		* defaultConfig()  to return a dictionary of default settings
		                   such as { 'Frequency': 5 }

		* configFilename() to return the filename by which users can
		                   override the configuration such as
		                   'Pinger.config'


	Subclasses typically use the setting() method, for example:

		time.sleep(self.setting('Frequency'))


	They might also use the printConfig() method, for example:

		self.printConfig()      # or
		self.printConfig(file)


	Users of your software can create a file with the same name as
	configFilename() and selectively override settings. The format of
	the file is a Python dictionary.

	Subclasses can also override userConfig() in order to obtain the
	user configuration settings from another source.
	"""

	## Init ##

	def __init__(self):
		self._config = None


	## Configuration

	def config(self):
		""" Returns the configuration of the object as a dictionary. This is a combination of defaultConfig() and userConfig(). This method caches the config. """
		if self._config is None:
			self._config = self.defaultConfig()
			self._config.update(self.userConfig())
			self._config.update(self.commandLineConfig())
		return self._config

	def setting(self, name, default=NoDefault):
		""" Returns the value of a particular setting in the configuration. """
		if default is NoDefault:
			return self.config()[name]
		else:
			return self.config().get(name, default)

	def hasSetting(self, name):
		return self.config().has_key(name)

	def defaultConfig(self):
		""" Returns a dictionary containing all the default values for the settings. This implementation returns {}. Subclasses should override. """
		return {}

	def configFilename(self):
		""" Returns the filename by which users can override the configuration. Subclasses must override to specify a name. Returning None is valid, in which case no user config file will be loaded. """
		raise AbstractError, self.__class__

	def configName(self):
		"""
		Returns the name of the configuration file (the portion
		before the '.config').  This is used on the command-line.
		"""
		return os.path.splitext(os.path.basename(self.configFilename()))[0]

	def configReplacementValues(self):
		"""
		Returns a dictionary suitable for use with "string % dict"
		that should be used on the text in the config file.  If an
		empty dictionary (or None) is returned then no substitution
		will be attempted.
		"""
		return {}

	def userConfig(self):
		""" Returns the user config overrides found in the optional config file, or {} if there is no such file. The config filename is taken from configFilename(). """
		try:
			filename = self.configFilename()
			if filename is None:
				return {}
			file = open(filename)
		except IOError:
			return {}
		else:
			contents = file.read()
			file.close()
			modloader.watchFile(filename)
			replacements = self.configReplacementValues()
			if replacements:
				try:
					contents = contents % replacements
				except:
					raise ConfigurationError, 'Unable to embed replacement text in %s.' % self.configFilename()

			try:
				config = eval(contents, {})
			except:
				raise ConfigurationError, 'Invalid configuration file, %s.' % self.configFilename()
			if type(config) is not DictType:
				raise ConfigurationError, 'Invalid type of configuration. Expecting dictionary, but got %s.'  % type(config)
			return config

	def printConfig(self, dest=None):
		""" Prints the configuration to the given destination, which defaults to stdout. A fixed with font is assumed for aligning the values to start at the same column. """
		if dest is None:
			dest = sys.stdout
		keys = self.config().keys()
		keys.sort()
		width = max(map(lambda key: len(key), keys))
		for key in keys:
			dest.write(string.ljust(key, width)+' = '+str(self.setting(key))+'\n')
		dest.write('\n')

	def commandLineConfig(self):
		"""
		Settings that came from the command line (via
		addCommandLineSetting).
		"""
		return _settings.get(self.configName(), {})

_settings = {}
def addCommandLineSetting(name, value):
	"""
	Take a setting, like --AppServer.Verbose=0, and call
	addCommandLineSetting('AppServer.Verbose', '0'), and
	it will override any settings in AppServer.config
	"""
	configName, settingName = string.split(name, '.', 1)
	value = valueForString(value)
	if not _settings.has_key(configName):
		_settings[configName] = {}
	_settings[configName][settingName] = value

def commandLineSetting(configName, settingName, default=NoDefault):
	"""
	Retrieve a command-line setting.  You can use this with
	non-existent classes, like --Context.Root=/WK, and then
	fetch it back with commandLineSetting('Context', 'Root').
	"""
	if default is NoDefault:
		return _settings[configName][settingName]
	else:
		return _settings.get(configName, {}).get(settingName, default)

