# -*- coding: utf-8 -*-
#
# Copyright © 2014 Geoffrey T. Dairiki <dairiki@dairiki.org>
#
from __future__ import absolute_import

import logging

from pyramid.request import Request
from pyramid import testing
import pytest

@pytest.fixture
def current_request(request):
    r = Request.blank('/')
    config = testing.setUp(request=r)
    request.addfinalizer(testing.tearDown)
    return r

@pytest.fixture
def log_record():
    return logging.LogRecord('test', logging.INFO, __file__, 0, '', (), None)

class MockObject(object):
    def __init__(self, **kw):
        self.__dict__.update(kw)

class TestFormatter(object):
    def make_one(self, *args, **kwargs):
        from pyramid_log import Formatter
        return Formatter(*args, **kwargs)

    def test_with_explicit_request(self, log_record):
        log_record.request = Request.blank('/', POST={})
        formatter = self.make_one('{request.method}')
        assert formatter.format(log_record) == 'POST'

    def test_with_threadlocal_request(self, current_request, log_record):
        formatter = self.make_one('{request.method}')
        assert formatter.format(log_record) == 'GET'

    def test_format_called_with_log_disabled(self, log_record):
        manager = logging.root.manager
        class MockRequest(object):
            @property
            def disable(self):
                return manager.disable
        log_record.request = MockRequest()
        formatter = self.make_one('{request.disable}')
        assert formatter.format(log_record) == '%d' % log_record.levelno
        # Check that manager.disable is restored
        assert not manager.disable

class TestReplaceDict(object):
    def make_one(self, obj, d):
        from pyramid_log import _ReplaceDict
        return _ReplaceDict(obj, d)

    def test_getattr(self):
        class Obj(object):
            def m(self):
                return 'foo'
        obj = Obj()
        proxy = self.make_one(obj, {'x': 'bar'})
        assert proxy.m() == 'foo'
        assert proxy.x == 'bar'

    def test_setattr_modifies_proxy(self):
        obj = MockObject(x='orig')
        d = {}
        proxy = self.make_one(obj, d)
        proxy.x = 'changed'
        assert d['x'] == 'changed'
        assert obj.x == 'orig'

    def test_init_with_explicit_dict(self):
        obj = object()
        d = {}
        proxy = self.make_one(obj, d)
        assert proxy.__dict__ is d

class TestStrFormatFormatter(object):
    def make_one(self, *args, **kwargs):
        from .compat import StrFormatFormatter
        return StrFormatFormatter(*args, **kwargs)

    def make_log_record(self, **kwargs):
        d = dict(name='root',
                 level=logging.DEBUG,
                 msg='message',
                 args=(),
                 exc_info=None)
        d.update(kwargs)
        return logging.makeLogRecord(d)

    def test_raises_value_error_on_bad_style(self):
        with pytest.raises(ValueError):
            self.make_one(style='%')
        with pytest.raises(ValueError):
            self.make_one(style='$')

    def test_format(self):
        formatter = self.make_one('{goober}')
        record = self.make_log_record(goober='peanut')
        assert formatter.format(record) == 'peanut'

    def test_default_fmt(self):
        formatter = self.make_one()
        record = self.make_log_record(msg='howdy')
        assert formatter.format(record) == 'howdy'

    def test_uses_time(self):
        assert self.make_one('{asctime}').usesTime()
        assert self.make_one('{asctime:.4}').usesTime()
        assert not self.make_one('{facetime}').usesTime()

def test_FormatString():
    from .compat import _FormatString
    fs = _FormatString('foo={foo}')
    assert fs % {'foo': 'x'} == 'foo=x'
