'''<b>DefineGrid:</b>
Produces a grid of desired specifications either manually, or
automatically based on previously identified objects. The grid can then
be used to make measurements (using Identify Objects in Grid) or to
display text information (using Display Grid Info) within each
compartment of the grid.
<hr>

This module defines the location of a grid that can be used by modules
downstream. When used in combination with <b>IdentifyObjectsInGrid</b>, it
allows the measurement of the size, shape, intensity and texture of each
object in a grid. The grid is defined by the location of marker spots
(control spots) in the grid, which are either indicated manually or are
found automatically using previous modules in the pipeline.

If you are using images of plastic plates, it may be useful to precede
this module with an IdentifyPrimAutomatic module to find the plastic
plate, followed by a Crop module to remove the plastic edges of the
plate, so that the grid can be defined within the smooth portion of the
plate only. If the plates are not centered in exactly the same position
from one image to the next, this allows the plates to be identified
automatically and then cropped so that the interior of the plates, upon
which the grids will be defined, are always in precise alignment with
each other. 

Features measured:
XLocationOfLowestXSpot
YLocationOfLowestYSpot
XSpacing
YSpacing
Rows
Columns
TotalHeight
TotalWidth
LeftOrRightNum
TopOrBottomNum
RowsOrColumnsNum
The last three are related to the questions the module ask you about the
grid.

See also: <b>IdentifyObjectsInGrid</b>
'''
#CellProfiler is distributed under the GNU General Public License.
#See the accompanying file LICENSE for details.
#
#Developed by the Broad Institute
#Copyright 2003-2009
#
#Please see the AUTHORS file for credits.
#
#Website: http://www.cellprofiler.org


__version__="$Revision$"

import numpy as np

import cellprofiler.cpgridinfo as cpg
import cellprofiler.cpmodule as cpm
import cellprofiler.cpimage as cpi
import cellprofiler.measurements as cpmeas
import cellprofiler.settings as cps
from cellprofiler.cpmath.cpmorphology import centers_of_labels

NUM_TOP_LEFT = "Top left"
NUM_BOTTOM_LEFT = "Bottom left"
NUM_TOP_RIGHT = "Top right"
NUM_BOTTOM_RIGHT = "Bottom right"
NUM_BY_ROWS = "Rows"
NUM_BY_COLUMNS = "Columns"

EO_EACH = "Each cycle"
EO_ONCE = "Once"

AM_AUTOMATIC = "Automatic"
AM_MANUAL = "Manual"

MAN_MOUSE = "Mouse"
MAN_COORDINATES = "Coordinates"

FAIL_NO = "No"
FAIL_ANY_PREVIOUS = "Any Previous"
FAIL_FIRST = "The First"

'''The module dictionary keyword of the first or most recent good gridding'''
GOOD_GRIDDING = "GoodGridding"

'''Measurement category for this module'''
M_CATEGORY = 'DefinedGrid'
'''Feature name of top left spot x coordinate'''
F_X_LOCATION_OF_LOWEST_X_SPOT = "XLocationOfLowestXSpot"
'''Feature name of top left spot y coordinate'''
F_Y_LOCATION_OF_LOWEST_Y_SPOT = "YLocationOfLowestYSpot"
'''Feature name of x distance between spots'''
F_X_SPACING = "XSpacing"
'''Feature name of y distance between spots'''
F_Y_SPACING = "YSpacing"
'''Feature name of # of rows in grid'''
F_ROWS = "Rows"
'''Feature name of # of columns in grid'''
F_COLUMNS = "Columns"

class DefineGrid(cpm.CPModule):
    
    module_name = "DefineGrid"
    variable_revision_number = 1
    category = "Other"
    
    def create_settings(self):
        """Create your settings by subclassing this function
        
        create_settings is called at the end of initialization.
        """
        self.grid_image = cps.GridNameProvider("Grid name:", doc="""
            This is the name for the grid. You can use this name to
            retrieve the grid in subsequent modules.""")
        self.grid_rows = cps.Integer("Number of rows:",8,1)
        self.grid_columns = cps.Integer("Number of columns:",12,1)
        self.origin = cps.Choice("Where is the first spot?",
                                 [NUM_TOP_LEFT, NUM_BOTTOM_LEFT,
                                  NUM_TOP_RIGHT, NUM_BOTTOM_RIGHT], doc="""
            Grid cells are numbered consecutively; this option picks the
            origin for the numbering system and the direction for numbering.
            For instance, if you choose "Top left", the top left cell is
            cell # 1 and cells to the right and bottom are indexed with
            larger numbers.""")
        self.ordering = cps.Choice("Order by:", [NUM_BY_ROWS, NUM_BY_COLUMNS],
                                   doc="""
            Grid cells can either be numbered by rows, then columns or by
            columns, then rows. For instance, you might ask to start numbering
            a 96-well plate at the top left using the "Where is the first spot?"
            setting. If you choose, "Rows", then well A01 will be assigned
            the index, "1", B01, the index "2" and so on up to H01 which
            receives the index, "8". Well A02 will be assigned the index, "9".
            Conversely, if you choose, "Columns", well A02 will be assigned,
            "2", well A12 will be assigned "12" and well B01 will be assigned
            "13".""")
        self.each_or_once = cps.Choice(
            "Would you like to define a new grid for each image cycle, "
            "or define a grid once and use it for all images?",
            [EO_EACH, EO_ONCE], doc="""
            If all of your images are perfectly aligned with each
            other (due to very consistent image acquisition, consistent 
            grid location within the plate, and/or automatic cropping 
            precisely within each plate), you can define the location of the 
            marker spots ONCE for all of the image
            cycles; if the location of the grid will vary from one image cycle 
            to the next then you should define the location of the marker spots 
            for EACH CYCLE independently.""")
        self.auto_or_manual = cps.Choice(
            "Would you like to define the grid automatically, based on objects "
            "you have identified in a previous module?",
            [AM_AUTOMATIC, AM_MANUAL], doc="""
            This setting controls how the grid is defined:

            <ul><li>% <b>Manual mode</b>: In manual mode, you manually indicate
            known locations of marker spots in the grid and have the rest of 
            the positions calculated from those marks, no matter what the 
            image itself looks like. You can define the grid either by
            clicking on the image with a mouse or by entering coordinates.
            </li>
            <li><a> name="AutomaticMode"</a><b>Automatic mode</b></a>: 
            If you would like the grid to be defined
            automatically, an IdentifyPrimAutomatic module must be run prior to 
            this module to identify the objects which will be used to define 
            the grid. The left-most, right-most, top-most, and bottom-most 
            object will be used to define the edges of the grid and the rows 
            and columns will be evenly spaced between these edges. Note that 
            automatic mode requires that the incoming objects are nicely 
            defined - for example, if there is an object at the edge of the 
            images that is not really an object that ought to be in the grid, 
            a skewed grid will result. You might wish to use a 
            <b>FilterByObjectMeasurement</b> module to clean up badly 
            identified objects prior to defining the grid. If the spots are 
            slightly out of alignment with each other from one image cycle to 
            the next, this allows the identification to be a bit flexible and 
            adapt to the real location of the spots.</li></ul>""")
        self.object_name = cps.ObjectNameSubscriber(
            "What are the previously identified objects you want to use to "
            "define the grid?", "None",doc="""
            Use this setting to specify the name of the objects that will
            be used to define the grid. See the documentation for
            <a href="AutomaticMode">Automatic mode</a> in the automatic or
            manual setting's documentation.""")
        self.manual_choice = cps.Choice(
            "Do you want to define the grid using the mouse or by entering "
            "the coordinates of the cells?",[MAN_MOUSE, MAN_COORDINATES],
            doc="""You can either use the user interface to define the grid
            or you can enter the coordinates of the spots:
            
            <ul><li><b>Mouse</b>: The user interface displays the image of
            your grid. You will be asked to click in the center of two of
            the grid cells and specify the row and column for each. The
            grid coordinates will be computed from this information.</li>
            <li><b>Coordinates</b>: This option lets you enter the X and Y
            coordinates of the grid cells directly. You can display an image
            of your grid to find the locations of the centers of the cells,
            then enter the X and Y position and cell coordinates for each
            of two cells.</li></ul>""")
        self.manual_image = cps.ImageNameSubscriber(
            "What image do you want to display when defining the grid?",
            "None", doc="""This setting lets you choose the image to display 
            in the grid definition user interface.""")
        self.first_spot_coordinates = cps.Coordinates(
            "Enter the coordinates of the first cell on your grid",
            (0,0),doc="""This setting defines the location of the first of
            two cells in your grid. You should enter the coordinates of
            the center of the cell. You can display an image of your grid
            and use the <i>Show pixel data</i> tool to determine the
            coordinates of the center of your cell.""")
        self.first_spot_row = cps.Integer(
            "What is this cell's row number?", 1, minval=1,
            doc="""Enter the row index for the first cell here. Rows are
            numbered starting at the origin. For instance, if you chose
            "Top left" as your origin, well A01 will be row number 1
            and H01 will be row number 8. If you chose "Bottom left",
            A01 will be row number 8 and H01 will be row number 12.""")
        self.first_spot_col = cps.Integer(
            "What is this cell's column number?",1, minval=1,
            doc="""Enter the column index for the first cell here. Columns
            are numbered starting at the origin. For instance, if you chose
            "Top left" as your origin, well A01 will be column number 1
            and A12 will be column number 12. If you chose "Top right",
            A01 and A12 will be 12 and 1 respectively.""")
        self.second_spot_coordinates = cps.Coordinates(
            "Enter the coordinates of the second cell on your grid",
            (0,0),doc="""This setting defines the location of the second of
            two cells in your grid. You should enter the coordinates of
            the center of the cell. You can display an image of your grid
            and use the <i>Show pixel data</i> tool to determine the
            coordinates of the center of your cell.""")
        self.second_spot_row = cps.Integer(
            "What is this cell's row number?", 1, minval=1,
            doc="""Enter the row index for the second cell here. Rows are
            numbered starting at the origin. For instance, if you chose
            "Top left" as your origin, well A01 will be row number 1
            and H01 will be row number 8. If you chose "Bottom left",
            A01 will be row number 8 and H01 will be row number 12.""")
        self.second_spot_col = cps.Integer(
            "What is this cell's column number?",1, minval=1,
            doc="""Enter the column index for the second cell here. Columns
            are numbered starting at the origin. For instance, if you chose
            "Top left" as your origin, well A01 will be column number 1
            and A12 will be column number 12. If you chose "Top right",
            A01 and A12 will be 12 and 1 respectively.""")
        self.wants_image = cps.Binary(
            "Do you want to save an image of the grid?", False,
            doc="""This module can create an annotated image of the grid
            which can be saved using the <b>SaveImages</b> module. Check
            this box if you want to save the annotated image.
            """)
        self.display_image_name = cps.ImageNameSubscriber(
            "Display image name:", cps.LEAVE_BLANK, can_be_blank = True,
            doc = """Enter the name of the image that should be used as
            the background for annotations (grid lines and grid indexes).
            This image will be used for the figure and for the saved image.""")
        self.save_image_name = cps.ImageNameProvider(
            "Output image name:", "Grid",doc="""
            Enter the name you want to use for the output image. You can
            save this image using the <b>SaveImages</b> module.""")
        self.failed_grid_choice = cps.Choice(
            "If the gridding fails, would you like to use a previous grid "
            "that worked?", [FAIL_NO, FAIL_ANY_PREVIOUS, FAIL_FIRST],
            doc="""This setting allows you to control how the module responds
            to errors:
            
            <ul><li><b>No</b>: The module will stop the pipeline if gridding
            fails.</li>
            <li><b>Any Previous</b>: The module will use the gridding from
            the most recent successful gridding.</li>
            <li><b>The First</b>: The module will use the gridding from
            the first gridding.</li></ul>
            
            The pipeline will stop in all cases if the first gridding fails.""")
        
    def settings(self):
        """Return the settings to be loaded or saved to/from the pipeline
        
        These are the settings (from cellprofiler.settings) that are
        either read from the strings in the pipeline or written out
        to the pipeline. The settings should appear in a consistent
        order so they can be matched to the strings in the pipeline.
        """
        return [self.grid_image, self.grid_rows, self.grid_columns,
                self.origin, self.ordering, self.each_or_once, 
                self.auto_or_manual, self.object_name, self.manual_choice,
                self.manual_image, self.first_spot_coordinates,
                self.first_spot_row, self.first_spot_col,
                self.second_spot_coordinates, self.second_spot_row,
                self.second_spot_col, self.wants_image, 
                self.save_image_name,
                self.display_image_name, self.failed_grid_choice]
    
    def visible_settings(self):
        """The settings that are visible in the UI
        """
        result = [self.grid_image, self.grid_rows, self.grid_columns,
                  self.origin, self.ordering, self.each_or_once,
                  self.auto_or_manual]
        if self.auto_or_manual == AM_AUTOMATIC:
            result += [self.object_name, self.failed_grid_choice]
        elif self.auto_or_manual == AM_MANUAL:
            result += [self.manual_choice]
            if self.manual_choice == MAN_MOUSE:
                result += [self.manual_image]
            elif self.manual_choice == MAN_COORDINATES:
                result += [self.first_spot_coordinates,
                           self.first_spot_row, self.first_spot_col,
                           self.second_spot_coordinates,
                           self.second_spot_row, self.second_spot_col]
            else:
                raise NotImplementedError("Unknown manual choice: %s"%
                                          self.manual_choice.value)
        else:
            raise NotImplementedError("Unknown automatic / manual choice: %s" %
                                      self.auto_or_manual.value)
        result += [self.wants_image]
        if self.wants_image:
            result+= [self.save_image_name]
        result += [self.display_image_name]
        return result
    
    def run(self, workspace):
        """Run the module 
        
        workspace    - The workspace contains
            pipeline     - instance of cpp for this run
            image_set    - the images in the image set being processed
            object_set   - the objects (labeled masks) in this image set
            measurements - the measurements for this run
            frame        - the parent frame to whatever frame is created. None means don't draw.
        """
        if (self.each_or_once == EO_ONCE and 
            self.get_good_gridding(workspace) is not None):
            gridding = self.get_good_gridding(workspace)
        if self.auto_or_manual == AM_AUTOMATIC:
            gridding = self.run_automatic(workspace)
        elif self.manual_choice == MAN_COORDINATES:
            gridding = self.run_coordinates(workspace)
        elif self.manual_choice == MAN_MOUSE:
            gridding = self.run_mouse(workspace)
        self.set_good_gridding(workspace, gridding)
        workspace.set_grid(self.grid_image.value, gridding)
        #
        # Save measurements
        #
        self.add_measurement(workspace, F_X_LOCATION_OF_LOWEST_X_SPOT, 
                             gridding.x_location_of_lowest_x_spot)
        self.add_measurement(workspace, F_Y_LOCATION_OF_LOWEST_Y_SPOT,
                             gridding.y_location_of_lowest_y_spot)
        self.add_measurement(workspace, F_ROWS, gridding.rows)
        self.add_measurement(workspace, F_COLUMNS, gridding.columns)
        self.add_measurement(workspace, F_X_SPACING, gridding.x_spacing)
        self.add_measurement(workspace, F_Y_SPACING, gridding.y_spacing)
        if self.wants_image:
            from cellprofiler.gui.cpfigure import figure_to_image
            import matplotlib
            import matplotlib.backends.backend_wxagg
            figure = matplotlib.figure.Figure()
            axes = figure.add_axes((0,0,1,1),frameon=False)
            self.display(workspace, gridding, axes)
            axes.axison=False
            ai = axes.images[0]
            size = 2*np.array(ai.get_size(),float) / float(figure.get_dpi())
            figure.set_size_inches(size[1],size[0])
            canvas = matplotlib.backends.backend_wxagg.FigureCanvasAgg(figure)
            pixel_data = figure_to_image(figure)
            image = cpi.Image(pixel_data)
            workspace.image_set.add(self.save_image_name.value, image)
        if workspace.frame is not None:
            self.display(workspace, gridding)

    def run_automatic(self, workspace):
        '''Automatically define a grid based on objects

        Returns a CPGridInfo object
        '''
        objects = workspace.object_set.get_objects(self.object_name.value)
        centroids = centers_of_labels(objects.segmented)
        if centroids.shape[1] < 2:
            #
            # Failed if too few objects
            #
            if self.failed_grid_choice == FAIL_NO:
                raise RuntimeError("%s has too few grid cells"%
                                   self.object_name.value)
            else:
                result = self.get_good_gridding(workspace)
                if result is None:
                    raise RuntimeError("%s has too few grid cells and there is no previous successful grid"%
                                       self.object_name.value)
                return result
        #
        # Artificially swap these to match the user's orientation
        #
        first_row, second_row = (1,self.grid_rows.value)
        if self.origin in (NUM_BOTTOM_LEFT, NUM_BOTTOM_RIGHT):
            first_row, second_row = (second_row, first_row)
        first_column, second_column = (1, self.grid_columns.value)
        if self.origin in (NUM_TOP_RIGHT, NUM_BOTTOM_RIGHT):
            first_column, second_column = (second_column, first_column)
        first_x = np.min(centroids[1,:])
        first_y = np.min(centroids[0,:])
        second_x = np.max(centroids[1,:])
        second_y = np.max(centroids[0,:])
        return self.build_grid_info(first_x, first_y, first_row, first_column,
                                    second_x, second_y, second_row, second_column)
    
    def run_coordinates(self, workspace):
        '''Define a grid based on the coordinates of two points
        
        Returns a CPGridInfo object
        '''
        return self.build_grid_info(self.first_spot_coordinates.x,
                                    self.first_spot_coordinates.y,
                                    self.first_spot_row.value,
                                    self.first_spot_col.value,
                                    self.second_spot_coordinates.x,
                                    self.second_spot_coordinates.y,
                                    self.second_spot_row.value,
                                    self.second_spot_col.value)
    
    def run_mouse(self, workspace):
        '''Define a grid by running the UI
        
        Returns a CPGridInfo object
        '''
        import matplotlib
        import matplotlib.backends.backend_wxagg as backend
        import wx
        from wx.lib.intctrl import IntCtrl
        #
        # Make up a dialog box. It has the following structure:
        #
        # Dialog:
        #    top_sizer:
        #        Canvas
        #            Figure
        #               Axis
        #        control_sizer
        #            first_sizer
        #               first_row
        #               first_col
        #            second_sizer
        #               second_row
        #               second_col
        #            button_sizer
        #               Redisplay
        #               OK
        #               cancel
        #
        figure = matplotlib.figure.Figure()
        axes = figure.add_subplot(1,1,1)
        frame = wx.Dialog(workspace.frame,title="Select grid cells")
        top_sizer = wx.BoxSizer(wx.VERTICAL)
        frame.SetSizer(top_sizer)
        canvas = backend.FigureCanvasWxAgg(frame,-1,figure)
        top_sizer.Add(canvas, 1, wx.EXPAND)
        top_sizer.Add(wx.StaticText(frame, -1,
            "Select the center of a grid cell with the left mouse button.\n"),
                      0, wx.EXPAND|wx.ALL, 5)
        control_sizer = wx.BoxSizer(wx.HORIZONTAL)
        top_sizer.Add(control_sizer,0,wx.EXPAND|wx.ALL, 5)
        FIRST_CELL = "First cell"
        SECOND_CELL = "Second cell"
        cell_choice = wx.RadioBox(frame, label="Choose current cell",
                                  choices = [FIRST_CELL, SECOND_CELL],
                                  style=wx.RA_VERTICAL)
        control_sizer.Add(cell_choice)
        #
        # Text boxes for the first cell's row and column
        #
        first_sizer = wx.GridBagSizer(2,2)
        control_sizer.Add(first_sizer, 1, wx.EXPAND|wx.ALL, 5)
        first_sizer.Add(wx.StaticText(frame, -1, "First cell column:"),
                        wx.GBPosition(0,0), flag=wx.EXPAND)
        first_column = IntCtrl(frame, -1, 1, min=1, max=self.grid_columns.value)
        first_sizer.Add(first_column, wx.GBPosition(0,1),flag=wx.EXPAND)
        first_sizer.Add(wx.StaticText(frame, -1, "First cell row:"),
                        wx.GBPosition(1,0),flag = wx.EXPAND)
        first_row = IntCtrl(frame, -1, 1, min=1, max=self.grid_rows.value)
        first_sizer.Add(first_row, wx.GBPosition(1,1), flag=wx.EXPAND)
        first_sizer.Add(wx.StaticText(frame,-1,"X:"), wx.GBPosition(0,2))
        first_x = IntCtrl(frame, -1, 100, min=1)
        first_sizer.Add(first_x, wx.GBPosition(0,3))
        first_sizer.Add(wx.StaticText(frame,-1,"Y:"), wx.GBPosition(1,2))
        first_y = IntCtrl(frame, -1, 100, min=1)
        first_sizer.Add(first_y, wx.GBPosition(1,3))
        #
        # Text boxes for the second cell's row and column
        #
        second_sizer = wx.GridBagSizer(2,2)
        control_sizer.Add(second_sizer, 1, wx.EXPAND|wx.ALL, 5)
        second_sizer.Add(wx.StaticText(frame, -1, "Second cell column:"),
                        wx.GBPosition(0,0), flag=wx.EXPAND)
        second_column = IntCtrl(frame, -1, self.grid_columns.value,
                                min=1, max=self.grid_columns.value)
        second_sizer.Add(second_column, wx.GBPosition(0,1),flag=wx.EXPAND)
        second_sizer.Add(wx.StaticText(frame, -1, "Second cell row:"),
                        wx.GBPosition(1,0),flag = wx.EXPAND)
        second_row = IntCtrl(frame, -1, self.grid_rows.value, 
                             min=1, max=self.grid_rows.value)
        second_sizer.Add(second_row, wx.GBPosition(1,1), flag=wx.EXPAND)
        second_sizer.Add(wx.StaticText(frame,-1,"X:"), wx.GBPosition(0,2))
        second_x = IntCtrl(frame, -1, 200, min=1)
        second_sizer.Add(second_x, wx.GBPosition(0,3))
        second_sizer.Add(wx.StaticText(frame,-1,"Y:"), wx.GBPosition(1,2))
        second_y = IntCtrl(frame, -1, 200, min=1)
        second_sizer.Add(second_y, wx.GBPosition(1,3))
        #
        # Buttons
        #
        button_sizer = wx.BoxSizer(wx.VERTICAL)
        control_sizer.Add(button_sizer, 0, wx.EXPAND |wx.ALL, 5)
        redisplay_button = wx.Button(frame, -1, "Redisplay")
        button_sizer.Add(redisplay_button)
        button_sizer.Add(wx.Button(frame,wx.OK, "OK"))
        button_sizer.Add(wx.Button(frame,wx.CANCEL, "Cancel"))
        status = [wx.OK]
        gridding = [None]
        def redisplay(event):
            gridding[0] = self.build_grid_info(int(first_x.Value),
                                               int(first_y.Value),
                                               int(first_row.Value),
                                               int(first_column.Value),
                                               int(second_x.Value),
                                               int(second_y.Value),
                                               int(second_row.Value),
                                               int(second_column.Value))
            self.display(workspace, gridding[0], axes)
            canvas.draw()
        def cancel(event):
            status[0] = wx.CANCEL
            frame.SetReturnCode(wx.CANCEL)
            frame.Close(True)
        def ok(event):
            status[0] = wx.OK
            frame.SetReturnCode(wx.OK)
            frame.Close(True)
            
        def button_release(event):
            if event.inaxes == axes:
                if cell_choice.Selection == 0:
                    first_x.Value = str(int(event.xdata))
                    first_y.Value = str(int(event.ydata))
                    cell_choice.Selection = 1
                else:
                    second_x.Value = str(int(event.xdata))
                    second_y.Value = str(int(event.ydata))
                    cell_choice.Selection = 0
                redisplay(None)
        redisplay(None)
        frame.Fit()
        frame.Bind(wx.EVT_BUTTON, redisplay, redisplay_button)
        frame.Bind(wx.EVT_BUTTON, cancel, id=wx.CANCEL)
        frame.Bind(wx.EVT_BUTTON, ok, id=wx.OK)
        canvas.mpl_connect("button_release_event", button_release)
        frame.ShowModal()
        if status[0] != wx.OK:
            raise RuntimeError("Pipeline aborted during grid editing")
        return gridding[0]
    
    def get_feature_name(self, feature):
        return '_'.join((M_CATEGORY, self.grid_image.value, feature))
    
    def add_measurement(self, workspace, feature, value):
        '''Add an image measurement using our category and grid
        
        feature - the feature name of the measurement to add
        value - the value for the measurement
        '''
        feature_name = self.get_feature_name(feature)
        workspace.measurements.add_image_measurement(feature_name, value)
        
    def build_grid_info(self, first_x, first_y, first_row, first_col,
                        second_x, second_y, second_row, second_col):
        '''Populate and return a CPGridInfo based on two cell locations'''
        first_row, first_col =\
                  self.canonical_row_and_column(first_row, first_col)
        second_row, second_col =\
                  self.canonical_row_and_column(second_row, second_col)
        gridding = cpg.CPGridInfo()
        gridding.x_spacing = (float(first_x-second_x) / 
                              float(first_col - second_col))
        gridding.y_spacing = (float(first_y-second_y) / 
                              float(first_row - second_row))
        gridding.x_location_of_lowest_x_spot = int(first_x - first_col *
                                                   gridding.x_spacing)
        gridding.y_location_of_lowest_y_spot = int(first_y - first_row *
                                                   gridding.y_spacing)
        gridding.rows = self.grid_rows.value
        gridding.columns = self.grid_columns.value
        gridding.left_to_right = (self.origin in (NUM_TOP_LEFT, NUM_BOTTOM_LEFT))
        gridding.top_to_bottom = (self.origin in (NUM_TOP_LEFT, NUM_TOP_RIGHT))
        gridding.total_width = gridding.x_spacing * gridding.columns
        gridding.total_height = gridding.y_spacing * gridding.rows
        
        line_left_x = (gridding.x_location_of_lowest_x_spot - 
                       round(gridding.x_spacing/2))
        line_top_y = (gridding.y_location_of_lowest_y_spot - 
                      round(gridding.y_spacing/2))
        #
        # Make a 2 x columns array of x-coordinates of vertical lines (x0=x1)
        #
        gridding.vert_lines_x = np.tile((np.arange(gridding.columns + 1) *
                                         gridding.x_spacing + line_left_x),
                                        (2,1)).astype(int)
        #
        # Make a 2 x rows array of y-coordinates of horizontal lines (y0=y1)
        #
        gridding.horiz_lines_y = np.tile((np.arange(gridding.rows + 1) *
                                          gridding.y_spacing + line_top_y),
                                         (2,1)).astype(int)
        #
        # Make a 2x columns array of y-coordinates of vertical lines
        # all of which are from line_top_y to the bottom
        #
        gridding.vert_lines_y = np.transpose(np.tile(
            (line_top_y, line_top_y + gridding.total_height),
            (gridding.columns+1, 1))).astype(int)
        gridding.horiz_lines_x = np.transpose(np.tile(
            (line_left_x, line_left_x + gridding.total_width),
            (gridding.rows+1, 1))).astype(int)
        gridding.x_locations = (gridding.x_location_of_lowest_x_spot +
                                np.arange(gridding.columns) * 
                                gridding.x_spacing).astype(int)
        gridding.y_locations = (gridding.y_location_of_lowest_y_spot +
                                np.arange(gridding.rows) * 
                                gridding.y_spacing).astype(int)
        #
        # The spot table has the numbering for each spot in the grid
        #
        gridding.spot_table = np.arange(gridding.rows * gridding.columns)+1
        if self.ordering == NUM_BY_COLUMNS:
            gridding.spot_table.shape = (gridding.rows, gridding.columns)
        else:
            gridding.spot_table.shape = (gridding.columns, gridding.rows)
            gridding.spot_table = np.transpose(gridding.spot_table)
        if self.origin in (NUM_BOTTOM_LEFT, NUM_BOTTOM_RIGHT):
            # Flip top and bottom
            gridding.spot_table = gridding.spot_table[::-1,:]
        if self.origin in (NUM_TOP_RIGHT, NUM_BOTTOM_RIGHT):
            # Flip left and right
            gridding.spot_table = gridding.spot_table[:,::-1]
        return gridding
        
    def canonical_row_and_column(self, row, column):
        '''Convert a row and column as entered by the user to canonical form
        
        The user might select something other than the bottom left as the
        origin of their coordinate space. This method returns a row and
        column using a numbering where the top left corner is 0,0
        '''
        if self.origin in (NUM_BOTTOM_LEFT, NUM_BOTTOM_RIGHT):
            row = self.grid_rows.value - row
        else:
            row -=1
        if self.origin in (NUM_TOP_RIGHT, NUM_BOTTOM_RIGHT):
            column = self.grid_columns.value - column
        else:
            column -= 1
        return (row, column)
        
    def display(self, workspace, gridding, axes=None):
        '''Display the grid in a figure'''
        import matplotlib
        
        if axes is None:
            figure = workspace.create_or_find_figure(subplots=(1,1))
            figure.clf()
            axes = figure.subplot(0,0)
        else:
            axes.cla()
        assert isinstance(axes, matplotlib.axes.Axes)
        assert isinstance(gridding, cpg.CPGridInfo)
        #
        # Get an image to draw on or get a blank image
        #
        if self.display_image_name == cps.LEAVE_BLANK:
            image = np.zeros((gridding.total_height + 
                              2 * gridding.y_location_of_lowest_y_spot,
                              gridding.total_width +
                              2 * gridding.x_location_of_lowest_x_spot,3))
        else:
            image = workspace.image_set.get_image(self.display_image_name.value)
            image = image.pixel_data
            if image.ndim == 2:
                image = np.tile(image,(3,1,1))
                image = np.transpose(image, (1,2,0))
        #
        # draw the image on the figure
        #
        axes.imshow(image)
        #
        # Draw lines
        #
        for xc, yc in ((gridding.horiz_lines_x, gridding.horiz_lines_y),
                       (gridding.vert_lines_x, gridding.vert_lines_y)):
            for i in range(xc.shape[1]):
                line = matplotlib.lines.Line2D(xc[:,i],yc[:,i],
                                               color="red")
                axes.add_line(line)
        #
        # Draw labels
        #
        for row in range(gridding.rows):
            for column in range(gridding.columns):
                label = str(gridding.spot_table[row,column])
                x = gridding.x_locations[column]
                y = gridding.y_locations[row]
                text = matplotlib.text.Text(x,y,label,
                                            horizontalalignment='center',
                                            verticalalignment='center',
                                            size='smaller',
                                            color="black",
                                            bbox= dict(facecolor = "white",
                                                       alpha = .5,
                                                       edgecolor = "black"))
                axes.add_artist(text)
    
    def get_good_gridding(self, workspace):
        '''Get either the first gridding or the most recent successful gridding'''
        d = self.get_dictionary(workspace.image_set_list)
        return d.get(GOOD_GRIDDING, None)
    
    def set_good_gridding(self, workspace, gridding):
        '''Set the gridding to use upon failure'''
        d = self.get_dictionary(workspace.image_set_list)
        if (self.failed_grid_choice == FAIL_ANY_PREVIOUS or
            not d.has_key(GOOD_GRIDDING)):
            d[GOOD_GRIDDING] =gridding
    
    def upgrade_settings(self,setting_values,variable_revision_number,
                         module_name,from_matlab):
        '''Adjust setting values if they came from a previous revision
        
        setting_values - a sequence of strings representing the settings
                         for the module as stored in the pipeline
        variable_revision_number - the variable revision number of the
                         module at the time the pipeline was saved. Use this
                         to determine how the incoming setting values map
                         to those of the current module version.
        module_name - the name of the module that did the saving. This can be
                      used to import the settings from another module if
                      that module was merged into the current module
        from_matlab - True if the settings came from a Matlab pipeline, False
                      if the settings are from a CellProfiler 2.0 pipeline.
        
        Overriding modules should return a tuple of setting_values,
        variable_revision_number and True if upgraded to CP 2.0, otherwise
        they should leave things as-is so that the caller can report
        an error.
        '''
        if from_matlab and variable_revision_number == 3:
            grid_name, rows_cols, left_or_right, top_or_bottom,\
            rows_or_columns, each_or_once, auto_or_manual, object_name,\
            control_spot_mode, image_name, horz_vert_offset,\
            distance_units, horz_vert_spacing, control_spot,\
            rgb_name, failed_grid_choice = setting_values
            try:
                rows, cols = [int(x.strip()) for x in rows_cols.split(',')]
            except:
                rows, cols = (8,12)
            try:
                x_spacing, y_spacing = [int(x.strip()) 
                                        for x in horz_vert_spacing.split(',')]
            except:
                x_spacing, y_spacing = (10,10)
            try:
                off_x, off_y = [int(x.strip()) for x in horz_vert_offset.split(',')]
                first_x, first_y = [int(x.strip()) for x in control_spot.split(',')]
                first_x += off_x
                first_y += off_y
            except:
                first_x, first_y = (0,0)
            second_x = first_x + (cols - 1) * x_spacing
            second_y = first_y + (rows - 1)* y_spacing

            origin = top_or_bottom + " " + left_or_right.lower()
            setting_values = [
                grid_name, 
                str(rows),
                str(cols),
                origin,
                rows_or_columns,
                each_or_once,
                auto_or_manual,
                object_name,
                control_spot_mode,
                image_name,
                "%d,%d"%(first_x, first_y),
                "1","1",
                "%d,%d"%(second_x, second_y),
                str(rows),str(cols),
                cps.NO if rgb_name == cps.DO_NOT_USE else cps.YES,
                rgb_name,
                image_name, failed_grid_choice]
            from_matlab = False
            variable_revision_number = 1
        return setting_values, variable_revision_number, from_matlab
    
    def get_measurement_columns(self, pipeline):
        '''Return a sequence describing the measurement columns needed by this module
        
        This call should return one element per image or object measurement
        made by the module during image set analysis. The element itself
        is a 3-tuple:
        first entry: either one of the predefined measurement categories,
                     {"Image", "Experiment" or "Neighbors" or the name of one
                     of the objects.}
        second entry: the measurement name (as would be used in a call 
                      to add_measurement)
        third entry: the column data type (for instance, "varchar(255)" or
                     "float")
        '''
        return [(cpmeas.IMAGE, self.get_feature_name(F_ROWS), cpmeas.COLTYPE_INTEGER),
                (cpmeas.IMAGE, self.get_feature_name(F_COLUMNS), cpmeas.COLTYPE_INTEGER),
                (cpmeas.IMAGE, self.get_feature_name(F_X_SPACING), cpmeas.COLTYPE_FLOAT),
                (cpmeas.IMAGE, self.get_feature_name(F_Y_SPACING), cpmeas.COLTYPE_FLOAT),
                (cpmeas.IMAGE, self.get_feature_name(F_X_LOCATION_OF_LOWEST_X_SPOT), cpmeas.COLTYPE_FLOAT),
                (cpmeas.IMAGE, self.get_feature_name(F_Y_LOCATION_OF_LOWEST_Y_SPOT), cpmeas.COLTYPE_FLOAT)]

    def get_categories(self, pipeline,object_name):
        """Return the categories of measurements that this module produces
        
        object_name - return measurements made on this object (or 'Image' for image measurements)
        """
        if object_name == cpmeas.IMAGE:
            return [M_CATEGORY]
        return []
    
    def get_measurements(self, pipeline, object_name, category):
        if object_name == cpmeas.IMAGE and category == M_CATEGORY:
            return ['_'.join((self.grid_image.value, feature))
                    for feature in (F_ROWS, F_COLUMNS, F_X_SPACING,
                                    F_Y_SPACING, F_X_LOCATION_OF_LOWEST_X_SPOT,
                                    F_Y_LOCATION_OF_LOWEST_Y_SPOT)]
        return []
        