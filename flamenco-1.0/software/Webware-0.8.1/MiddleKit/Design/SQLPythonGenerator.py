from PythonGenerator import PythonGenerator
from PythonGenerator import Klass as SuperKlass


class SQLPythonGenerator(PythonGenerator):
	pass


class Klass:

	def writePyImports(self):
		SuperKlass.writePyImports.im_func(self) # invoke our super generator's method
		# @@ 2000-11-22 ce: the above is pretty hacky, invoking super is the only awkward aspect of mix-ins that hasn't been solved
		self._pyOut.write('from types import InstanceType, LongType\n')
		self._pyOut.write('from MiddleKit.Run.SQLObjectStore import ObjRefError\n\n')


class ObjRefAttr:

	def writePyGet(self, out):
		name = self.name()
		pyGetName = self.pyGetName()
		klassName = self.klass().name()
		out.write('''
	def %(pyGetName)s(self):
		if self._%(name)s is not None and type(self._%(name)s) is not InstanceType:
			try:
				self.__dict__['_%(name)s'] = self._mk_store.fetchObjRef(self._%(name)s)
			except ObjRefError, e:
				self.__dict__['_%(name)s'] = self.objRefErrorWasRaised(e, %(klassName)r, %(name)r)
		return self._%(name)s
''' % locals())


class ListAttr:

	def writePyGet(self, out, names):
		out.write('''
	def %(pyGetName)s(self):
		if self._%(name)s is None:
			from %(package)s%(targetClassName)s import %(targetClassName)s
			self._%(name)s = self._mk_store.fetchObjectsOfClass(%(targetClassName)s, clauses='where %(lowerSourceClassName)sId=%%i' %% self.sqlObjRef())
		return self._%(name)s
''' % names)
