def test(store):
	from Foo import Foo

	f = store.fetchObjectsOfClass(Foo)[0]

	d  = '2000-01-01'
	t  = '13:01'
	dt = '2000-01-01 13:01'
	try:
		try:
			from mx.DateTime import DateTimeFrom, DateTimeDeltaFrom
		except ImportError:
			from DateTime import DateTimeFrom, DateTimeDeltaFrom
		print 'Testing with DateTime module.'
		d  = DateTimeFrom(d)
		t  = DateTimeDeltaFrom(t)
		dt = DateTimeFrom(dt)
	except ImportError:
		print 'Testing with strings.'
	assert f.d()==d, 'f.d()=%s, d=%s' % (f.d(), d)
	assert f.t()==t, 'f.t()=%s, t=%s' % (f.t(), t)
	assert f.dt()==dt, 'f.dt()=%s, dt=%s' % (f.dt(), dt)
