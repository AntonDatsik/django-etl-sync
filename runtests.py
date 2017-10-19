#!/usr/bin/env python
import os
import sys
import django
from django.conf import settings


# put this here for now as long as we support Django 1.6.5
os.environ['DJANGO_SETTINGS_MODULE'] = 'tests.settings'


from django.test.utils import get_runner


tests = 'tests'
try:
    tests = sys.argv[1]
except IndexError:
    pass


if __name__ == "__main__":
    os.environ['DJANGO_SETTINGS_MODULE'] = 'tests.settings'
    try:
        django.setup()
    except AttributeError:
        pass
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    failures = test_runner.run_tests([tests])
    sys.exit(bool(failures))
