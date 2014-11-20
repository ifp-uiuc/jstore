import os
from StringIO import StringIO

import numpy
import Image

class Jstore(object):
    '''Helper class to get data from jstore `database`.

    Parameters
    ----------
    path : str
        Location of the database
    mode : str
        Either 'disk' or 'memory'
        In 'disk' mode, `get` reads images from disk.
        In 'memory' mode, the database is copied from disk to memory
        on initialization. Afterwards `get` reads images from memory.
        So `memory` mode is better if you are going to access the data
        multiple times.
    '''
    def __init__(self, path, mode='disk'):
        self.path = path

        if not os.path.exists(path):
            raise Exception("path doesn't exist")

        if mode not in ['disk', 'memory']:
            raise Exception("Unknown mode.")

        # Make file paths
        self.header_path = os.path.join(path, "header")
        self.data_path = os.path.join(path, "data")

        # Load header into memory
        # header is currently array of jpeg sizes
        self.header = numpy.fromstring(
            open(self.header_path, 'rb').read(), 
            dtype=numpy.uint32) # 32 bits, 4 bytes

        self.num_entries = len(self.header)

        # Calculate the offset by summing up the sizes
        self.offsets = numpy.cumsum(
            numpy.hstack((numpy.uint32(0), # makes the first offset 0
                          self.header)))

        # Open data
        if mode == 'disk':
            self.data_file = open(self.data_path, 'rb')
        elif mode == 'memory':
            print 'Loading jstore data into memory...'
            self.data_file = StringIO(open(self.data_path, 'rb').read())
            print 'Done.'

    def get(self, i):
        offset = self.offsets[i]
        size = self.header[i]
        self.data_file.seek(offset)
        string = self.data_file.read(size)

        # Steps to convert jpeg string to numpy array
        string_file = StringIO(string)
        image = Image.open(string_file).convert('RGB')
        array = numpy.array(image)
        return array

class JstoreMaker(object):
    '''Helper class to create jstore `database`.

    Parameters
    ----------
    path : str
        Location to save the database.
    '''
    def __init__(self, path):
        self.path = path

        # Make path if it doesn't exist
        if not os.path.exists(self.path):
            os.makedirs(self.path)

        # Make file paths
        self.header_path = os.path.join(path, "header")
        self.data_path = os.path.join(path, "data")

        self.header_list = []
        self.data_list = []

    def append(self, string):
        bytes = numpy.uint32(len(string)) # 32 bits, 4 bytes

        self.header_list.append(bytes)
        self.data_list.append(string)

    def save(self):
        # Save header
        header_file = open(self.header_path, 'wb')
        for item in self.header_list:
            header_file.write(item)
        header_file.close()

        # Save data file
        data_file = open(self.data_path, 'wb')
        for item in self.data_list:
            data_file.write(item)
        data_file.close()


def make_jstore(path):
    '''Creates a jstore `database` from the jpegs in path.

    Reads the jpegs at `path` and creates a jstore `database` to store
    them. It creates the jstore `database` at '<path>\jstore'.

    Parameters
    ----------
    path : str
        Path to directory full of jpegs. Currently expects files to end
        with '.jpeg'.
    '''
    filenames = numpy.sort(os.listdir(path))
    jpeg_filenames = [item for item in filenames
        if item.endswith('.jpeg')]

    jstore_path = os.path.join(path, 'jstore')
    jstore_maker = JstoreMaker(jstore_path)

    print 'Reading jpegs...'
    for filename in jpeg_filenames:
        string = open(filename, 'rb').read()
        jstore_maker.append(string)
    print 'Done.'

    print 'Saving jstore...'
    jstore_maker.save()
    print 'Done.'