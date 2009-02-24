"""test_crop.py - test the Crop module

"""
__version__="$Revision$"

import base64
import numpy as np
import unittest
import StringIO

import cellprofiler.workspace as cpw
import cellprofiler.pipeline as cpp
import cellprofiler.cpimage as cpi
import cellprofiler.modules.crop as cpmc
import cellprofiler.measurements as cpm
import cellprofiler.objects as cpo
import cellprofiler.preferences as cpprefs

INPUT_IMAGE = "input_image"
CROP_IMAGE = "crop_image"
CROPPING = "cropping"
OUTPUT_IMAGE = "output_image"

class TestCrop(unittest.TestCase):
    def make_workspace(self, 
                       input_pixels,
                       crop_image = None,
                       cropping = None ):
        """Return a workspace with the given images installed and the crop module"""
        image_set_list = cpi.ImageSetList()
        image_set = image_set_list.get_image_set(0)
        module = cpmc.Crop()
        image_set.add(INPUT_IMAGE, cpi.Image(input_pixels))
        module.image_name.value = INPUT_IMAGE
        module.cropped_image_name.value = OUTPUT_IMAGE 
        if crop_image != None:
            image_set.add(CROP_IMAGE, cpi.Image(crop_image))
            module.image_mask_source.value = CROP_IMAGE
        if cropping != None:
            image_set.add(CROPPING, cpi.Image(crop_mask = cropping))
            module.cropping_mask_source.value = CROPPING
        workspace = cpw.Workspace(cpp.Pipeline(),
                                  module,
                                  image_set,
                                  cpo.ObjectSet(),
                                  cpm.Measurements(),
                                  image_set_list)
        return workspace, module
    
    def test_00_00_zeros(self):
        """Test cropping an image with a mask of all zeros"""
        workspace, module = self.make_workspace(np.zeros((10,10)),
                                                crop_image = np.zeros((10,10),bool))
        module.shape.value = cpmc.SH_IMAGE
        module.remove_rows_and_columns.value = cpmc.RM_NO
        module.run(workspace)
        output_image = workspace.image_set.get_image(OUTPUT_IMAGE)
        self.assertTrue(np.all(output_image.pixel_data == 0))
        self.assertTrue(np.all(output_image.mask == output_image.pixel_data))
        self.assertTrue(np.all(output_image.crop_mask == output_image.pixel_data))
        m = workspace.measurements
        pixel_area = cpprefs.get_pixel_size() ** 2
        self.assertTrue('Image' in m.get_object_names())
        feature = 'Crop_OriginalImageArea_%s'%(OUTPUT_IMAGE)
        self.assertTrue(feature in m.get_feature_names('Image'))
        values = m.get_current_measurement('Image',feature)
        self.assertEqual(len(values),1)
        self.assertAlmostEqual(values[0],10*10*pixel_area)
        feature = 'Crop_AreaRetainedAfterCropping_%s'%(OUTPUT_IMAGE)
        self.assertTrue(feature in m.get_feature_names('Image'))
        values = m.get_current_measurement('Image',feature)
        self.assertEqual(len(values),1)
        self.assertEqual(values[0],0)
    
    def test_00_01_zeros_and_remove_all(self):
        """Test cropping and removing rows and columns on a blank image"""
        workspace, module = self.make_workspace(np.zeros((10,10)),
                                                crop_image = np.zeros((10,10),bool))
        module.shape.value = cpmc.SH_IMAGE
        module.remove_rows_and_columns.value = cpmc.RM_ALL
        module.run(workspace)
        output_image = workspace.image_set.get_image(OUTPUT_IMAGE)
        self.assertEqual(np.product(output_image.pixel_data.shape),0)
    
    def test_01_01_crop_edges_with_image(self):
        """Test cropping and removing rows and columns with an image"""
        x,y = np.mgrid[0:10,0:10]
        input_image = x/100.0 + y/10.0
        crop_image = np.zeros((10,10),bool)
        crop_image[2,3] = True
        crop_image[7,5] = True
        expected_image = np.zeros((6,3)) 
        expected_image[0,0]=input_image[2,3]
        expected_image[5,2]=input_image[7,5]
        workspace, module = self.make_workspace(input_image,
                                                crop_image = crop_image)
        module.shape.value = cpmc.SH_IMAGE
        module.remove_rows_and_columns.value = cpmc.RM_EDGES
        module.run(workspace)
        output_image = workspace.image_set.get_image(OUTPUT_IMAGE)
        self.assertTrue(np.all(output_image.pixel_data == expected_image))

    def test_01_02_crop_all_with_image(self):
        """Test cropping and removing rows and columns with an image"""
        x,y = np.mgrid[0:10,0:10]
        input_image = x/100.0 + y/10.0
        crop_image = np.zeros((10,10),bool)
        crop_image[2,3] = True
        crop_image[7,5] = True
        expected_image = input_image[(2,7),:][:,(3,5)]
        expected_image[1,0] = 0
        expected_image[0,1] = 0
        workspace, module = self.make_workspace(input_image,
                                                crop_image = crop_image)
        module.shape.value = cpmc.SH_IMAGE
        module.remove_rows_and_columns.value = cpmc.RM_ALL
        module.run(workspace)
        output_image = workspace.image_set.get_image(OUTPUT_IMAGE)
        self.assertTrue(np.all(output_image.pixel_data == expected_image))
    
    def test_02_01_crop_edges_with_cropping(self):
        """Test cropping and removing rows and columns with an image cropping"""
        x,y = np.mgrid[0:10,0:10]
        input_image = x/100.0 + y/10.0
        crop_image = np.zeros((10,10),bool)
        crop_image[2,3] = True
        crop_image[7,5] = True
        expected_image = np.zeros((6,3)) 
        expected_image[0,0]=input_image[2,3]
        expected_image[5,2]=input_image[7,5]
        workspace, module = self.make_workspace(input_image,
                                                cropping = crop_image)
        module.shape.value = cpmc.SH_CROPPING
        module.remove_rows_and_columns.value = cpmc.RM_EDGES
        module.run(workspace)
        output_image = workspace.image_set.get_image(OUTPUT_IMAGE)
        self.assertTrue(np.all(output_image.pixel_data == expected_image))
    
    def test_03_01_crop_with_ellipse_x_major(self):
        """Crop with an ellipse that has its major axis in the X direction"""
        x,y = np.mgrid[0:10,0:10]
        input_image = x/100.0 + y/10.0
        workspace, module = self.make_workspace(input_image)
        module.shape.value = cpmc.SH_ELLIPSE
        module.remove_rows_and_columns.value = cpmc.RM_EDGES
        module.ellipse_center.set_value((4,5))
        module.ellipse_x_radius.value = 3
        module.ellipse_y_radius.value = 2
        expected_image = input_image[3:8,1:8]
        for i,j in ((0,0),(1,0),(0,1),(0,2)):
            expected_image[i,j] = 0
            expected_image[-i-1,j] = 0
            expected_image[i,-j-1] = 0
            expected_image[-i-1,-j-1] = 0
        module.run(workspace)
        output_image = workspace.image_set.get_image(OUTPUT_IMAGE)
        self.assertTrue(np.all(output_image.pixel_data == expected_image))
    
    def test_03_02_crop_with_ellipse_y_major(self):
        x,y = np.mgrid[0:10,0:10]
        input_image = x/100.0 + y/10.0
        workspace, module = self.make_workspace(input_image)
        module.shape.value = cpmc.SH_ELLIPSE
        module.remove_rows_and_columns.value = cpmc.RM_EDGES
        module.ellipse_center.set_value((5,4))
        module.ellipse_x_radius.value = 2
        module.ellipse_y_radius.value = 3
        expected_image = input_image[1:8,3:8]
        for i,j in ((0,0),(1,0),(0,1),(2,0)):
            expected_image[i,j] = 0
            expected_image[-i-1,j] = 0
            expected_image[i,-j-1] = 0
            expected_image[-i-1,-j-1] = 0
        module.run(workspace)
        output_image = workspace.image_set.get_image(OUTPUT_IMAGE)
        self.assertTrue(np.all(output_image.pixel_data == expected_image))
        
    def test_04_01_crop_with_rectangle(self):
        x,y = np.mgrid[0:10,0:10]
        input_image = x/100.0 + y/10.0
        expected_image = input_image[2:8,1:9]
        workspace, module = self.make_workspace(input_image)
        module.shape.value = cpmc.SH_RECTANGLE
        module.horizontal_limits.set_value((1,9))
        module.vertical_limits.set_value((2,8))
        module.remove_rows_and_columns.value = cpmc.RM_EDGES
        module.run(workspace)
        output_image = workspace.image_set.get_image(OUTPUT_IMAGE)
        self.assertTrue(np.all(output_image.pixel_data == expected_image))

    def test_04_02_crop_with_rectangle_unbounded_xmin(self):
        x,y = np.mgrid[0:10,0:10]
        input_image = x/100.0 + y/10.0
        expected_image = input_image[2:8,:9]
        workspace, module = self.make_workspace(input_image)
        module.shape.value = cpmc.SH_RECTANGLE
        module.horizontal_limits.set_value((0,9))
        module.vertical_limits.set_value((2,8))
        module.remove_rows_and_columns.value = cpmc.RM_EDGES
        module.run(workspace)
        output_image = workspace.image_set.get_image(OUTPUT_IMAGE)
        self.assertTrue(np.all(output_image.pixel_data == expected_image))

    def test_04_03_crop_with_rectangle_unbounded_xmax(self):
        x,y = np.mgrid[0:10,0:10]
        input_image = x/100.0 + y/10.0
        expected_image = input_image[2:8,1:]
        workspace, module = self.make_workspace(input_image)
        module.shape.value = cpmc.SH_RECTANGLE
        module.horizontal_limits.set_value((1,"end"))
        module.vertical_limits.set_value((2,8))
        module.remove_rows_and_columns.value = cpmc.RM_EDGES
        module.run(workspace)
        output_image = workspace.image_set.get_image(OUTPUT_IMAGE)
        self.assertTrue(np.all(output_image.pixel_data == expected_image))
        
    def test_04_04_crop_with_rectangle_unbounded_ymin(self):
        x,y = np.mgrid[0:10,0:10]
        input_image = x/100.0 + y/10.0
        expected_image = input_image[:8,1:9]
        workspace, module = self.make_workspace(input_image)
        module.shape.value = cpmc.SH_RECTANGLE
        module.horizontal_limits.set_value((1,9))
        module.vertical_limits.set_value((0,8))
        module.remove_rows_and_columns.value = cpmc.RM_EDGES
        module.run(workspace)
        output_image = workspace.image_set.get_image(OUTPUT_IMAGE)
        self.assertTrue(np.all(output_image.pixel_data == expected_image))

    def test_04_05_crop_with_rectangle_unbounded_ymax(self):
        x,y = np.mgrid[0:10,0:10]
        input_image = x/100.0 + y/10.0
        expected_image = input_image[2:,1:9]
        workspace, module = self.make_workspace(input_image)
        module.shape.value = cpmc.SH_RECTANGLE
        module.horizontal_limits.set_value((1,9))
        module.vertical_limits.set_value((2,"end"))
        module.remove_rows_and_columns.value = cpmc.RM_EDGES
        module.run(workspace)
        output_image = workspace.image_set.get_image(OUTPUT_IMAGE)
        self.assertTrue(np.all(output_image.pixel_data == expected_image))
        
    def test_05_01_crop_image_plate_fixup(self):
        x,y = np.mgrid[0:10,0:10]
        input_image = x/100.0 + y/10.0
        crop_image = np.zeros((10,10),bool)
        crop_image[2:,1:9] = True
        crop_image[1,(1,4)] = True # A rough edge to be cropped
        expected_image = input_image[2:,1:9]
        workspace, module = self.make_workspace(input_image,
                                                crop_image = crop_image)
        module.shape.value = cpmc.SH_IMAGE
        module.horizontal_limits.set_value((0,"end"))
        module.vertical_limits.set_value((0,"end"))
        module.remove_rows_and_columns.value = cpmc.RM_EDGES
        module.use_plate_fix.value = True;
        module.run(workspace)
        output_image = workspace.image_set.get_image(OUTPUT_IMAGE)
        self.assertTrue(np.all(output_image.pixel_data == expected_image))
    
    def test_05_02_crop_image_plate_fixup_with_rectangle(self):
        x,y = np.mgrid[0:10,0:10]
        input_image = x/100.0 + y/10.0
        crop_image = np.zeros((10,10),bool)
        crop_image[1:,1:9] = True
        expected_image = input_image[2:,1:9]
        workspace, module = self.make_workspace(input_image,
                                                crop_image = crop_image)
        module.shape.value = cpmc.SH_IMAGE
        module.horizontal_limits.set_value((0,"end"))
        module.vertical_limits.set_value((2,"end"))
        module.remove_rows_and_columns.value = cpmc.RM_EDGES
        module.use_plate_fix.value = True;
        module.run(workspace)
        output_image = workspace.image_set.get_image(OUTPUT_IMAGE)
        self.assertTrue(np.all(output_image.pixel_data == expected_image))

    def test_06_01_load_matlab_pipeline(self):
        u64data = 'TUFUTEFCIDUuMCBNQVQtZmlsZSwgUGxhdGZvcm06IFBDV0lOLCBDcmVhdGVkIG9uOiBUdWUgRmViIDI0IDE1OjAzOjMzIDIwMDkgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAABSU0PAAAAngIAAHic7VhPb9MwFHe6dH+gqjZ2YIJLjhxKlW4LcKzYVqgEHeqqSRy9xiuW0jjKn6nbp+F7cOHIx+CDcMAuTptY6ZK4kRqqurKenvN+v+f34mc7rQMAfr8EYJvKXdor4F+rcl2JdKZfId/H9sirAhUc8fGftF9DF8MbC11DK0AemLVwvGvfksG9M3v0mZiBhXpwHDWmrReMb5DrXd6GQP74C54g6wo/IBBvoVkf3WEPE5vjOb84OvNLfMFvnXa9Ps+DIuRBpf0wMs7s22BurybkbT9iv8/7AE381xcTOPS1MfSH3xjPuxSeXYGH6ZcuHr2nqc4yjz0Bv8fxH1yE7Eg8afPYEXh2OE8fmZnwVQHP9PPmoNvJ6D8pD2cucZbJA8MXkQfGkzUPae9Txv+FZWHHQ9Lrks3foYWdJ59ZefQUnq0YzxboNAeZ4ngq+Gf6GSGuiW0Y1vf/yFNUvSbVWwe7nl8SfN510efrQqY+DL3VeKvr0vgTXW+8WSE+zz6bhD82Wo1Toxzxt1PwTwQ808+JZhNfCzx+AZDOA52HsUQcRoH4ovKQt45Ouf+y4ZQYTgEnkvEdS85zWVw7BVfU+6zEeCqgR1aD+5iCOxDiZTq2TXyHzQBaGh7D0ewWLpP3rxRdRtyifIVxijJvXTQX8ISyncKXdL8YufDeG0ILJfDlnW/R8S/Dty3whS3kq0RwsvKX+vh3Y7QO8rynpP1iWjQjlwROeXmy8iV9P8z5NLpVIGedecR8ZZUb/6v1v+7ySFm8nzFdBfH9rA3y7xufCDS7kQtAlnNAjfGo0/8aVo0TzxcRV6Has1qtJnPOtxLyksVflTbx+yQNp/LxPy9+PGe/6blWfXwdfAfxdfAKLLYPW5ntN3IjN3Ij11H+BeSfKPE='
        data = base64.b64decode(u64data)
        pipeline = cpp.Pipeline()
        pipeline.load(StringIO.StringIO(data))
        self.assertEqual(len(pipeline.modules()),4)
        self.assertTrue(all([isinstance(module,cpmc.Crop)
                             for module in pipeline.modules()[1:]]))
        module = pipeline.modules()[1]
        self.assertEqual(module.image_name.value,"OrigBlue")
        self.assertEqual(module.cropped_image_name.value,"CropBlue")
        self.assertEqual(module.shape.value,cpmc.SH_ELLIPSE)
        self.assertEqual(module.individual_or_once,cpmc.IO_FIRST)
        self.assertEqual(module.ellipse_center.x,200)
        self.assertEqual(module.ellipse_center.y,500)
        self.assertEqual(module.ellipse_x_radius.value,400)
        self.assertEqual(module.ellipse_y_radius.value,200)
        self.assertTrue(module.remove_rows_and_columns)
        
        module = pipeline.modules()[2]
        self.assertEqual(module.image_name.value,"OrigGreen")
        self.assertEqual(module.cropped_image_name.value,"CropGreen")
        self.assertEqual(module.cropping_mask_source.value,"CropBlue")
        self.assertEqual(module.shape.value,cpmc.SH_CROPPING)
        self.assertFalse(module.use_plate_fix.value)
        self.assertTrue(module.remove_rows_and_columns.value)

        module = pipeline.modules()[3]
        self.assertEqual(module.image_name.value,"OrigRed")
        self.assertEqual(module.cropped_image_name.value,"CropRed")
        self.assertEqual(module.shape.value,cpmc.SH_CROPPING)
        self.assertEqual(module.cropping_mask_source.value,"CropBlue")
        self.assertFalse(module.use_plate_fix.value)
        self.assertTrue(module.remove_rows_and_columns.value)
                