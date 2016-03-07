try:
    import unittest2 as unittest  # to support Python 2.6
except ImportError:
    import unittest

from deepdiff import DeepDiff

from pprint import PrettyPrinter
pp = PrettyPrinter(indent=4)

import gazelib
from gazelib.containers import CommonV1

import jsonschema

import os
import tempfile

def get_sample_filepath(sample_name):
    '''
    Create absolute filepath from sample filename.
    '''
    this_dir = os.path.dirname(os.path.realpath(__file__))
    full_path = os.path.join(this_dir, 'fixtures', sample_name)
    return full_path

def get_temp_filepath(file_name):
    '''
    Generate filepath for a file that is needed only briefly.
    '''
    # Absolute path to temp dir.
    p = tempfile.mkdtemp()
    return os.path.join(p, file_name)

def remove_temp_file(abs_filepath):
    '''
    Remove file created by the tempfile.mkdtemp
    Warning! Is capable to remove any file and its directory.
    '''
    d = os.path.dirname(abs_filepath)
    os.remove(abs_filepath)
    os.rmdir(d)

def load_sample(sample_name):
    '''
    Reads from fixtures/ directory
    Access e.g. by: load_sample('sample.common.json')
    '''
    full_path = get_sample_filepath(sample_name)
    return gazelib.io.load_json(full_path)


def assert_valid(self, common_raw, msg='Invalid CommonV1 structure'):
    '''
    Assert given dict is valid gazelib/common/v1
    '''
    try:
        CommonV1.validate(common_raw)
    except:
        self.fail(msg)


class TestCommonV1(unittest.TestCase):

    def test_empty_init(self):
        c = CommonV1()
        assert_valid(self, c.raw, 'CommonV1 default structure is invalid.')

    def test_init_with_file(self):
        fpath = get_sample_filepath('sample.common.json')
        c = CommonV1(fpath)
        assert_valid(self, c.raw)

    def test_validate(self):
        raw = load_sample('sample.common.json')
        subraw = load_sample('subsample.common.json')

        # Ensure fixtures are valid
        assert_valid(self, raw)
        assert_valid(self, subraw)

        # Make invalid modification
        raw['events'] = 'foo'
        f = lambda: CommonV1.validate(raw)
        self.assertRaises(jsonschema.ValidationError, f)

        # Make invalid modification
        subraw['schema'] = 'foo'
        f = lambda: CommonV1.validate(subraw)
        self.assertRaises(jsonschema.ValidationError, f)

    def test_get_start_end_time(self):
        subraw = load_sample('subsample.common.json')
        subg = CommonV1(subraw)

        t0 = subg.get_relative_start_time()
        t1 = subg.get_relative_end_time()
        dur = subg.get_duration()

        self.assertEqual(t0, -0.5)
        self.assertEqual(t1, 0.5)
        self.assertEqual(dur, 1.0)

    def test_slice_by_relative_time(self):

        raw = load_sample('sample.common.json')
        subraw = load_sample('subsample.common.json')
        g = gazelib.containers.CommonV1(raw)
        subg = gazelib.containers.CommonV1(subraw)

        sliceg = g.slice_by_relative_time(0.05, 0.11)

        dd = DeepDiff(sliceg.raw, subg.raw)
        self.assertEqual(dd, {})

    def test_slice_by_global_time(self):
        raw = load_sample('sample.common.json')
        subraw = load_sample('subsample.common.json')
        g = gazelib.containers.CommonV1(raw)
        subg = gazelib.containers.CommonV1(subraw)

        sliceg = g.slice_by_global_time(1234567890.05, 1234567890.11)

        dd = DeepDiff(sliceg.raw, subg.raw)
        self.assertEqual(dd, {})

    def test_slice_by_timeline(self):

        raw = load_sample('sample.common.json')
        subraw = load_sample('subsample.common.json')
        g = gazelib.containers.CommonV1(raw)
        subg = gazelib.containers.CommonV1(subraw)

        sliceg = g.slice_by_timeline('ecg', 5)

        dd = DeepDiff(subg.raw, sliceg.raw)
        # pp.pprint(dd)
        # pp.pprint(sliceg.raw)
        self.assertEqual(dd, {})

    def test_slice_by_tag(self):

        raw = load_sample('sample.common.json')
        subraw = load_sample('subsample.common.json')
        g = gazelib.containers.CommonV1(raw)
        subg = gazelib.containers.CommonV1(subraw)

        sliceg = g.slice_by_tag('test/last-half')

        dd = DeepDiff(subg.raw, sliceg.raw)
        self.assertEqual(dd, {})

    def test_iter_slices_by_tag(self):

        raw = load_sample('sample.common.json')
        g = gazelib.containers.CommonV1(raw)

        slices = list(g.iter_slices_by_tag('test/center'))

        self.assertEqual(len(slices), 2)
        self.assertEqual(len(slices[0].raw['events']), 5)
        self.assertEqual(len(slices[1].raw['events']), 4)  # no first-half
        self.assertEqual(len(slices[1].raw['timelines']['eyetracker']), 1)

        #dd = DeepDiff(subg.raw, sliceg.raw)
        #self.assertEqual(dd, {})

    def test_add_environment(self):

        raw = load_sample('sample.common.json')
        g = gazelib.containers.CommonV1(raw)

        g.add_environment('test_env', 123)
        self.assertEqual(g.get_environment('test_env'), 123)
        self.assertIn('test_env', g.get_environment_names())

        self.assertTrue(g.has_environments(['test_env']))
        f = lambda: g.assert_has_environments(['test_env', 'foo'])
        self.assertRaises(CommonV1.InsufficientDataException, f)

        assert_valid(self, g.raw)

    def test_add_stream(self):

        raw = load_sample('sample.common.json')
        g = gazelib.containers.CommonV1(raw)

        tlex = gazelib.containers.CommonV1.MissingTimelineException
        isex = gazelib.containers.CommonV1.InvalidStreamException

        f = lambda: g.add_stream('my_stream', 'my_timeline', [1,2,3])
        self.assertRaises(tlex, f)

        f = lambda: g.add_stream('my_stream', 'eyetracker', [1])
        self.assertRaises(isex, f)

        g.add_stream('my_stream', 'eyetracker', [1, 2, 3, 4, 5])
        self.assertIn('my_stream', g.get_stream_names())

        self.assertTrue(g.has_streams(['my_stream']))
        f = lambda: g.assert_has_streams(['my_stream', 'foo'])
        self.assertRaises(CommonV1.InsufficientDataException, f)

        assert_valid(self, g.raw)

    def test_add_event(self):

        raw = load_sample('sample.common.json')
        g = gazelib.containers.CommonV1(raw)

        ieex = gazelib.containers.CommonV1.InvalidEventException

        f = lambda: g.add_event('my_tag', 0.0, 1.4)
        self.assertRaises(ieex, f)

        f = lambda: g.add_event(['my_tag', 'my_tag2'], 'a', 1.4)
        self.assertRaises(ieex, f)

        g.add_event(['my_tag', 'my_tag2'], 0.0, 1.4)
        l = list(g.iter_events_by_tag('my_tag'))
        self.assertEqual(len(l), 1)

        assert_valid(self, g.raw)

    def test_save_as_json(self):

        fpath = get_temp_filepath('myfile.json')
        c = CommonV1()
        c.add_environment('test', 'hello')
        c.save_as_json(fpath)

        cc = CommonV1(fpath)
        self.assertTrue(cc.has_environments(['test']))

        self.assertTrue(os.path.exists(fpath))
        remove_temp_file(fpath)
        self.assertFalse(os.path.exists(fpath))
