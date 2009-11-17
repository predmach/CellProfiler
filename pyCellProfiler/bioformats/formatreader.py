'''formatreader.py - mechanism to wrap a bioformats ReaderWrapper and ImageReader

Example:
    import bioformats.formatreader as biordr
    
    env = biordr.get_env()

    ChannelSeparator = biordr.make_reader_wrapper_class(env, 'loci/formats/ChannelSeparator')
    ImageReader = biordr.make_image_reader_class(env)

    cs = ChannelSeparator(ImageReader('/path/to/file.tif'))

    my_red_image, my_green_image, my_blue_image = \
        [cs.open_bytes(cs.getIndex(0,i,0)) for i in range(3)]
'''
    
__version__ = "$Revision: 1$"

import numpy as np
import os
import sys

import cellprofiler.utilities.jutil as jutil
import bioformats
import cellprofiler.utilities.javabridge as javabridge

def make_format_tools_class():
    '''Get a wrapper for the loci/formats/FormatTools class
    
    The FormatTools class has many of the constants needed by
    other classes as statics.
    '''
    class FormatTools(object):
        '''A wrapper for loci.formats.FormatTools
        
        See http://hudson.openmicroscopy.org.uk/job/LOCI/javadoc/loci/formats/FormatTools.html
        '''
        env = jutil.get_env()
        klass = env.find_class('loci/formats/FormatTools')
        CAN_GROUP = jutil.get_static_field(klass, 'CAN_GROUP','I')
        CANNOT_GROUP = jutil.get_static_field(klass, 'CANNOT_GROUP','I')
        DOUBLE = jutil.get_static_field(klass, 'DOUBLE','I')
        FLOAT = jutil.get_static_field(klass, 'FLOAT', 'I')
        INT16 = jutil.get_static_field(klass, 'INT16', 'I')
        INT32 = jutil.get_static_field(klass, 'INT32', 'I')
        INT8 = jutil.get_static_field(klass, 'INT8', 'I')
        MUST_GROUP = jutil.get_static_field(klass, 'MUST_GROUP', 'I')
        UINT16 = jutil.get_static_field(klass, 'UINT16', 'I')
        UINT32 = jutil.get_static_field(klass, 'UINT32', 'I')
        UINT8 = jutil.get_static_field(klass, 'UINT8', 'I')
    return FormatTools

def make_iformat_reader_class(class_name):
    '''Bind a Java class that implements IFormatReader to a Python class
    
    Returns a class that implements IFormatReader through calls to the
    implemented class passed in. The returned class can be subclassed to
    provide additional bindings.
    '''
    env = jutil.get_env()
    class IFormatReader(object):
        '''A wrapper for loci.formats.IFormatReader
        
        See http://hudson.openmicroscopy.org.uk/job/LOCI/javadoc/loci/formats/ImageReader.html
        '''
        close = jutil.make_method('close','()V',
                                  'Close the currently open file and free memory')
        getDimensionOrder = jutil.make_method('getDimensionOrder',
                                              '()Ljava/lang/String;',
                                              'Return the dimension order as a five-character string, e.g. "XYCZT"')
        getMetadata = jutil.make_method('getMetadata',
                                              '()Ljava/util/Hashtable;',
                                              'Obtains the hashtable containing the metadata field/value pairs')
        getMetadataValue = jutil.make_method('getMetadataValue',
                                             '(Ljava/lang/String;)'
                                             'Ljava/lang/Object;',
                                             'Look up a specific metadata value from the store')
        getImageCount = jutil.make_method('getImageCount',
                                          '()I','Determines the number of images in the current file')
        getIndex = jutil.make_method('getIndex', '(III)I',
                                     'Get the plane index given z, c, t')
        getRGBChannelCount = jutil.make_method('getRGBChannelCount',
                                               '()I','Gets the number of channels per RGB image (if not RGB, this returns 1')
        getSizeC = jutil.make_method('getSizeC', '()I',
                                     'Get the number of color planes')
        getSizeT = jutil.make_method('getSizeT', '()I',
                                     'Get the number of frames in the image')
        getSizeX = jutil.make_method('getSizeX', '()I',
                                     'Get the image width')
        getSizeY = jutil.make_method('getSizeY', '()I',
                                     'Get the image height')
        getSizeZ = jutil.make_method('getSizeZ', '()I',
                                     'Get the image depth')
        getPixelType = jutil.make_method('getPixelType', '()I',
                                         'Get the pixel type: see FormatTools for types')
        isLittleEndian = jutil.make_method('isLittleEndian',
                                           '()Z','Return True if the data is in little endian order')
        isRGB = jutil.make_method('isRGB', '()Z',
                                  'Return True if images in the file are RGB')
        isInterleaved = jutil.make_method('isInterleaved', '()Z',
                                          'Return True if image colors are interleaved within a plane')
        openBytes = jutil.make_method('openBytes','(I)[B',
                                      'Get the specified image plane as a byte array')
        openBytesXYWH = jutil.make_method('openBytes','(IIIII)[B',
                                          '''Get the specified image plane as a byte array
                                          
                                          (corresponds to openBytes(int no, int x, int y, int w, int h))
                                          no - image plane number
                                          x,y - offset into image
                                          w,h - dimensions of image to return''')
    return IFormatReader
    
def make_image_reader_class():
    '''Return an image reader class for the given Java environment'''
    env = jutil.get_env()
    class_name = 'loci/formats/ImageReader'
    klass = env.find_class(class_name)
    base_klass = env.find_class('loci/formats/IFormatReader')
    IFormatReader = make_iformat_reader_class(class_name)
    #
    # This uses the reader.txt file from inside the loci_tools.jar
    #
    class_list = jutil.make_instance("loci/formats/ClassList", 
                                     "(Ljava/lang/String;"
                                     "Ljava/lang/Class;" # base
                                     "Ljava/lang/Class;)V", # location in jar
                                     "readers.txt", base_klass, klass)
    class ImageReader(IFormatReader):
        new_fn = jutil.make_new(class_name, '(Lloci/formats/ClassList;)V')
        def __init__(self):
            self.new_fn(class_list)
        setId = jutil.make_method('setId', '(Ljava/lang/String;)V',
                                  'Set the name of the data file')
        getFormat = jutil.make_method('getFormat',
                                      '()Ljava/lang/String;',
                                      'Get a string describing the format of this file')
        getReader = jutil.make_method('getReader',
                                      '()Lloci/formats/IFormatReader;')
    return ImageReader

        
def make_reader_wrapper_class(class_name):
    '''Make an ImageReader wrapper class
    
    class_name - the name of the wrapper class, for instance, 
                 "loci/formats/ChannelSeparator"
    
    You can instantiate an instance of the wrapper class like this:
    rdr = ChannelSeparator(ImageReader())
    '''
    IFormatReader = make_iformat_reader_class(class_name)
    class ReaderWrapper(IFormatReader):
        __doc__ = '''A wrapper for %s
        
        See http://hudson.openmicroscopy.org.uk/job/LOCI/javadoc/loci/formats/ImageReader.html
        '''%class_name
        new_fn = jutil.make_new(class_name, '(Lloci/formats/IFormatReader;)V')
        def __init__(self, rdr):
            self.new_fn(rdr)
            
        setId = jutil.make_method('setId', '(Ljava/lang/String;)V',
                                  'Set the name of the data file')
    return ReaderWrapper

def make_format_writer_class(class_name):
    '''Make a FormatWriter wrapper class
    
    class_name - the name of a class that implements loci.formats.FormatWriter
                 Known names in the loci.formats.out package:
                     APNGWriter, AVIWriter, EPSWriter, ICSWriter, ImageIOWriter,
                     JPEG2000Writer, JPEGWriter, LegacyQTWriter, OMETiffWriter,
                     OMEXMLWriter, QTWriter, TiffWriter
    '''
    new_fn = jutil.make_new(class_name, 
                            '(Ljava/lang/String;Ljava/lang/String;)V')
    class FormatWriter(object):
        __doc__ = '''A wrapper for %s implementing loci.formats.FormatWriter
        See http://hudson.openmicroscopy.org.uk/job/LOCI/javadoc/loci/formats/FormatWriter'''%class_name
        def __init__(self):
            self.new_fn()
            
        canDoStacks = jutil.make_method('canDoStacks','()Z',
                                        'Reports whether the writer can save multiple images to a single file')
        getColorModel = jutil.make_method('getColorModel',
                                          '()Ljava/awt/image/ColorModel;',
                                          'Gets the color model')
        getCompression = jutil.make_method('getCompression',
                                           '()Ljava/lang/String;',
                                           'Gets the current compression type')
        getCompressionTypes = jutil.make_method('getCompressionTypes',
                                                '()[Ljava/lang/String;',
                                                'Gets the available compression types')
        getFramesPerSecond = jutil.make_method('getFramesPerSecond',
                                               '()I', "Gets the frames per second to use when writing")
        getMetadataRetrieve = jutil.make_method('getMetadataRetrieve',
                                                '()Lloci/formats/meta/MetadataRetrieve;',
                                                'Retrieves the current metadata retrieval object for this writer.')
        
        getPixelTypes = jutil.make_method('getPixelTypes',
                                          '()[I')
        isInterleaved = jutil.make_method('isInterleaved','()Z',
                                          'Gets whether or not the channels in an image are interleaved')
        isSupportedType = jutil.make_method('isSupportedType','(I)Z',
                                            'Checks if the given pixel type is supported')
        saveBytes = jutil.make_method('saveBytes', '([BZ)V',
                                      'Saves the given byte array to the current file')
        setColorModel = jutil.make_method('setColorModel',
                                          '(Ljava/awt/image/ColorModel;)V',
                                          'Sets the color model')
        setCompression = jutil.make_method('setCompression',
                                           '(Ljava/lang/String;)V',
                                           'Sets the current compression type')
        setFramesPerSecond = jutil.make_method('setFramesPerSecond',
                                               '(I)V',
                                               'Sets the frames per second to use when writing')
        setId = jutil.make_method('setId','(Ljava/lang/String;)V',
                                  'Sets the current file name')
        setInterleaved = jutil.make_method('setInterleaved', '(Z)V',
                                           'Sets whether or not the channels in an image are interleaved')
        setMetadataRetrieve = jutil.make_method('setMetadataRetrieve',
                                                '(Lloci/formats/meta/MetadataRetrieve;)V',
                                                'Sets the metadata retrieval object from which to retrieve standardized metadata')
    return FormatWriter
        
if __name__ == "__main__":
    import wx
    import matplotlib.backends.backend_wxagg as mmmm
    import bioformats
    
    jutil.attach()
    ImageReader = make_image_reader_class()
    ChannelSeparator = make_reader_wrapper_class("loci/formats/ChannelSeparator")
    FormatTools = make_format_tools_class()
    class MyApp(wx.App):
        def OnInit(self):
            self.PrintMode = 0
            dlg = wx.FileDialog(None)
            if dlg.ShowModal()==wx.ID_OK:
                rdr = ImageReader()
                rdr.setId(dlg.Path)
                print "Format = %s"%rdr.getFormat()
                w = rdr.getSizeX()
                h = rdr.getSizeY()
                pixel_type = rdr.getPixelType()
                little_endian = rdr.isLittleEndian()
                metadata = rdr.getMetadata()
                d = jutil.jdictionary_to_string_dictionary(metadata)
                for key in d.keys():
                    print key+"="+d[key]
                if pixel_type == FormatTools.INT8:
                    dtype = np.char
                elif pixel_type == FormatTools.UINT8:
                    dtype = np.uint8
                elif pixel_type == FormatTools.UINT16:
                    dtype = '<u2' if little_endian else '>u2'
                elif pixel_type == FormatTools.INT16:
                    dtype = '<i2' if little_endian else '>i2'
                elif pixel_type == FormatTools.UINT32:
                    dtype = '<u4' if little_endian else '>u4'
                elif pixel_type == FormatTools.INT32:
                    dtype = '<i4' if little_endian else '>i4'
                elif pixel_type == FormatTools.FLOAT:
                    dtype = '<f4' if little_endian else '>f4'
                elif pixel_type == FormatTools.DOUBLE:
                    dtype = '<f8' if little_endian else '>f8'
                    
                if rdr.getRGBChannelCount() > 1:
                    rdr.close()
                    rdr = ChannelSeparator(ImageReader())
                    rdr.setId(dlg.Path)
                    red_image, green_image, blue_image = [
                        np.frombuffer(rdr.openBytes(rdr.getIndex(0,i,0)),dtype)
                        for i in range(3)]
                    image = np.dstack((red_image, green_image, blue_image))
                    image.shape=(h,w,3)
                else:
                    image = np.frombuffer(rdr.openBytes(0),dtype)
                    image.shape = (h,w)
                rdr.close()
                fig = mmmm.Figure()
                axes = fig.add_subplot(1,1,1)
                axes.imshow(image)
                frame = mmmm.FigureFrameWxAgg(1,fig)
                frame.Show()
                return True
            return False
    app = MyApp(0)
    app.MainLoop()
    jutil.detach()
    
    