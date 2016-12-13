import os
import re
import glob
import warnings
from six import StringIO
from django.db import transaction
from django.test import TestCase
from etl_sync.loaders import (
    get_logfilename, FeedbackCounter)
from .utils import captured_output
from .models import TestModel
from etl_sync.loaders import Loader, Extractor


class TestUtils(TestCase):

    def test_get_logfilename(self):
        logfile_path = get_logfilename(
            '/this/is/somewhere/on/the/filesystem.csv')
        self.assertTrue(
            re.match(
                r'^\/this\/is\/somewhere\/on\/the\/filesystem\.csv\.\d{4}-'
                '\d{2}-\d{2}\.log$',
                logfile_path))


class TestFeedbackCounter(TestCase):

    def test_feedbackcounter(self):
        counter = FeedbackCounter()
        self.assertEqual(counter.counter, 0)
        counter.increment()
        self.assertEqual(counter.counter, 1)
        counter.increment()
        self.assertEqual(counter.counter, 2)
        counter.reject()
        self.assertEqual(counter.counter, 3)
        self.assertEqual(counter.rejected, 1)
        counter.update()
        self.assertEqual(counter.counter, 4)
        self.assertEqual(counter.rejected, 1)
        self.assertEqual(counter.updated, 1)
        counter.create()
        self.assertEqual(counter.counter, 5)
        self.assertEqual(counter.updated, 1)
        self.assertEqual(counter.created, 1)


    def test_feedback(self):
        counter = FeedbackCounter()
        for index in range(0, 10):
            counter.create()
            counter.reject()
        with captured_output() as (out, err):
            counter.feedback(filename='test', records=20)
        # captured print output
        res = out.getvalue().strip()
        self.assertIn('10 created', res)
        self.assertIn('20 records processed', res)


class TestInit(TestCase):

    def test_logfilename(self):
        loader = Loader(filename='data.csv')
        name = loader.logfile.name
        self.assertTrue(
            re.match(r'^data.csv.\d{4}-\d{2}-\d{2}.log$', name))
        os.remove(name)
        loader = Loader(filename='data.csv', logfilename='test.log')
        self.assertEqual(loader.logfile.name, 'test.log')
        os.remove('test.log')
        loader = Loader(filename=StringIO('test'))
        self.assertFalse(loader.logfile)

    def test_feedbacksize(self):
        loader = Loader()
        self.assertEqual(loader.feedbacksize, 5000)
        loader = Loader(feedbacksize=20)
        self.assertEqual(loader.feedbacksize, 20)
        with self.settings(ETL_FEEDBACK=30):
            loader = Loader()
            self.assertEqual(loader.feedbacksize, 30)


class TestfileTestCase(TestCase):

    def setUp(self):
        path = os.path.dirname(os.path.realpath(__file__))
        self.filename = '{0}/data.txt'.format(path)

    def tearDown(self):
        path = os.path.dirname(os.path.realpath(__file__))
        files = glob.glob('%s/data.txt.*.log' % path)
        (os.remove(fil) for fil in files)
        TestModel.objects.all().delete()


class TestLoad(TestfileTestCase):
    """
    Tests data loading from file.
    """

    def test_load_from_file(self):
        with transaction.atomic():
            loader = Loader(filename=self.filename, model_class=TestModel)
            loader.load()
        self.assertEqual(TestModel.objects.all().count(), 3)
