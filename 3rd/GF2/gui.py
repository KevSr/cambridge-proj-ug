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
from OpenGL import GL, GLUT


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

    render(self, text): Handles all drawing operations.

    on_paint(self, event): Handles the paint event.

    on_size(self, event): Handles the canvas resize event.

    on_mouse(self, event): Handles mouse events.

    render_text(self, text, x_pos, y_pos): Handles text drawing
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

        # Initialise variables for panning
        self.pan_x = 0
        self.pan_y = 0
        self.last_mouse_x = 0  # previous mouse x position
        self.last_mouse_y = 0  # previous mouse y position

        # Initialise variables for zooming
        self.zoom = 1

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

    def on_paint(self, event):
        """Handle the paint event."""
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
        text = ""
        # TODO: Currently no text is being printed when event is triggered
        if event.ButtonDown():
            self.last_mouse_x = event.GetX()
            self.last_mouse_y = event.GetY()
            text = "".join(["Mouse button pressed at: ", str(event.GetX()),
                            ", ", str(event.GetY())])
            #self.Refresh()
        if event.ButtonUp():
            text = "".join(["Mouse button released at: ", str(event.GetX()),
                            ", ", str(event.GetY())])
            #self.Refresh()
        if event.Dragging():
            self.pan_x += event.GetX() - self.last_mouse_x
            self.pan_y -= event.GetY() - self.last_mouse_y
            self.last_mouse_x = event.GetX()
            self.last_mouse_y = event.GetY()
            self.init = False
            text = "".join(["Mouse dragged to: ", str(event.GetX()),
                            ", ", str(event.GetY()), ". Pan is now: ",
                            str(self.pan_x), ", ", str(self.pan_y)])
            #self.Refresh()
        if event.GetWheelRotation() < 0:
            self.zoom *= (1.0 + (
                event.GetWheelRotation() / (20 * event.GetWheelDelta())))
            self.init = False
            text = "".join(["Negative mouse wheel rotation. Zoom is now: ",
                            str(self.zoom)])
            #self.Refresh()
        if event.GetWheelRotation() > 0:
            self.zoom /= (1.0 - (
                event.GetWheelRotation() / (20 * event.GetWheelDelta())))
            self.init = False
            text = "".join(["Positive mouse wheel rotation. Zoom is now: ",
                            str(self.zoom)])
            #self.Refresh()
        if text:
            self.render_text(text, 10, 10)
            self.Refresh()

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

        self.SetCurrent(self.context)
        if not self.init:
            # Configure the viewport, modelview and projection matrices
            self.init_gl()
            self.init = True

        # Clear everything
        GL.glClear(GL.GL_COLOR_BUFFER_BIT)

        for i in range(len(self.signal_array)):
            if self.text_array[i] is not None:
                # Draw specified text at position (10, 10)
                self.render_text(self.text_array[i], 75, 75+150*i)

            # Draw a sample signal trace
            GL.glBegin(GL.GL_LINE_STRIP)
            x_step_size = 50
            y_step_size = 50
            x = 100 - x_step_size
            x_next = 100
            y_origin = 100 + 150*i

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
        self.Refresh()


class Gui(wx.Frame):
    """Configure the main window and all the widgets.

    This class provides a graphical user interface for the Logic Simulator and
    enables the user to change the circuit properties and run simulations.

    Parameters
    ----------
    title: title of the window.

    Public methods
    --------------
    on_menu(self, event): Event handler for the file menu.

    on_spin_run(self, event): Event handler for when the user changes the spin control value for "run".

    on_spin_continue(self, event): Event handler for when the user changes the spin control value for "continue".

    on_run_button(self, event): Event handler for when the user clicks the run button.

    on_continue_button(self, event): Event handler for when the user clicks the continue button.

    on_switch_button(self, event): Event handler when the user clicks the switch button.

    on_monitor_button(self, event): Event handler when the user clicks the monitor button.

    on_quit_button(self.event): Event handler when the user clicks the quit button.

    on_text_box(self, event): Event handler for when the user enters text.
    """

    def __init__(self, title, path, names, devices, network, monitors, logging=False):
        """Initialise widgets and layout."""
        super().__init__(parent=None, title=title, size=(1200, 600))

        # Replicate userint.py's functionality
        self.names = names
        self.devices = devices
        self.monitors = monitors
        self.network = network
        self.cycles_completed = 0  # number of simulation cycles completed

        # Configure the file menu
        fileMenu = wx.Menu()
        menuBar = wx.MenuBar()
        fileMenu.Append(wx.ID_ABOUT, _(u"&About"))
        fileMenu.Append(wx.ID_EXIT, _(u"&Exit"))
        menuBar.Append(fileMenu, _(u"&File"))
        self.SetMenuBar(menuBar)

        # Canvas for drawing signals
        self.canvas = MyGLCanvas(self, self.devices, self.monitors)

      #  locale = wx.Locale(wx.LANGUAGE_SPANISH)
     #   self.locale.AddCatalogLookupPathPrefix('.')
      #  self.locale.AddCatalog('simple_de')

        # Configure the widgets
        self.text_run_cycle = wx.StaticText(self, wx.ID_ANY, _(u"Cycles"))
        self.text_continue_cycle = wx.StaticText(self, wx.ID_ANY, _(u"Cycles"))
        self.spin_run = wx.SpinCtrl(self, wx.ID_ANY, "10")
        self.spin_continue = wx.SpinCtrl(self, wx.ID_ANY, "10")
        self.run_button = wx.Button(self, wx.ID_ANY, _(u"Run"))
        self.continue_button = wx.Button(self, wx.ID_ANY, _(u"Continue"))
        self.continue_button.Enable(False)
        self.restore_view_button = wx.Button(self, wx.ID_ANY, _(u"Restore view"))
        self.quit_button = wx.Button(self, wx.ID_ANY, _(u"Quit"))
        self.switch_button = wx.Button(self, wx.ID_ANY, _(u"Set Switches On/Off"))
        self.monitor_button = wx.Button(self, wx.ID_ANY, _(u"Set/Zap Monitors"))
        self.status_text = wx.StaticText(self, wx.ID_ANY, _(u"Status Messages:"))
        self.message = ""
        self.message_box = wx.TextCtrl(self, wx.ID_ANY, self.message, style=wx.TE_MULTILINE | wx.TE_READONLY)
        # self.text_box = wx.TextCtrl(self, wx.ID_ANY, "",
        #                             style=wx.TE_PROCESS_ENTER)

        # Bind events to widgets
        self.Bind(wx.EVT_MENU, self.on_menu)
        self.spin_run.Bind(wx.EVT_SPINCTRL, self.on_spin_run)
        self.spin_continue.Bind(wx.EVT_SPINCTRL, self.on_spin_continue)
        self.run_button.Bind(wx.EVT_BUTTON, self.on_run_button)
        self.continue_button.Bind(wx.EVT_BUTTON, self.on_continue_button)
        self.switch_button.Bind(wx.EVT_BUTTON, self.on_switch_button)
        self.monitor_button.Bind(wx.EVT_BUTTON, self.on_monitor_button)
        self.restore_view_button.Bind(wx.EVT_BUTTON, self.on_restore_view_button)
        self.quit_button.Bind(wx.EVT_BUTTON, self.on_quit_button)
        # self.text_box.Bind(wx.EVT_TEXT_ENTER, self.on_text_box)

        # Configure sizers for layout
        main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        side_sizer = wx.BoxSizer(wx.VERTICAL)
        simulate_run_sizer = wx.BoxSizer(wx.HORIZONTAL)
        simulate_continue_sizer = wx.BoxSizer(wx.HORIZONTAL)
        button_sizer = wx.BoxSizer(wx.VERTICAL)
        text_sizer = wx.BoxSizer(wx.VERTICAL)

        main_sizer.Add(self.canvas, 5, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(side_sizer, 1, wx.ALL, 5)

        side_sizer.Add(simulate_run_sizer, 0, wx.TOP, 5)
        side_sizer.Add(simulate_continue_sizer, 0, wx.TOP, 5)
        side_sizer.Add(button_sizer, 1, wx.TOP, 5)
        side_sizer.Add(text_sizer, 5, wx.ALIGN_CENTRE | wx.EXPAND, 5)

        simulate_run_sizer.Add(self.run_button, 2, wx.ALL, 5)
        simulate_run_sizer.Add(self.spin_run, 2, wx.ALL, 5)
        simulate_run_sizer.Add(self.text_run_cycle, 1, wx.ALL, 5)
        simulate_continue_sizer.Add(self.continue_button, 2, wx.ALL, 5)
        simulate_continue_sizer.Add(self.spin_continue, 2, wx.ALL, 5)
        simulate_continue_sizer.Add(self.text_continue_cycle, 1, wx.ALL, 5)

        button_sizer.Add(self.switch_button, 1, wx.ALL, 5)
        button_sizer.Add(self.monitor_button, 1, wx.ALL, 5)
        button_sizer.Add(self.restore_view_button, 1, wx.ALL, 5)
        button_sizer.Add(self.quit_button, 1, wx.ALL, 5)

        text_sizer.Add(0, 0, 1)
        text_sizer.Add(self.status_text, 0, wx.ALL, 5)
        text_sizer.Add(self.message_box, 3, wx.EXPAND, 5)
        # side_sizer.Add(self.text_box, 1, wx.ALL, 5)

        self.SetSizeHints(800, 400)
        self.SetSizer(main_sizer)

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

        # enables printing to console/terminal
        self.logging = logging

    def on_menu(self, event):
        """Handle the event when the user selects a menu item."""
        Id = event.GetId()
        if Id == wx.ID_EXIT:
            self.Close(True)
        if Id == wx.ID_ABOUT:
            wx.MessageBox(_(u"Logic Simulator\nCreated by Mojisola Agboola\n2017"),
                          _(u"About Logsim"), wx.ICON_INFORMATION | wx.OK)

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
        self.print(wx.GetTranslation(_(u"Run button pressed.")))
        self.continue_command()
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
        # TODO: why does this return a None as well?
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

        # TODO: Simplify return message
        for i in range(len(switch_list)):
            state = self.devices.set_switch(switch_id[i], switch_state[i])
            if self.logging is True:
                if state:
                    print(_(u"Successfully set switch."))
                else:
                    print(_(u"Error! Invalid switch."))

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

        print(monitor_id_list)

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
        self.canvas.reset_view()

    def on_quit_button(self, event):
        self.Close()

    # def on_text_box(self, event):
    #     """Handle the event when the user enters text."""
    #     text_box_value = self.text_box.GetValue()
    #     text = "".join(["New text box value: ", text_box_value])
    #     self.canvas.render(text)

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
                    print(_(u"Successfully made monitor."))
                else:
                    print(_(u"Error! Could not make monitor."))

    def zap_command(self, monitor):
        """Remove the specified monitor."""
        if monitor is not None:
            [device, port] = monitor
            if self.monitors.get_monitor_signal(device, port) is not None:
                if self.monitors.remove_monitor(device, port):
                    if self.logging:
                        print(_(u"Successfully zapped monitor"))
                else:
                    if self.logging:
                        print(_(u"Error! Could not zap monitor."))
            else:
                if self.logging:
                    print(_(u"Monitor was already zapped"))

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

    def print(self, text, append=False):
        """Print messages onto the status message box"""
        if append:
            self.message_box.WriteText(text)
        else:
            self.message_box.Clear()
            self.message_box.WriteText(text)
