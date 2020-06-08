"""Implement the graphical user interface for the Logic Simulator.

Used in the Logic Simulator project to enable the user to run the simulation
or adjust the network properties.

Classes:
--------
MyGLCanvas - handles all canvas drawing operations.
Gui - configures the main window and all the widgets.
"""
import wx
import wx.glcanvas as wxcanvas
import numpy as np
import math
from OpenGL import GL, GLU, GLUT

from names import Names
from devices import Devices
from network import Network
from monitors import Monitors
from scanner import Scanner
from parse import Parser


class MyGLCanvas(wxcanvas.GLCanvas):
    """Handle all drawing operations.

    This class contains functions for drawing onto the canvas. It
    also contains handlers for events relating to the canvas.

    Parameters
    ----------
    parent: parent window.
    devices: instance of the devices.Devices() class.
    monitors: instance of the monitors.Monitors() class.

    Public methods
    --------------
    init_gl(self): Configures the OpenGL context.

    init_gl_3d(self):

    render(self): Handles all drawing operations.

    on_paint(self, event): Handles the paint event.

    on_size(self, event): Handles the canvas resize event.

    on_mouse(self, event): Handles mouse events.

    render_text(self, text, x_pos, y_pos, z_pos): Handles text drawing
                                                  operations.
    """

    def __init__(self, parent, devices, monitors):
        """Initialise canvas properties and useful variables."""
        super().__init__(parent, -1,
                         attribList=[wxcanvas.WX_GL_RGBA,
                                     wxcanvas.WX_GL_DOUBLEBUFFER,
                                     wxcanvas.WX_GL_DEPTH_SIZE, 16, 0])
        GLUT.glutInit()
        self.init = False
        self.context = wxcanvas.GLContext(self)

        # Constants for OpenGL materials and lights
        self.mat_diffuse = [0.0, 0.0, 0.0, 1.0]
        self.mat_no_specular = [0.0, 0.0, 0.0, 0.0]
        self.mat_no_shininess = [0.0]
        self.mat_specular = [0.5, 0.5, 0.5, 1.0]
        self.mat_shininess = [50.0]
        self.top_right = [1.0, 1.0, 1.0, 0.0]
        self.straight_on = [0.0, 0.0, 1.0, 0.0]
        self.no_ambient = [0.0, 0.0, 0.0, 1.0]
        self.dim_diffuse = [0.5, 0.5, 0.5, 1.0]
        self.bright_diffuse = [1.0, 1.0, 1.0, 1.0]
        self.med_diffuse = [0.75, 0.75, 0.75, 1.0]
        self.full_specular = [0.5, 0.5, 0.5, 1.0]
        self.no_specular = [0.0, 0.0, 0.0, 1.0]

        # Initialise variables for panning
        self.pan_x_3d = 0
        self.pan_y_3d = 0
        self.last_mouse_x = 0  # previous mouse x position
        self.last_mouse_y = 0  # previous mouse y position
        self.pan_x = 0
        self.pan_y = 0

        # Initialise the scene rotation matrix
        self.scene_rotate = np.identity(4, 'f')

        # Initialise variables for zooming
        self.zoom = 1

        # Offset between viewpoint and origin of the scene
        self.depth_offset = 1000

        # Bind events to the canvas
        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_SIZE, self.on_size)
        self.Bind(wx.EVT_MOUSE_EVENTS, self.on_mouse)

        # initialise variables for devices and monitors
        self.devices = devices
        self.monitors = monitors
        self.toggle = 0
        self.text_array = []
        self.signal_array = []
        self.toggle_3D = False

    def init_gl(self):
        """Configure and initialise the OpenGL context."""
        size = self.GetClientSize()
        self.SetCurrent(self.context)
        GL.glDrawBuffer(GL.GL_BACK)
        GL.glClearColor(0.0, 0.0, 0.0, 0.0)     # set to black background
        GL.glViewport(0, 0, size.width, size.height)
        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glLoadIdentity()
        GL.glOrtho(0, size.width, 0, size.height, -1, 1)
        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glLoadIdentity()
        GL.glTranslated(self.pan_x, self.pan_y, 0.0)
        GL.glScaled(self.zoom, self.zoom, self.zoom)

    def init_gl_3d(self):
        """Configure and initialise the OpenGL context."""
        size = self.GetClientSize()
        self.SetCurrent(self.context)

        GL.glViewport(0, 0, size.width, size.height)

        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glLoadIdentity()

        GLU.gluPerspective(45, size.width / size.height, 10, 10000)

        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glLoadIdentity()  # lights positioned relative to the viewer
        GL.glLightfv(GL.GL_LIGHT0, GL.GL_AMBIENT, self.no_ambient)
        GL.glLightfv(GL.GL_LIGHT0, GL.GL_DIFFUSE, self.med_diffuse)
        GL.glLightfv(GL.GL_LIGHT0, GL.GL_SPECULAR, self.no_specular)
        GL.glLightfv(GL.GL_LIGHT0, GL.GL_POSITION, self.top_right)
        GL.glLightfv(GL.GL_LIGHT1, GL.GL_AMBIENT, self.no_ambient)
        GL.glLightfv(GL.GL_LIGHT1, GL.GL_DIFFUSE, self.dim_diffuse)
        GL.glLightfv(GL.GL_LIGHT1, GL.GL_SPECULAR, self.no_specular)
        GL.glLightfv(GL.GL_LIGHT1, GL.GL_POSITION, self.straight_on)

        GL.glMaterialfv(GL.GL_FRONT, GL.GL_SPECULAR, self.mat_specular)
        GL.glMaterialfv(GL.GL_FRONT, GL.GL_SHININESS, self.mat_shininess)
        GL.glMaterialfv(GL.GL_FRONT, GL.GL_AMBIENT_AND_DIFFUSE,
                        self.mat_diffuse)
        GL.glColorMaterial(GL.GL_FRONT, GL.GL_AMBIENT_AND_DIFFUSE)

        GL.glClearColor(0.0, 0.0, 0.0, 0.0)
        GL.glDepthFunc(GL.GL_LEQUAL)
        GL.glShadeModel(GL.GL_SMOOTH)
        GL.glDrawBuffer(GL.GL_BACK)
        GL.glCullFace(GL.GL_BACK)
        GL.glEnable(GL.GL_COLOR_MATERIAL)
        GL.glEnable(GL.GL_CULL_FACE)
        GL.glEnable(GL.GL_DEPTH_TEST)
        GL.glEnable(GL.GL_LIGHTING)
        GL.glEnable(GL.GL_LIGHT0)
        GL.glEnable(GL.GL_LIGHT1)
        GL.glEnable(GL.GL_NORMALIZE)

        # Viewing transformation - set the viewpoint back from the scene
        GL.glTranslatef(0.0, 0.0, -self.depth_offset)

        # Modelling transformation - pan, zoom and rotate
        GL.glTranslatef(self.pan_x_3d, self.pan_y_3d, 0.0)
        GL.glMultMatrixf(self.scene_rotate)
        GL.glScalef(self.zoom, self.zoom, self.zoom)

    def render_3d(self):
        """Handle all drawing operations."""
        self.SetCurrent(self.context)
        if not self.init:
            # Configure the OpenGL rendering context
            self.init_gl_3d()
            self.init = True

        # Clear everything
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)

        if self.toggle == 1:
            self.draw_signals()
        GL.glColor3f(1.0, 1.0, 1.0)  # text is white

        # We have been drawing to the back buffer, flush the graphics pipeline
        # and swap the back buffer to the front
        GL.glFlush()
        self.SwapBuffers()

    def render(self, text = None):
        """Handle all drawing operations."""
        self.SetCurrent(self.context)
        if not self.init:
            # Configure the viewport, modelview and projection matrices
            self.init_gl()
            self.init = True

        # Clear everything
        GL.glClear(GL.GL_COLOR_BUFFER_BIT)

        if self.toggle == 1:
            self.draw_signals()

        if text is not None:
            # Draw specified text at position (10, 10)
            self.render_text(text, 10, 10)

        GL.glFlush()
        self.SwapBuffers()

    def draw_cuboid(self, x_pos, y_pos, half_width, half_depth, height):
        """Draw a cuboid.

        Draw a cuboid at the specified position, with the specified
        dimensions.
        """
        if not self.init:
            # Configure the viewport, modelview and projection matrices
            self.init_gl()
            self.init = True
        GL.glBegin(GL.GL_QUADS)

        GL.glNormal3f(0, -1, 0)
        GL.glVertex3f(x_pos - half_width, y_pos,  -half_depth)
        GL.glVertex3f(x_pos + half_width, y_pos,  -half_depth)
        GL.glVertex3f(x_pos + half_width, y_pos,  half_depth)
        GL.glVertex3f(x_pos - half_width, y_pos,  half_depth)

        GL.glNormal3f(0, 1, 0)
        GL.glVertex3f(x_pos + half_width, y_pos + height, -half_depth)
        GL.glVertex3f(x_pos - half_width, y_pos + height, -half_depth)
        GL.glVertex3f(x_pos - half_width, y_pos + height, half_depth)
        GL.glVertex3f(x_pos + half_width, y_pos + height, half_depth)
        GL.glNormal3f(-1, 0, 0)
        GL.glVertex3f(x_pos - half_width, y_pos + height, -half_depth)
        GL.glVertex3f(x_pos - half_width, y_pos, -half_depth)
        GL.glVertex3f(x_pos - half_width, y_pos, half_depth)
        GL.glVertex3f(x_pos - half_width, y_pos + height, half_depth)
        GL.glNormal3f(1, 0, 0)
        GL.glVertex3f(x_pos + half_width, y_pos, -half_depth)
        GL.glVertex3f(x_pos + half_width, y_pos + height, -half_depth)
        GL.glVertex3f(x_pos + half_width, y_pos + height, half_depth)
        GL.glVertex3f(x_pos + half_width, y_pos, half_depth)
        GL.glNormal3f(0, 0, -1)
        GL.glVertex3f(x_pos - half_width, y_pos, -half_depth)
        GL.glVertex3f(x_pos - half_width, y_pos + height, -half_depth)
        GL.glVertex3f(x_pos + half_width, y_pos + height, -half_depth)
        GL.glVertex3f(x_pos + half_width, y_pos, -half_depth)
        GL.glNormal3f(0, 0, 1)
        GL.glVertex3f(x_pos - half_width, y_pos + height, half_depth)
        GL.glVertex3f(x_pos - half_width, y_pos, half_depth)
        GL.glVertex3f(x_pos + half_width, y_pos, half_depth)
        GL.glVertex3f(x_pos + half_width, y_pos + height, half_depth)

        GL.glEnd()

    def draw_prism(self, x_pos, y_pos, half_width, half_depth, height, rise = True):
        """Draw a prism at the specified position, with the specified
        dimensions.
        """
        if not self.init:
            # Configure the viewport, modelview and projection matrices
            self.init_gl()
            self.init = True
        GL.glBegin(GL.GL_QUADS)

        if rise:
            GL.glNormal3f(-1, 1, 0)
            GL.glVertex3f(x_pos + half_width, y_pos + height, -half_depth)
            GL.glVertex3f(x_pos - half_width, y_pos, -half_depth)
            GL.glVertex3f(x_pos - half_width, y_pos, half_depth)
            GL.glVertex3f(x_pos + half_width, y_pos + height, half_depth)

        else:
            GL.glNormal3f(1, 1, 0)
            GL.glVertex3f(x_pos + half_width, y_pos, -half_depth)
            GL.glVertex3f(x_pos - half_width, y_pos + height, -half_depth)
            GL.glVertex3f(x_pos - half_width, y_pos + height, half_depth)
            GL.glVertex3f(x_pos + half_width, y_pos, half_depth)

        GL.glNormal3f(0, -1, 0)
        GL.glVertex3f(x_pos - half_width, y_pos, -half_depth)
        GL.glVertex3f(x_pos + half_width, y_pos, -half_depth)
        GL.glVertex3f(x_pos + half_width, y_pos, half_depth)
        GL.glVertex3f(x_pos - half_width, y_pos, half_depth)

        GL.glNormal3f(-1, 0, 0)
        GL.glVertex3f(x_pos - half_width, y_pos + height, -half_depth)
        GL.glVertex3f(x_pos - half_width, y_pos, -half_depth)
        GL.glVertex3f(x_pos - half_width, y_pos, half_depth)
        GL.glVertex3f(x_pos - half_width, y_pos + height, half_depth)
        GL.glNormal3f(0, 0, -1)
        GL.glVertex3f(x_pos - half_width, y_pos, -half_depth)
        GL.glVertex3f(x_pos - half_width, y_pos + height, -half_depth)
        GL.glVertex3f(x_pos + half_width, y_pos + height, -half_depth)
        GL.glVertex3f(x_pos + half_width, y_pos, -half_depth)
        GL.glNormal3f(0, 0, 1)
        GL.glVertex3f(x_pos - half_width, y_pos + height, half_depth)
        GL.glVertex3f(x_pos - half_width, y_pos, half_depth)
        GL.glVertex3f(x_pos + half_width, y_pos, half_depth)
        GL.glVertex3f(x_pos + half_width, y_pos + height, half_depth)

        GL.glEnd()

    def on_paint(self, event):
        """Handle the paint event."""
        if self.toggle_3D:
            self.SetCurrent(self.context)
            if not self.init:
                # Configure the OpenGL rendering context
                self.init_gl_3d()
                self.init = True

            size = self.GetClientSize()
            text = "".join(["Canvas redrawn on paint event, size is ",
                            str(size.width), ", ", str(size.height)])
            self.render_3d()

        else:
            self.SetCurrent(self.context)
            size = self.GetClientSize()
            # text = "".join(["Canvas redrawn on paint event, size is ",
            #                 str(size.width), ", ", str(size.height)])
            if self.toggle == 0:
                if not self.init:
                    # Configure the viewport, modelview and projection matrices
                    self.init_gl()
                    self.init = True
                GL.glFlush()
                self.SwapBuffers()

            else:
                self.SetCurrent(self.context)
                GL.glDrawBuffer(GL.GL_BACK)
                GL.glViewport(0, 0, size.width, size.height)
                GL.glMatrixMode(GL.GL_PROJECTION)
                GL.glLoadIdentity()
                GL.glOrtho(0, size.width, 0, size.height, -1, 1)
                GL.glMatrixMode(GL.GL_MODELVIEW)
                GL.glLoadIdentity()
                GL.glTranslated(self.pan_x, self.pan_y, 0.0)
                GL.glScaled(self.zoom, self.zoom, self.zoom)
                self.draw_signals()
                # self.render_text(text, 10, 10)
                GL.glFlush()
                self.SwapBuffers()

    def on_size(self, event):
        """Handle the canvas resize event."""
        # Forces reconfiguration of the viewport, modelview and projection
        # matrices on the next paint event
        self.init = False

    def on_mouse(self, event):
        """Handle mouse events."""
        if self.toggle_3D:
            self.SetCurrent(self.context)

            if event.ButtonDown():
                self.last_mouse_x = event.GetX()
                self.last_mouse_y = event.GetY()

            if event.Dragging():
                GL.glMatrixMode(GL.GL_MODELVIEW)
                GL.glLoadIdentity()
                x = event.GetX() - self.last_mouse_x
                y = event.GetY() - self.last_mouse_y
                if event.LeftIsDown():
                    GL.glRotatef(math.sqrt((x * x) + (y * y)), y, x, 0)
                if event.MiddleIsDown():
                    GL.glRotatef((x + y), 0, 0, 1)
                if event.RightIsDown():
                    self.pan_x_3d += x
                    self.pan_y_3d -= y
                GL.glMultMatrixf(self.scene_rotate)
                GL.glGetFloatv(GL.GL_MODELVIEW_MATRIX, self.scene_rotate)
                self.last_mouse_x = event.GetX()
                self.last_mouse_y = event.GetY()
                self.init = False

            if event.GetWheelRotation() < 0:
                self.zoom *= (1.0 + (
                    event.GetWheelRotation() / (20 * event.GetWheelDelta())))
                self.init = False

            if event.GetWheelRotation() > 0:
                self.zoom /= (1.0 - (
                    event.GetWheelRotation() / (20 * event.GetWheelDelta())))
                self.init = False

            self.Refresh()  # triggers the paint event

        else:
            text = ""
            # TODO: Currently no text is being printed when event is triggered
            if event.ButtonDown():
                self.last_mouse_x = event.GetX()
                self.last_mouse_y = event.GetY()
                text = "".join(["Mouse button pressed at: ", str(event.GetX()),
                                ", ", str(event.GetY())])
                # self.Refresh()
            if event.ButtonUp():
                text = "".join(["Mouse button released at: ", str(event.GetX()),
                                ", ", str(event.GetY())])
                # self.Refresh()
            if event.Dragging():
                self.pan_x += event.GetX() - self.last_mouse_x
                self.pan_y -= event.GetY() - self.last_mouse_y
                self.last_mouse_x = event.GetX()
                self.last_mouse_y = event.GetY()
                self.init = False
                text = "".join(["Mouse dragged to: ", str(event.GetX()),
                                ", ", str(event.GetY()), ". Pan is now: ",
                                str(self.pan_x), ", ", str(self.pan_y)])
                # self.Refresh()
            if event.GetWheelRotation() < 0:
                self.zoom *= (1.0 + (
                        event.GetWheelRotation() / (20 * event.GetWheelDelta())))
                self.init = False
                text = "".join(["Negative mouse wheel rotation. Zoom is now: ",
                                str(self.zoom)])
                # self.Refresh()
            if event.GetWheelRotation() > 0:
                self.zoom /= (1.0 - (
                        event.GetWheelRotation() / (20 * event.GetWheelDelta())))
                self.init = False
                text = "".join(["Positive mouse wheel rotation. Zoom is now: ",
                                str(self.zoom)])
                # self.Refresh()
            if text:
                self.render_text(text, 10, 10)
                self.Refresh()

    def render_text_3d(self, text, x_pos, y_pos, z_pos):
        """Handle text drawing operations."""
        GL.glDisable(GL.GL_LIGHTING)
        GL.glRasterPos3f(x_pos, y_pos, z_pos)
        font = GLUT.GLUT_BITMAP_HELVETICA_10

        for character in text:
            if character == '\n':
                y_pos = y_pos - 20
                GL.glRasterPos3f(x_pos, y_pos, z_pos)
            else:
                GLUT.glutBitmapCharacter(font, ord(character))

        GL.glEnable(GL.GL_LIGHTING)

    def render_text(self, text, x_pos, y_pos):
        """Handle text drawing operations."""
        GL.glColor3f(1.0, 1.0, 1.0)  # text is black
        GL.glRasterPos2f(x_pos, y_pos)
        font = GLUT.GLUT_BITMAP_HELVETICA_12

        for character in text:
            if character == '\n':
                y_pos = y_pos - 20
                GL.glRasterPos2f(x_pos, y_pos)
            else:
                GLUT.glutBitmapCharacter(font, ord(character))

    def draw_signals(self, text_array=[], signal_array=[]):

        if text_array:
            self.text_array = text_array
            self.signal_array = signal_array

        self.toggle = 1

        if self.toggle_3D:
            self.SetCurrent(self.context)
            if not self.init:
                # Configure the viewport, modelview and projection matrices
                self.init_gl_3d()
                self.init = True

            # Clear everything
            GL.glClear(GL.GL_COLOR_BUFFER_BIT)
            for i in range(len(self.signal_array)):
                x_step_size = 20
                y_step_size = 40

                # set origins where plot starts
                x_origin = 0
                y_origin = 0

                x = x_origin
                y = y_origin + y_step_size*i
                if self.text_array[i] is not None:
                    # Draw specified text at position (10, 10)
                    self.render_text_3d(self.text_array[i]+":", x-50, y, 0)
                    self.render_text_3d("0", x-20, y, 0)
                    self.render_text_3d("1", x-20, y + y_step_size/2, 0)

                if i == 0:
                    self.render_text("0", x_origin-x_step_size/2, y_origin - y_step_size/2)
                    for counter in range(len(self.signal_array[i])):
                        self.render_text_3d(str(counter+1), x_origin + (counter+0.5)*x_step_size, y_origin - y_step_size/2, 0)

                for signal in self.signal_array[i]:
                    GL.glColor3f(1.0, 0.7, 0.5)  # signal trace is beige

                    if signal == self.devices.HIGH:
                        self.draw_cuboid(x, y, 10, 10, y_step_size/2 + 1)
                        x += x_step_size

                    elif signal == self.devices.LOW:
                        self.draw_cuboid(x, y, 10, 10, 1)
                        x += x_step_size

                    elif signal == self.devices.RISING:
                        self.draw_prism(x, y, 10, 10, y_step_size/2 + 1)
                        x += x_step_size

                    elif signal == self.devices.FALLING:
                        self.draw_prism(x, y, 10, 10, y_step_size/2 + 1, rise=False)
                        x += x_step_size

                    elif signal == self.devices.BLANK:
                        self.draw_cuboid(x, y, 10, 0, 0)
                        x += x_step_size

                GL.glColor3f(1.0, 1.0, 1.0)  # text is white
            GL.glFlush()
            self.SwapBuffers()

        else:
            self.SetCurrent(self.context)
            if not self.init:
                # Configure the viewport, modelview and projection matrices
                self.init_gl()
                self.init = True

            # Clear everything
            GL.glClear(GL.GL_COLOR_BUFFER_BIT)

            for i in range(len(self.signal_array)):
                if self.text_array[i] is not None:
                    # Draw specified text at position
                    self.render_text(self.text_array[i]+":", 5, 50+75*i)
                    self.render_text("0", 40, 45 + 75 * i)
                    self.render_text("1", 40, 70 + 75 * i)

                x_step_size = 25
                y_step_size = 25
                x_next = 50
                x = x_next - x_step_size
                y_origin = 50 + 75*i

                if i == 0:
                    self.render_text("0", x_next, y_origin - 25)
                    for counter in range(len(self.signal_array[i])):
                        self.render_text(str(counter+1), 50 + (counter+1)*x_step_size, y_origin - 25)

                # Draw a sample signal trace
                GL.glBegin(GL.GL_LINE_STRIP)

                for signal in self.signal_array[i]:
                    skip_next = False
                    GL.glColor3f(0.0, 1.0, 0.0)

                    if signal == self.devices.HIGH:
                        x += x_step_size
                        y = y_origin + y_step_size
                        x_next += x_step_size
                        y_next = y_origin + y_step_size

                    elif signal == self.devices.LOW:
                        x += x_step_size
                        y = y_origin
                        x_next += x_step_size
                        y_next = y_origin

                    elif signal == self.devices.RISING:
                        x += 2*x_step_size
                        y = y_origin
                        x_next += x_step_size
                        y_next = y_origin + y_step_size
                        skip_next = True
                    elif signal == self.devices.FALLING:
                        x += 2*x_step_size
                        y = y_origin + y_step_size
                        x_next += x_step_size
                        y_next = y_origin
                        skip_next = True
                    elif signal == self.devices.BLANK:
                        x += x_step_size
                        x_next += x_step_size
                        y = y_origin
                        y_next = y_origin
                        GL.glColor3f(0.0, 0.0, 0.0)

                    GL.glVertex2f(x, y)
                    if not skip_next:
                        GL.glVertex2f(x_next, y_next)

                GL.glEnd()
                GL.glFlush()
                self.SwapBuffers()

    def reset_view(self):
        self.pan_x = 0
        self.pan_y = 0
        self.zoom = 1
        if self.toggle_3D:
            self.scene_rotate = np.identity(4, 'f')
            self.zoom = 2
            self.pan_x_3d = 0
            self.pan_y_3d = 0
        self.init = False

        self.Refresh()

    def adjust_signal_size(self):
        pass


class Gui(wx.Frame):
    """Configure the main window and all the widgets.

    This class provides a graphical user interface for the Logic Simulator and
    enables the user to change the circuit properties and run simulations.

    Parameters
    ----------
    title: title of the window.

    Public methods
    --------------
    on_menu(self, event): Event handler for the file menu. Contains About, Open and Close.

    on_spin_run(self, event): Event handler for when the user changes the spin
                           control value for number of cycles to run.

    on_spin_run(self, event): Event handler for when the user changes the spin
                           control value for number of cycles to continue.

    on_run_button(self, event): Event handler for when the user clicks the run button.

    on_run_button(self, event): Event handler for when the user clicks the continue button.

    on_switch_button(self, event): Event handler for when the user clicks the switch button.

    on_monitor_button(self, event): Event handler for when the user clicks the monitor button.

    on_restore_view_button(self, event): Event handler for when the user clicks the restore view button.  Resets the
                                         canvas to its original zoom level and orientation

    on_three_d_button(self, event): Event handler for when the user clicks the Enable 3D/Disable 3D button.

    on_quit_button(self, event): Event handler for when the user clicks the Quit button

    run_command(self): Runs the simulation from scratch.

    continue_command(self): Continues a previously run simulation.

    run_network(self, cycles): Runs the network for the specified number of
                               simulation cycles.

    monitor_command(self): Sets the specified monitor.

    zap_command(self): Removes the specified monitor.

    draw_signals(self): Obtain the monitored outputs as arrays to be drawn onto the canvas

    load_file(self): Loads the selected definition file and reinitialises the GUI parameters.

    print(self): Print messages onto the status message box
    """

    def __init__(self, title, path, names, devices, network, monitors, app, logging=False):
        """Initialise widgets and layout."""
        super().__init__(parent=None, title=title, size=(1200, 600))

        # Replicate userint.py's functionality
        self.names = names
        self.devices = devices
        self.monitors = monitors
        self.network = network
        self.path = path
        self.cycles_completed = 0  # number of simulation cycles completed

        # Configure the file menu
        fileMenu = wx.Menu()
        menuBar = wx.MenuBar()
        fileMenu.Append(wx.ID_ABOUT, _(u"&About"))
        fileMenu.Append(wx.ID_OPEN, _(u"&Open"))
        fileMenu.Append(wx.ID_EXIT, _(u"&Exit"))
        menuBar.Append(fileMenu, _(u"&File"))
        self.SetMenuBar(menuBar)

        # Canvas for drawing signals
        self.canvas = MyGLCanvas(self, self.devices, self.monitors)

        # Configure the widgets
        self.text_run_cycle = wx.StaticText(self, wx.ID_ANY, _(u"Cycles"))
        self.text_continue_cycle = wx.StaticText(self, wx.ID_ANY, _(u"Cycles"))
        self.spin_run = wx.SpinCtrl(self, wx.ID_ANY, "10")
        self.spin_continue = wx.SpinCtrl(self, wx.ID_ANY, "10")
        self.run_button = wx.Button(self, wx.ID_ANY, _(u"Run"))
        self.continue_button = wx.Button(self, wx.ID_ANY, _(u"Continue"))
        self.continue_button.Enable(False)
        self.restore_view_button = wx.Button(self, wx.ID_ANY, _(u"Restore view"))
        self.threeD_button = wx.Button(self, wx.ID_ANY, _(u"Enable 3D"))
        self.quit_button = wx.Button(self, wx.ID_ANY, _(u"Quit"))
        self.switch_button = wx.Button(self, wx.ID_ANY, _(u"Set Switches On/Off"))
        self.monitor_button = wx.Button(self, wx.ID_ANY, _(u"Set/Zap Monitors"))
        self.status_text = wx.StaticText(self, wx.ID_ANY, _(u"Status Messages:"))
        self.message = ""
        self.message_box = wx.TextCtrl(self, wx.ID_ANY, self.message, style=wx.TE_MULTILINE | wx.TE_READONLY)
        self.print(self.path)

        # Bind events to widgets
        self.Bind(wx.EVT_MENU, self.on_menu)
        self.spin_run.Bind(wx.EVT_SPINCTRL, self.on_spin_run)
        self.spin_continue.Bind(wx.EVT_SPINCTRL, self.on_spin_continue)
        self.run_button.Bind(wx.EVT_BUTTON, self.on_run_button)
        self.continue_button.Bind(wx.EVT_BUTTON, self.on_continue_button)
        self.switch_button.Bind(wx.EVT_BUTTON, self.on_switch_button)
        self.monitor_button.Bind(wx.EVT_BUTTON, self.on_monitor_button)
        self.restore_view_button.Bind(wx.EVT_BUTTON, self.on_restore_view_button)
        self.threeD_button.Bind(wx.EVT_BUTTON, self.on_three_d_button)
        self.quit_button.Bind(wx.EVT_BUTTON, self.on_quit_button)

        # Configure sizers for layout
        self.main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.side_sizer = wx.BoxSizer(wx.VERTICAL)
        simulate_run_sizer = wx.BoxSizer(wx.HORIZONTAL)
        simulate_continue_sizer = wx.BoxSizer(wx.HORIZONTAL)
        button_sizer = wx.BoxSizer(wx.VERTICAL)
        text_sizer = wx.BoxSizer(wx.VERTICAL)

        self.main_sizer.Add(self.canvas, 5, wx.EXPAND | wx.ALL, 5)
        self.main_sizer.Add(self.side_sizer, 1, wx.ALL, 5)

        self.side_sizer.Add(simulate_run_sizer, 0, wx.TOP, 5)
        self.side_sizer.Add(simulate_continue_sizer, 0, wx.TOP, 5)
        self.side_sizer.Add(button_sizer, 1, wx.TOP, 5)
        self.side_sizer.Add(text_sizer, 5, wx.ALIGN_CENTRE | wx.EXPAND, 5)

        simulate_run_sizer.Add(self.run_button, 2, wx.ALL, 5)
        simulate_run_sizer.Add(self.spin_run, 2, wx.ALL, 5)
        simulate_run_sizer.Add(self.text_run_cycle, 1, wx.ALL, 5)
        simulate_continue_sizer.Add(self.continue_button, 2, wx.ALL, 5)
        simulate_continue_sizer.Add(self.spin_continue, 2, wx.ALL, 5)
        simulate_continue_sizer.Add(self.text_continue_cycle, 1, wx.ALL, 5)

        button_sizer.Add(self.switch_button, 1, wx.ALL, 5)
        button_sizer.Add(self.monitor_button, 1, wx.ALL, 5)
        button_sizer.Add(self.restore_view_button, 1, wx.ALL, 5)
        button_sizer.Add(self.threeD_button, 1, wx.ALL, 5)
        button_sizer.Add(self.quit_button, 1, wx.ALL, 5)

        text_sizer.Add(0, 0, 1)
        text_sizer.Add(self.status_text, 0, wx.ALL, 5)
        text_sizer.Add(self.message_box, 3, wx.EXPAND, 5)

        self.SetSizeHints(800, 400)
        self.SetSizer(self.main_sizer)

        # Configure default/initial values
        self.spin_value_run = "10"  # must be same as initial display on spin widget
        self.spin_value_continue = "10"
        self.switch_selections = []
        self.list_of_monitors = []
        self.monitor_selections = []
        self.monitor = []

        # sets whether the list of monitors in system can be changed
        self.toggle_list_of_monitors = 1
        self.toggle_run = False
        self.threeD_toggle = 0

        # enables printing to console/terminal
        self.logging = False

    def on_menu(self, event):
        """Handle the event when the user selects a menu item."""
        Id = event.GetId()
        if Id == wx.ID_EXIT:
            self.Close(True)
        if Id == wx.ID_ABOUT:
            wx.MessageBox(_(u"Logic Simulator\nCreated by Team 10\n2019"),
                          _(u"About Logsim"), wx.ICON_INFORMATION | wx.OK)
        if Id == wx.ID_OPEN:
            self.load_file()

    def on_spin_run(self, event):
        """Handle the event when the user changes the spin control value."""
        self.spin_value_run = self.spin_run.GetValue()
        text = "".join([_(u"New spin control value: "), str(self.spin_value_run)])
        self.print(text)

    def on_spin_continue(self, event):
        """Handle the event when the user changes the spin control value."""
        self.spin_value_continue = self.spin_continue.GetValue()
        text = "".join([_(u"New spin control value: "), str(self.spin_value_continue)])
        self.print(text)

    def on_run_button(self, event):
        """Handle the event when the user clicks the run button."""
        self.print(_(u"Run button pressed."))
        if self.toggle_run is False:
            self.toggle_run = True
            self.continue_button.Enable(True)
        self.run_command()

    def on_continue_button(self, event):
        """Handle the event when the user clicks the continue button."""
        self.print(_(u"Continue button pressed."))
        self.continue_command()

    def on_switch_button(self, event):
        """Handle the event when the user clicks the switch button."""
        self.print(_(u"Setting switches"))

        switch_list = []
        switch_id = self.devices.find_devices(self.devices.SWITCH)
        for i in range(len(switch_id)):
            k = self.names.get_name_string(switch_id[i])
            if k is not None:
                switch_list.append(k)

        switch_dialog = wx.MultiChoiceDialog(self, _(u"Set switches On/Off"), _(u"Set switches"),
                                             switch_list, style=wx.OK)
        switch_dialog.SetSelections(self.switch_selections)

        if switch_dialog.ShowModal() == wx.ID_OK:
            self.switch_selections = switch_dialog.GetSelections()

        switch_state = [0]*len(switch_list)

        for i in range(len(self.switch_selections)):
            switch_state[self.switch_selections[i]] = 1

        for i in range(len(switch_list)):
            state = self.devices.set_switch(switch_id[i], switch_state[i])
            if self.logging is True:
                if state:
                    print("Successfully set switch.")
                else:
                    print("Error! Invalid switch.")

    def on_monitor_button(self, event):
        """Handle the event when the user clicks the monitor button."""
        text = _(u"Setting/Zapping which signals to monitor")
        self.canvas.render(text)

        monitor_id_list = list(self.monitors.monitors_dictionary)

        # append devices with outputs that are not defined as monitorable in definition file.
        for device_id in self.devices.find_devices():
            device = self.devices.get_device(device_id)
            for output_id in device.outputs:
                if (device_id, output_id) not in self.monitors.monitors_dictionary:
                    monitor_id_list.append((device_id, output_id))

        for i in range(len(monitor_id_list)):
            if monitor_id_list[i][0] is None:
                return None
            elif monitor_id_list[i][1] is not None:
                port_id = monitor_id_list[i][1]
                if port_id is None:
                    return None
            else:
                port_id = None

            string_name = self.names.get_name_string(monitor_id_list[i][0])

            if port_id is not None:
                port_name = self.names.get_name_string(monitor_id_list[i][1])
            else:
                port_name = ""
            if string_name is not None:

                # only append to this list the first time button is clicked
                if self.toggle_list_of_monitors == 1:
                    self.list_of_monitors.append(str(string_name) + "." + str(port_name))
                    self.monitor.append([monitor_id_list[i][0], port_id])

        # prevent self.list_of_monitors and self.monitors from being overwritten when zapped
        self.toggle_list_of_monitors = 0

        monitor_dialog = wx.MultiChoiceDialog(self, _(u"Set/Zap which signals to monitor"),
                                              _(u"Set/Zap signals"), self.list_of_monitors, style=wx.OK)
        monitor_dialog.SetSelections(self.monitor_selections)

        signal_state = [0]*len(self.list_of_monitors)

        if monitor_dialog.ShowModal() == wx.ID_OK:
            self.monitor_selections = monitor_dialog.GetSelections()

        for i in range(len(self.monitor_selections)):
            signal_state[self.monitor_selections[i]] = 1

        if sum(signal_state) == 0:
            self.print(_(u"All monitors are zapped."))

        for i in range(len(signal_state)):
            if signal_state[i] == 1:
                self.monitor_command(self.monitor[i])
            elif signal_state[i] == 0:
                self.zap_command(self.monitor[i])
            else:
                raise ValueError

    def on_restore_view_button(self, event):
        """" Handles the event when restore view button is clicked. Resets the canvas to its original zoom level and
        orientation"""
        self.canvas.reset_view()

    def on_three_d_button(self, event):
        """ Handles the event for when the user clicks the Enable 3D/Disable 3D button.
            renders the signals in 2D or 3D. """
        if self.threeD_toggle:
            self.threeD_button.SetLabel(_(u"Enable 3D"))
            self.threeD_toggle = False
            self.canvas.toggle_3D = False
            self.canvas.init = False
            self.canvas.Refresh()
            self.canvas.reset_view()
        else:
            self.threeD_button.SetLabel(_(u"Disable 3D"))
            self.threeD_toggle = True
            self.canvas.toggle_3D = True
            self.canvas.init = False
            self.canvas.Refresh()
            self.canvas.reset_view()

    def on_quit_button(self, event):
        """ Handles the event when Quit button is clicked. Ends the program and closes the window."""
        self.Close()

    # ported from userint.py and changed slightly
    def run_command(self):
        """Run the simulation from scratch."""
        self.cycles_completed = 0
        cycles = int(self.spin_value_run)

        if cycles is not None:  # if the number of cycles provided is valid
            self.monitors.reset_monitors()
            self.print("".join([_(u"Running for "), str(cycles), _(u" cycles")]))
            self.devices.cold_startup()
            if self.run_network(cycles):
                self.cycles_completed += cycles

        self.draw_signals()

    def continue_command(self):
        """Continue a previously run simulation."""
        cycles = int(self.spin_value_continue)
        if cycles is not None:  # if the number of cycles provided is valid
            if self.cycles_completed == 0:
                self.print(_(u"Error! Nothing to continue. Run first."))
            elif self.run_network(cycles):
                self.cycles_completed += cycles
                self.print(" ".join([_(u"Continuing for"), str(cycles), _(u"cycles."),
                           _(u"Total:"), str(self.cycles_completed)]), append=True)

        self.draw_signals()

    def run_network(self, cycles):
        """Run the network for the specified number of simulation cycles.

        Return True if successful.
        """
        for _ in range(cycles):
            if self.network.execute_network():
                self.monitors.record_signals()
            else:
                self.print(_(u"Error! Network oscillating."))
                return False
        # self.monitors.display_signals()
        return True

    def monitor_command(self, monitor):
        """Set the specified monitor."""
        if monitor is not None:
            [device, port] = monitor
            monitor_error = self.monitors.make_monitor(device, port,
                                                       self.cycles_completed)
            if self.logging:
                if monitor_error == self.monitors.NO_ERROR or self.monitors.MONITOR_PRESENT:
                    print("Successfully made monitor.")
                else:
                    print("Error! Could not make monitor.")

    def zap_command(self, monitor):
        """Remove the specified monitor."""
        if monitor is not None:
            [device, port] = monitor
            if self.monitors.get_monitor_signal(device, port) is not None:
                if self.monitors.remove_monitor(device, port):
                    if self.logging:
                        print("Successfully zapped monitor")
                else:
                    if self.logging:
                        print("Error! Could not zap monitor.")
            else:
                if self.logging:
                    print("Monitor was already zapped")

    def draw_signals(self):
        """"Obtain the monitored outputs as arrays to be drawn onto the canvas"""
        margin = self.monitors.get_margin()
        text_array = []
        signal_array = []
        for device_id, output_id in self.monitors.monitors_dictionary:
            monitor_name = self.devices.get_signal_name(device_id, output_id)
            name_length = len(monitor_name)
            signal_list = self.monitors.monitors_dictionary[(device_id, output_id)]
            text = monitor_name + (margin - name_length) * " "
            signal_array.append(signal_list)
            text_array.append(text)

        self.canvas.draw_signals(text_array, signal_array)

    def load_file(self):
        """Loads the selected definition file and reinitialises the GUI parameters. """
        with wx.FileDialog(self, "Open test definition file", wildcard="TXT files (*.txt)|*.txt",
                           style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return  # the user changed their mind

            # Proceed loading the file chosen by the user
            self.path = fileDialog.GetPath()
            try:
                self.names = Names()
                self.devices = Devices(self.names)
                self.network = Network(self.names, self.devices)
                self.monitors = Monitors(self.names, self.devices, self.network)
                self.scanner = Scanner(self.path, self.names)
                self.parser = Parser(self.names, self.devices, self.network, self.monitors, self.scanner)
                self.parser.parse_network()
                self.cycles_completed = 0  # number of simulation cycles completed
                self.canvas.devices = self.devices

                # Configure default/initial values
                self.switch_selections = []
                self.list_of_monitors = []
                self.monitor_selections = []
                self.monitor = []

                # sets whether the list of monitors in system can be changed
                self.toggle_list_of_monitors = 1
                self.toggle_run = False

            except IOError:
                self.print(_(u"Cannot open file '%s'.") % self.path)

    def print(self, text, append=False):
        """Print messages onto the status message box"""
        if append:
            self.message_box.WriteText(text)
        else:
            self.message_box.Clear()
            self.message_box.WriteText(text)


lang = None


class LanguageGui(wx.Frame):
    def __init__(self):
        """Initialise widgets and layout."""
        super().__init__(parent=None, title="Select Language", size=(200, 200))
        self.selection = ""
        self.language_box = wx.Choice(self, id=wx.ID_ANY, choices=["English", "Chinese"], style=0)
        self.OK_button = wx.Button(self, wx.ID_ANY, "OK")
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(self.language_box, 1, wx.ALIGN_CENTRE | wx.ALL, 5)
        main_sizer.AddStretchSpacer(0.5)
        main_sizer.Add(self.OK_button, 0.5, wx.ALIGN_CENTRE | wx.ALL, 5)
        self.language_box.Bind(wx.EVT_CHOICE, self.chosen_language)
        self.OK_button.Bind(wx.EVT_BUTTON, self.confirm_selection)
        self.language = None
        self.SetSizer(main_sizer)

    def confirm_selection(self, event):
        self.Close()

    def chosen_language(self, event):
        global lang
        self.language = self.language_box.GetString(self.language_box.GetSelection())
        lang = self.language
