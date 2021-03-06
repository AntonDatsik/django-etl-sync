from __future__ import print_function

import csv
import glob
import os
import re
from unittest import skip

from django.test import TestCase, TransactionTestCase
from six import StringIO, text_type

from etl_sync.loaders import Extractor, Loader
from etl_sync.transformations import Transformer
from .models import ElNumero, TestModel
from .utils import captured_output


@skip
class TestUtils(TestCase):

    def test_get_logfilename(self):
        logfile_path = get_logfilename(
            '/this/is/somewhere/on/the/filesystem.csv')
        self.assertTrue(
            re.match(
                r'^\/this\/is\/somewhere\/on\/the\/filesystem\.csv\.\d{4}-'
                '\d{2}-\d{2}\.log$',
                logfile_path))


@skip
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


@skip
class TestInit(TestCase):

    def test_logfilename(self):
        loader = Loader('data.csv', model_class=TestModel)
        name = loader.logfile.name
        self.assertTrue(
            re.match(r'^data.csv.\d{4}-\d{2}-\d{2}.log$', name))
        os.remove(name)
        options = {'logfilename': 'test.log'}
        loader = Loader('data.csv', model_class=TestModel, options=options)
        self.assertEqual(loader.logfile.name, 'test.log')
        os.remove('test.log')
        loader = Loader(StringIO('test'), model_class=TestModel)
        self.assertFalse(loader.logfile)

    def test_feedbacksize(self):
        loader = Loader(None, model_class=TestModel)
        self.assertEqual(loader.feedbacksize, 5000)
        options = {'feedbacksize': 20}
        loader = Loader(None, model_class=TestModel, options=options)
        self.assertEqual(loader.feedbacksize, 20)


class TestLoad(TransactionTestCase):
    """
    Tests data loading from file.
    """

    def setUp(self):
        path = os.path.dirname(os.path.realpath(__file__))
        self.filename = '{0}/data.txt'.format(path)

    def tearDown(self):
        path = os.path.dirname(os.path.realpath(__file__))
        files = glob.glob('%s/data.txt.*.log' % path)
        (os.remove(fil) for fil in files)

    def test_load_from_file(self):
        loader = Loader(self.filename, model_class=TestModel)
        loader.load()
        self.assertEqual(TestModel.objects.all().count(), 3)


class TestHeaderlessLoad(TransactionTestCase):
    """
    Tests data loading from file without headers.
    """

    def setUp(self):
        path = os.path.dirname(os.path.realpath(__file__))
        self.filename = '{0}/data_no_headers.txt'.format(path)

    def tearDown(self):
        path = os.path.dirname(os.path.realpath(__file__))
        files = glob.glob('%s/data.txt.*.log' % path)
        for fil in files:
            os.remove(fil)

    def test_load_from_file(self):
        class HeaderlessTransformer(Transformer):
            mappings = {
                'rec': 'rec',
                'name': 'name',
                'nochwas': 'nochwas',
            }

        class HeaderlessLoader(Loader):
            """"""
            transformer_class = HeaderlessTransformer
            reader_kwargs = {
                'fieldnames': [
                    'rec', 'name', 'nochwas',
                ],
                'delimiter': u'\t',
                'quoting': csv.QUOTE_NONE
            }

        model = ElNumero

        loader = HeaderlessLoader(self.filename, model_class=model)
        loader.load()
        self.assertEqual(model.objects.count(), 3)


class TestExtractor(TestCase):
    """Test newly introduced ExtractorClass."""

    def setUp(self):
        self.filename = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), 'data.txt')

    def test_fileload(self):
        extractor = Extractor(self.filename)
        with extractor as ex:
            ct = 0
            for item in ex:
                ct += 1
                self.assertTrue(isinstance(item, dict))
            self.assertEqual(ct, 3)
            ct = 0

    def test_filelikeobject(self):
        with open(self.filename) as fil:
            content = StringIO(text_type(fil.read()))
        extractor = Extractor(content)
        with extractor as ex:
            ct = 0
            for item in ex:
                ct += 1
                self.assertTrue(isinstance(item, dict))
            self.assertEqual(ct, 3)
            ct = 0


class TestFileLikeObjectInLoader(TestCase):

    def setUp(self):
        self.filename = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), 'data.txt')

    def test_filelikeobject(self):
        with open(self.filename) as fil:
            content = StringIO(text_type(fil.read()))
        loader = Loader(content, model_class=TestModel)
        loader.load()
        self.assertEqual(TestModel.objects.all().count(), 3)


class TestOptionPassing(TestCase):

    def test_optionpassing(self):
        options = {
            'create': False,
            'update': True
        }
        ldr = Loader('test', model_class=TestModel, options=options)
        self.assertEqual(ldr.extractor.options, options)
        self.assertFalse(ldr.generator.create)
