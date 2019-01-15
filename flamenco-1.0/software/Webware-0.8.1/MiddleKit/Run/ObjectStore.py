import sys
from types import ClassType, StringType
from MiscUtils import NoDefault
from ObjectKey import ObjectKey
from MiddleKit.Core.ModelUser import ModelUser
from MiddleKit.Core.Klass import Klass as BaseKlass
from MiddleKit.Core.ObjRefAttr import ObjRefAttr
from MiddleKit.Core.ListAttr import ListAttr
	# ^^^ for use in _klassForClass() below
	# Can't import as Klass or Core.ModelUser (our superclass)
	# will try to mix it in.
from PerThreadList import PerThreadList, NonThreadedList
from PerThreadDict import PerThreadDict, NonThreadedDict
import thread


class UnknownObjectError(LookupError):
	""" This is the exception returned by store.fetchObject() if the specified object cannot be found (unless you also passed in a default value in which case that value is returned). """
	pass

class DeleteError(Exception):
	""" Base class for all delete exceptions """
	pass

class DeleteReferencedError(DeleteError):
	"""
	This is raised when you attempt to delete an object that is referenced by other objects with
	onDeleteOther not set to detach or cascade.  You can call referencingObjectsAndAttrs() to get a
	list of tuples of (object, attr) for the particular attributes that caused the error.
	And you can call object() to get the object that was trying to be deleted.
	This might not be the same as the object originally being deleted if a cascading
	delete was happening.
	"""
	def __init__(self, text, object, referencingObjectsAndAttrs):
		Exception.__init__(self, text)
		self._object = object
		self._referencingObjectsAndAttrs = referencingObjectsAndAttrs
	def object(self):
		return self._object
	def referencingObjects(self):
		return self._referencingObjectsAndAttrs

class DeleteObjectWithReferencesError(DeleteError):
	"""
	This is raised when you attempt to delete an object that references other objects,
	with onDeleteSelf=deny.  You can call attrs() to get a list of attributes
	that reference other objects with onDeleteSelf=deny.  And you can call object() to
	get the object trying to be deleted that contains those attrs.
	This might not be the same as the object originally being deleted if a cascading
	delete was happening.
	"""
	def __init__(self, text, object, attrs):
		Exception.__init__(self, text)
		self._object = object
		self._attrs = attrs
	def object(self):
		return self._object
	def attrs(self):
		return self._attrs

class ObjectStore(ModelUser):
	"""
	NOT IMPLEMENTED:
		* revertChanges()

	FUTURE
		* expanded fetch
	"""


	## Init ##

	def __init__(self):
		self._model          = None
		self._objects        = {} # keyed by ObjectKeys
		self._newSerialNum   = -1
		self._verboseDelete  =  0


	def modelWasSet(self):
		"""
		Performs additional set up of the store after the model is set.
		"""
		ModelUser.modelWasSet(self)
		self._threaded = self.setting('Threaded')
		if self._threaded:
			self._hasChanges     = {} # keep track on a per-thread basis
			self._newObjects	 = PerThreadList()
			self._deletedObjects = PerThreadList()
			self._changedObjects = PerThreadDict()
		else:
			self._hasChanges     = 0
			self._newObjects     = NonThreadedList()
			self._deletedObjects = NonThreadedList()
			self._changedObjects = NonThreadedDict()

	## Settings ##

	def setting(self, name, default=NoDefault):
		"""
		Returns the given setting for the store, which is actually
		just taken from the model.
		"""
		return self._model.setting(name, default)


	## Manipulating the objects in the store ##

	def hasObject(self, object):
		""" Checks if the object is in the store.  Note: this does not check the persistent store. """
		key = object.key()
		if key is None:
			return 0
		else:
			return self._objects.has_key(key)

	def object(self, key, default=NoDefault):
		""" Returns an object from the store by it's given key. If no default is given and the object is not in the store, then an exception is raised. Note: This method doesn't currently fetch objects from the persistent store. """
		if default is NoDefault:
			return self._objects[key]
		else:
			return self._objects.get(key, default)

	def addObject(self, object, noRecurse=0):
		"""
		Add the object and all referenced objects to the store.
		You can insert the same object multiple times, and you can insert an object that was
		loaded from the store.  In those cases, this is a no-op.
		The noRecurse flag is used internally, and should be avoided in regular
		MiddleKit usage; it causes only this object to be added to the store,
		not any dependent objects.
		"""
		if not object.isInStore():
			assert object.key()==None
			# Make the store aware of this new object
			self.willChange()
			self._newObjects.append(object)
			object.setStore(self)
			if not noRecurse:
				# Recursively add referenced objects to the store
				object.addReferencedObjectsToStore(self)

			# 2000-10-07 ce: Decided not to allow keys for non-persisted objects
			# Because the serial num, and therefore the key, will change
			# upon saving.
			#key = object.key()
			#if key is None:
			#	key = ObjectKey(object, self)
			#	object.setKey(key)
			#self._objects[key] = object

	def deleteObject(self, object):
		"""
		Restrictions: The object must be contained in the store and obviously
		you cannot remove it more than once.
		"""
		# First check if the delete is possible.  Then do the actual delete.  This avoids partially deleting
		# objects only to have an exception halt the process in the middle.

		objectsToDel = {}
		detaches = []
		self._deleteObject(object, objectsToDel, detaches)  # compute objectsToDel and detaches
		self.willChange()

		# detaches
		for obj, attr in detaches:
			if not objectsToDel.has_key(id(obj)):
				obj.setValueForAttr(attr, None)

		# deleted objects
		objectsToDel = objectsToDel.values()
		self._deletedObjects.extend(objectsToDel)

		# remove deleted objects from main list of objects
		for obj in objectsToDel:
			del self._objects[obj.key()]

	def _deleteObject(self, object, objectsToDel, detaches, superobject=None):
		"""
		Compile the list of objects to be deleted. This is a recursive
		method since deleting one object might be deleting others.

		object       - the object to delete
		objectsToDel - a running dictionary of all objects to delete
		detaches     - a running list of all detaches (eg, obj.attr=None)
		superobject  - the object that was the cause of this invocation
		"""
		# Some basic assertions
		assert self.hasObject(object)
		assert object.key() is not None

		v = self._verboseDelete

		if v:
			if superobject:
				cascadeString = 'cascade-'
				dueTo = ' due to deletion of %s.%i' % (superobject.klass().name(), superobject.serialNum())
			else:
				cascadeString = dueTo = ''
			print 'checking %sdelete of %s.%d%s' % (cascadeString, object.klass().name(), object.serialNum(), dueTo)

		objectsToDel[id(object)] = object

		# Deal with all other objects that reference or are referenced by this object.  By default, you are not allowed
		# to delete an object that has an ObjRef pointing to it.  But if the ObjRef has
		# onDeleteOther=detach, then that ObjRef attr will be set to None and the delete will be allowed;
		# and if onDeleteOther=cascade, then that object will itself be deleted and the delete
		# will be allowed.
		#
		# You _are_ by default allowed to delete an object that points to other objects (by List or ObjRef)
		# but if onDeleteSelf=deny it will be disallowed, or if onDeleteSelf=cascade the pointed-to
		# objects will themselves be deleted.

		# Get the objects/attrs that reference this object
		referencingObjectsAndAttrs = object.referencingObjectsAndAttrs()
		# Remove from that list anything in the cascaded list
		referencingObjectsAndAttrs = [(o,a) for o,a in referencingObjectsAndAttrs if not objectsToDel.has_key(id(o))]

		# Determine all referenced objects, constructing a list of (attr, referencedObject) tuples.
		referencedAttrsAndObjects = []
		for attr in object.klass().allDataAttrs():
			if isinstance(attr, ObjRefAttr):
				obj = object.valueForAttr(attr)
				if obj:
					referencedAttrsAndObjects.append((attr, obj))
			elif isinstance(attr, ListAttr):
				for obj in object.valueForAttr(attr):
					referencedAttrsAndObjects.append((attr, obj))
		# Remove from that list anything in the cascaded list
		referencedAttrsAndObjects = [(a,o) for a,o in referencedAttrsAndObjects if not objectsToDel.has_key(id(o))]

		# Check for onDeleteOther=deny
		badObjectsAndAttrs = []
		for referencingObject, referencingAttr in referencingObjectsAndAttrs:
			onDeleteOther = referencingAttr.get('onDeleteOther', 'deny')
			assert onDeleteOther in ('deny', 'detach', 'cascade')
			if onDeleteOther == 'deny':
				badObjectsAndAttrs.append((referencingObject, referencingAttr))
		if badObjectsAndAttrs:
			raise DeleteReferencedError(
				'You tried to delete an object (%s.%d) that is referenced by other objects with onDeleteOther unspecified or set to deny'
				% (object.klass().name(), object.serialNum()),
				object,
				badObjectsAndAttrs)

		# Check for onDeleteSelf=deny
		badAttrs = []
		for referencedAttr, referencedObject in referencedAttrsAndObjects:
			onDeleteSelf = referencedAttr.get('onDeleteSelf', 'detach')
			assert onDeleteSelf in ['deny', 'detach', 'cascade']
			if onDeleteSelf == 'deny':
				badAttrs.append(referencedAttr)
		if badAttrs:
			raise DeleteObjectWithReferencesError(
				'You tried to delete an object (%s.%d) that references other objects with onDeleteSelf set to deny'
				% (object.klass().name(), object.serialNum()),
				object,
				badAttrs)

		# cascade-delete objects with onDeleteOther=cascade
		for referencingObject, referencingAttr in referencingObjectsAndAttrs:
			onDeleteOther = referencingAttr.get('onDeleteOther', 'deny')
			if onDeleteOther == 'cascade':
				self._deleteObject(referencingObject, objectsToDel, detaches, object)

		# Check if it's possible to cascade-delete objects with onDeleteSelf=cascade
		for referencedAttr, referencedObject in referencedAttrsAndObjects:
			onDeleteSelf = referencedAttr.get('onDeleteSelf', 'detach')
			if onDeleteSelf == 'cascade':
				self._deleteObject(referencedObject, objectsToDel, detaches, object)

		# Detach objects with onDeleteOther=detach
		for referencingObject, referencingAttr in referencingObjectsAndAttrs:
			onDeleteOther = referencingAttr.get('onDeleteOther', 'deny')
			if onDeleteOther == 'detach':
				if v: print 'will set %s.%d.%s to None' % (referencingObject.klass().name(), referencingObject.serialNum(), referencingAttr.name())
				detaches.append((referencingObject, referencingAttr))

		# Detach objects with onDeleteSelf=detach
		# This is actually a no-op.  There is nothing that needs to be set to zero.


	## Changes ##

	def hasChangesForCurrentThread(self):
		''' return whether the current thread has changes to be committed '''
		if self._threaded:
			threadid = thread.get_ident()
			return self._hasChanges.get(threadid,0)
		else:
			return self._hasChanges

	def hasChanges(self):
		''' return whether any thread has changes to be committed '''
		if self._threaded:
			return 1 in self._hasChanges.values()
		return self._hasChanges

	def willChange(self):
		if self._threaded:
			threadid = thread.get_ident()
			self._hasChanges[threadid] = 1
		else:
			self._hasChanges = 1

	def saveAllChanges(self):
		""" Commits object changes to the object store by invoking commitInserts(), commitUpdates() and commitDeletions() all of which must by implemented by a concrete subclass. """
		self.commitDeletions(allThreads=1)
		self.commitInserts(allThreads=1)
		self.commitUpdates(allThreads=1)
		self._hasChanges = {}

	def saveChanges(self):
		""" Commits object changes to the object store by invoking commitInserts(), commitUpdates() and commitDeletions() all of which must by implemented by a concrete subclass. """
		self.commitDeletions()
		self.commitInserts()
		self.commitUpdates()
		if self._threaded:
			self._hasChanges[thread.get_ident()] = 0
		else:
			self._hasChanges = 0

	def commitInserts(self):
		""" Invoked by saveChanges() to insert any news objects add since the last save. Subclass responsibility. """
		raise AbstractError, self.__class__

	def commitUpdates(self):
		""" Invoked by saveChanges() to update the persistent store with any changes since the last save. """
		raise AbstractError, self.__class__

	def commitDeletions(self):
		""" Invoked by saveChanges() to delete from the persistent store any objects deleted since the last save. Subclass responsibility. """
		raise AbstractError, self.__class__

	def revertChanges(self):
		""" Discards all insertions and deletions, and restores changed objects to their original values. """
		raise NotImplementedError


	## Fetching ##

	def fetchObject(self, className, serialNum, default=NoDefault):
		""" Subclasses should raise UnknownObjectError if an object with the given className and serialNum does not exist, unless a default value was passed in, in which case that value should be returned. """
		raise AbstractError, self.__class__

	def fetchObjectsOfClass(self, className, isDeep=1):
		""" Fetches all objects of a given class. If isDeep is 1, then all subclasses are also returned. """
		raise AbstractError, self.__class__


	## Other ##

	def clear(self):
		"""
		Clears all objects from the memory of the store. This does not
		delete the objects in the persistent backing. This method can
		only be invoked if there are no outstanding changes to be
		saved. You can check for that with hasChanges().
		"""
		assert not self.hasChanges()
		assert self._newObjects.isEmpty()
		assert self._deletedObjects.isEmpty()
		assert self._changedObjects.isEmpty()

		self._objects        = {}
		self._newSerialNum   = -1

	def discardEverything(self):
		"""
		Discards all cached objects, including any modification
		tracking. However, objects in memory will not change state as
		a result of this call.

		This method is a severe form of clear() and is typically used
		only for debugging or production emergencies.
		"""
		if self._threaded:
			self._hasChanges     = {}
		else:
			self._hasChanges     = 0
		self._objects        = {}
		self._newObjects.clear()
		self._deletedObjects.clear()
		self._changedObjects.clear()
		self._newSerialNum   = -1


	## Notifications ##

	def objectChanged(self, object):
		"""
		MiddleObjects must send this message when one of their interesting attributes change, where an attribute is interesting if it's listed in the class model.
		This method records the object in a set for later processing when the store's changes are saved.
		If you subclass MiddleObject, then you're taken care of.
		"""
		self.willChange()
		self._changedObjects[object] = object  ## @@ 2000-10-06 ce: Should this be keyed by the object.key()? Does it matter?


	## Serial numbers ##

	def newSerialNum(self):
		""" Returns a new serial number for a newly created object. This is a utility methods for objects that have been created, but not yet committed to the persistent store. These serial numbers are actually temporary and replaced upon committal. Also, they are always negative to indicate that they are temporary, whereas serial numbers taken from the persistent store are positive. """
		self._newSerialNum -= 1
		return self._newSerialNum


	## Self utility ##

	def _klassForClass(self, aClass):
		""" Returns a Klass object for the given class, which may be:
			- the Klass object already
			- a Python class
			- a class name (e.g., string)
		Users of this method include the various fetchObjectEtc() methods which take a "class" parameter.
		"""
		assert aClass is not None
		if not isinstance(aClass, BaseKlass):
			if type(aClass) is ClassType:
				aClass = self._model.klass(aClass.__name__)
			elif type(aClass) is StringType:
				aClass = self._model.klass(aClass)
			else:
				raise ValueError, 'Invalid class parameter. Pass a Klass, a name or a Python class. Type of aClass is %s. aClass is %s.' % (type(aClass), aClass)
		return aClass


class Attr:

	def shouldRegisterChanges(self):
		""" MiddleObject asks attributes if changes should be registered. By default, all attributes respond true, but specific stores may choose to override this (a good example being ListAttr for SQLStore). """
		return 1
