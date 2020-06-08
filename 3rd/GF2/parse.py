"""Parse the definition file and build the logic network.

Used in the Logic Simulator project to analyse the syntactic and semantic
correctness of the symbols received from the scanner and then builds the
logic network.

Classes
-------
Parser - parses the definition file and builds the logic network.
"""


class Parser:
    """Parse the definition file and build the logic network.

    The parser deals with error handling. It analyses the syntactic and
    semantic correctness of the symbols it receives from the scanner, and
    then builds the logic network. If there are errors in the definition file,
    the parser detects this and tries to recover from it, giving helpful
    error messages.

    Parameters
    ----------
    names: instance of the names.Names() class.
    devices: instance of the devices.Devices() class.
    network: instance of the network.Network() class.
    monitors: instance of the monitors.Monitors() class.
    scanner: instance of the scanner.Scanner() class.

    Public methods
    --------------
    parse_network(self): Parses the circuit definition file.

    set_devices(self): Seperate function to set required devices.

    set_connections(self): Seperate function to set required devices.

    set_monitor(self): Seperate function to set monitoring points.

    make_monitor_dtype(self, device_id): Calls monitor.py's built in function
                                    that returns with type of error, specially
                                    for D type flip flops.

    make_monitor(self, device_id, output_id=None): Calls monitor.py's built in
                                    function that returns with type of error.

    device_check(self, device_kind, device_property): Checks if there are any
                                    errors in the definition file in the
                                    DEVICES section.

    connect(self, first_device_id, first_port_id, connect_device_name):
                        Function to call network.py's make_connect function.

    check_connection(self): Checks if any of the devices have unconnected
                            inputs.

    set_dtype_input_values(self, GND): Set all inputs of d-type if they are
                            not connected at the end of connection function.

    network_error_check(self, error_check, position=None, connect_device=None,
                        port_id=None, line_check=None): Checks if there are
                                        any errors reported from network.py.

    monitor_error_check(self, error_check): Checks if there are any errors
                                            returned from monitor.py.

    set_ground(self): Makes an arbitrary switch representing ground.

    call_error(self, error_type, line_check=None): Calls error functions in
                                                   scanner.py.

    network_arrow_check(self, first_device_id, arrow_check): Checks any error
                            up to the arrow which is required for connection.

    """

    def __init__(self, names, devices, network, monitors, scanner):
        """Initialise constants."""
        self.names = names
        self.devices = devices
        self.network = network
        self.monitors = monitors
        self.scanner = scanner
        self.error_count = 0
        self.SEMANTIC = "semantic error"
        self.POSITION = 0
        self.LINE = 0
        self.MISSING = ""

    def parse_network(self):
        """Parse the circuit definition file."""
        # Check all four keywords (DEVICES, CONNECT, MONITOR, END) are in
        # definition file

        file = self.scanner.f.read()
        self.scanner.f.seek(0, 0)
        for i in ['DEVICES', 'CONNECT', 'MONITOR', 'END']:
            start = 0
            if i in file:
                count = file.count(i)

                for j in range(count):
                    ind = file.find(i, start)
                    if file[ind-1] in ['', ' ', '\n'] and \
                       file[ind+len(i)] in ['', ' ', '\n']:
                        break
                    start += ind + 1
                else:
                    self.MISSING = i
                    print('KEYWORD: ' + i + ' not found')
            else:
                self.MISSING = i
                print('KEYWORD: ' + i + ' not found')

        keyword = self.scanner.get_symbol()
        if keyword.type is None:
            keyword = self.scanner.get_symbol()
        else:
            pass
        while keyword.type is self.scanner.KEYWORD:
            if keyword.id == self.scanner.DEVICES_ID:
                keyword = self.set_devices()  # Set devices
            else:
                # If incorrect syntax
                self.call_error(self.scanner.INCORRECT_KEYWORD, self.LINE)

            if keyword.id == self.scanner.CONNECT_ID:
                keyword = self.set_connections()  # Set Connections
            else:
                self.call_error(self.scanner.INCORRECT_KEYWORD, self.LINE+1)
            if keyword.id == self.scanner.MONITOR_ID:
                keyword = self.set_monitor()  # Set Monitoring points
            else:
                self.call_error(self.scanner.INCORRECT_KEYWORD, self.LINE+1)
            if keyword.id == self.scanner.END_ID:
                print("Number of errors found: {}".format(self.error_count))
                # Can only continue to logsim if error count is 0
                if self.error_count is 0:
                    return keyword.id  # Returns a value to enable logsim
                else:
                    return False
            else:
                self.call_error(self.scanner.INCORRECT_KEYWORD, self.LINE+1)
        else:
            self.call_error(self.scanner.INCORRECT_KEYWORD, self.LINE)

    def set_devices(self):
        """Seperate function to set required devices"""
        symbol = self.scanner.get_symbol()

        while True:  # Iterate until next keyword is met
            if symbol.type != self.scanner.NAME:  # Checks if name
                self.call_error(self.scanner.NO_NAME)

            device_id = symbol.id

            device_name = self.scanner.names.name_string_list[device_id]

            # Check name is valid
            gate_strings = ["AND", "OR", "NAND", "NOR", "XOR"]
            device_strings = ["CLOCK", "SWITCH", "DTYPE", "SIGGEN"]
            dtype_inputs = ["CLK", "SET", "CLEAR", "DATA"]
            dtype_outputs = ["Q", "QBAR"]

            for i in [gate_strings, device_strings, dtype_inputs,
                      dtype_outputs, self.scanner.keywords_list]:
                if device_name in i:
                    self.scanner.error_location()
                    raise SyntaxError(device_name + ' is not a valid name')

            # Check name is not overlapped
            if self.devices.get_device(device_id) is not None:
                if self.MISSING is 'CONNECT':
                    self.call_error(self.scanner.INCORRECT_KEYWORD,
                                    self.LINE + 1)
                else:
                    self.scanner.error_location()
                    raise SyntaxError(device_name + ' has been used')

            # Check for equal sign after device is found
            equal = self.scanner.get_symbol()
            if equal.type != self.scanner.EQUALS:
                if self.MISSING is 'CONNECT':
                    self.call_error(self.scanner.INCORRECT_KEYWORD,
                                    self.LINE + 1)
                else:
                    self.call_error(self.scanner.NO_EQUAL)

            # Check for device type
            device_kind = self.scanner.get_symbol()
            if device_kind.type != self.scanner.NAME:
                self.call_error(self.scanner.NO_NAME)

            device_kind = device_kind.id  # Sets device kind
            if device_kind not in self.devices.gate_types \
               and device_kind not in self.devices.device_types:
                self.scanner.error_location()
                device_name = self.scanner.names.get_name_string(device_kind)
                raise SyntaxError(device_name + ' is not a valid device type')

            self.LINE  =  self.scanner.current_line
            semicolon_check = self.scanner.get_symbol()
            # Check if devices require input specification.
            # If yes, expect a COMMA
            if semicolon_check.type is self.scanner.COMMA:
                # Checks if comma is present for further input
                device_property = self.scanner.get_symbol()
                if device_property.type != self.scanner.NUMBER:
                    self.scanner.error_location()
                    self.scanner.display_error(self.scanner.NO_NUMBER)
                device_property = device_property.id
                self.device_check(device_kind, device_property)
                if device_kind is not self.devices.SIGGEN:
                    # Make device using all variables
                    self.devices.make_device(device_id, device_kind,
                                             device_property)
                else:
                    self.LINE = self.scanner.current_line
                    comma_check = self.scanner.get_symbol()
                    if comma_check.type is self.scanner.COMMA:
                        device_property_2 = self.scanner.get_symbol()
                    else:
                        self.call_error(self.scanner.NO_COMMA, self.LINE)
                    if device_property_2.type != self.scanner.NUMBER:
                        self.scanner.error_location()
                        self.scanner.display_error(self.scanner.NO_NUMBER)
                    device_property_2 = device_property_2.id
                    self.devices.make_device(device_id, device_kind,
                                             device_property,
                                             device_property_2)

                # Check for semicolon
                semicolon = self.scanner.get_symbol()
                if semicolon.type != self.scanner.SEMICOLON:
                    self.scanner.error_location()
                    self.scanner.display_error(self.scanner.NO_SEMICOLON)

                # Make this variable for error handling
                self.LINE = self.scanner.current_line
                end_check = self.scanner.get_symbol()
                # Check if next symbol is keyword
                if end_check.type == self.scanner.KEYWORD:
                    return end_check
                else:
                    symbol = end_check

            # Check if devices require input specification.
            # If no, expect semicolon
            elif semicolon_check.type is self.scanner.SEMICOLON:
                if device_kind in [self.devices.CLOCK, self.devices.SWITCH,
                                   self.devices.AND, self.devices.OR,
                                   self.devices.NAND, self.devices.NOR]:
                    self.scanner.error_location(None, self.LINE)
                    device_name =\
                        self.scanner.names.get_name_string(device_kind)
                    raise SyntaxError('Expected Input specifications for ' +
                                      device_name + ' type')

                self.devices.make_device(device_id, device_kind)
                # Make device without device_property as
                # it is not present
                self.LINE = self.scanner.current_line
                end_check = self.scanner.get_symbol()
                if end_check.type == self.scanner.KEYWORD:
                    return end_check
                else:
                    symbol = end_check

            # Check if semicolon is found at end of line
            else:
                self.scanner.error_location()
                self.scanner.display_error(self.scanner.NO_SEMICOLON)

    def set_connections(self):
        """Seperate function to make connections"""
        first_device_name = self.scanner.get_symbol()
        while True:  # iterate until next one is Keyword
            if first_device_name.type != self.scanner.KEYWORD:
                first_device_id = first_device_name.id
                first_device = self.devices.get_device(first_device_id)

                if self.devices.get_device(first_device_id) is None:
                    self.scanner.error_location()
                    first_name =\
                        self.scanner.names.get_name_string(first_device_id)
                    print(first_name + ' not found')
                    self.error_count += 1

                    while first_device_name.type != self.scanner.SEMICOLON:
                        first_device_name = self.scanner.get_symbol()
                    first_device_name = self.scanner.get_symbol()

                # Check if first_device is a device and which device it is
                elif (first_device is not None and first_device.device_kind
                        is not self.devices.D_TYPE):
                    arrow_check = self.scanner.get_symbol()
                    self.network_arrow_check(first_device_id, arrow_check)
                    connect_device_name = self.scanner.get_symbol()
                    # Calls seperate function to connect devices
                    first_device_name = self.connect(first_device_id, None,
                                                     connect_device_name)

                elif (first_device is not None and first_device.device_kind
                      is self.devices.D_TYPE):
                    # For D Flip-flop
                    dot_check = self.scanner.get_symbol()
                    if dot_check.type is self.scanner.DOT:
                        first_device_port = self.scanner.get_symbol()
                        if (first_device_port.id not in
                                self.devices.dtype_output_ids):
                            # Error if port is not for d-type
                            self.network_error_check(self.network.PORT_ABSENT,
                                                     None, first_device)
                            first_device_port_id = None
                        else:
                            first_device_port_id = first_device_port.id
                    else:
                        self.network_error_check(self.SEMANTIC)
                        # Error if no port is connected
                        pass
                    arrow_check = self.scanner.get_symbol()
                    self.network_arrow_check(first_device_id, arrow_check)
                    connect_device_name = self.scanner.get_symbol()
                    first_device_name = self.connect(first_device_id,
                                                     first_device_port_id,
                                                     connect_device_name)
                else:
                    # If first device not valid
                    self.call_error(self.scanner.INVALID_VARIABLE)
            else:
                # Connects all unspecified inputs in dtype to ground
                return first_device_name

    def set_monitor(self):
        """Function to set monitoring points"""
        device_name = self.scanner.get_symbol()
        while True:
            if device_name.type == self.scanner.NAME:
                device_id = device_name.id
                device = self.devices.get_device(device_id)
                # As only D type flip-flip has more than one input
                if device is None:
                    self.make_monitor(device_id)

                elif (device is not None and
                        device.device_kind is not self.devices.D_TYPE):
                    self.make_monitor(device_id)
                elif (device is not None and
                      device.device_kind is self.devices.D_TYPE):
                    self.make_monitor_dtype(device_id)
                else:
                    self.call_error(self.scanner.INVALID_VARIABLE)
                self.LINE = self.scanner.current_line
                device_name = self.scanner.get_symbol()
            else:
                GND = self.set_ground()
                self.set_dtype_input_values(GND)
                self.check_connection()
                return device_name

    def make_monitor_dtype(self, device_id):
        """Calls monitor.py's built in function that
        returns with type of error, specially for D type
        flip flops"""
        dot_check = self.scanner.get_symbol()
        # Checks for dot if device is dtype as it has
        # multiple outputs
        if dot_check.type is self.scanner.DOT:
            output = self.scanner.get_symbol()
        else:
            self.monitor_error_check(self.monitors.NOT_OUTPUT)
        output_id = output.id
        if output_id in self.devices.dtype_output_ids:
            error_type = self.monitors.make_monitor(device_id,
                                                    output_id)
            # Checks for error
            self.monitor_error_check(error_type)
        else:
            self.monitor_error_check(self.monitors.NOT_OUTPUT)
        self.LINE = self.scanner.current_line
        semicolon = self.scanner.get_symbol()
        # Checks if semicolon
        if semicolon.type is not self.scanner.SEMICOLON:
            self.call_error(self.scanner.NO_SEMICOLON, self.LINE)

    def make_monitor(self, device_id, output_id=None):
        """Calls monitor.py's built in function that
        returns with type of error"""
        dot_check = self.scanner.get_symbol()
        if dot_check.type is self.scanner.DOT:
            self.monitor_error_check(self.monitors.NOT_OUTPUT)
        semicolon_check = dot_check
        error_type = self.monitors.make_monitor(device_id,
                                                output_id)
        # Checks for error
        self.monitor_error_check(error_type)
        self.LINE = self.scanner.current_line
        # Checks if semicolon
        for n in range(3):
            print(n)
            if semicolon_check.type is not self.scanner.SEMICOLON:
                if n < 2:
                    semicolon_check = self.scanner.get_symbol()
                    continue
                elif n == 2:
                    self.call_error(self.scanner.NO_SEMICOLON, self.LINE)
            else:
                break

    def device_check(self, device_kind, device_property):
        """Checks if there are any errors in the definition file in the
        DEVICES section"""
        # Check if devices requires input specification. If no, raise error.
        if (device_kind == self.devices.D_TYPE or device_kind ==
                self.devices.XOR):
            self.scanner.error_location()
            raise SyntaxError(self.scanner.names.get_name_string(device_kind) +
                              ' does not need input specification')
        # Check if gates (other than XOR) has valid input numbers
        if (device_kind in self.devices.gate_types and device_kind !=
                self.devices.XOR):
            if (device_property > self.devices.max_gate_inputs or
                    device_property < 1):
                self.scanner.error_location()
                raise ValueError('Expected gate input number between 1 to 16')
        # Check clock has valid simulation cycle number
        if device_kind == self.devices.CLOCK:
            if device_property < 1:
                self.scanner.error_location()
                raise ValueError('Invalid simulation cycle number.\
                                  Expected > 0')
        # Check switch has valid input states
        if device_kind == self.devices.SWITCH:
            if device_property not in [0, 1]:
                self.scanner.error_location()
                raise ValueError('Invalid switch input states.\
                                 Expected 1 or 0')

    def connect(self, first_device_id, first_port_id, connect_device_name):
        """Function to call network.py's make_connect function"""
        while True:  # Iterate until there is a semicolon
            if connect_device_name.type != self.scanner.SEMICOLON:
                connect_device_id = connect_device_name.id
                connect_device = self.devices.get_device(
                    connect_device_id)
                # Connections depend on which types of devices
                # are present
                self.LINE = self.scanner.current_line
                self.POSITION = self.scanner.current_position + 50
                dot_check = self.scanner.get_symbol()
                if dot_check.type is self.scanner.DOT:
                    # Checks if dot is present between device
                    # and port name, which is required
                    port = self.scanner.get_symbol()
                    port_id = port.id
                    comma_check = self.scanner.get_symbol()
                else:
                    port_id = None
                    comma_check = dot_check
                error_check = self.network.make_connection(
                    first_device_id, first_port_id,
                    connect_device_id, port_id)
                # Check if any semantic error is reported while
                # Producing the connection
                first_device = self.devices.get_device(first_device_id)
                if (first_device.device_kind is self.devices.D_TYPE and
                        first_port_id is None):
                    pass
                else:
                    self.network_error_check(error_check, self.POSITION,
                                             connect_device, port_id,
                                             self.LINE)
                if comma_check.type is self.scanner.COMMA:
                    # Checks if comma is present for
                    # further input
                    connect_device_name \
                        = self.scanner.get_symbol()
                elif comma_check.type is not self.scanner.SEMICOLON:
                    if comma_check.type is self.scanner.NAME:
                        self.call_error(self.scanner.NO_COMMA)
                    else:
                        self.call_error(self.scanner.NO_SEMICOLON)
                else:
                    connect_device_name \
                        = comma_check
            else:
                self.LINE = self.scanner.current_line

                first_device_name = self.scanner.get_symbol()
                return first_device_name

    def check_connection(self):
        """Checks if any of the devices have unconnected inputs"""
        device_list = self.devices.find_devices()
        for a in device_list:
            device = self.devices.get_device(a)
            if (device.device_kind is not self.devices.CLOCK and
                    device.device_kind is not self.devices.SWITCH):
                device_input = device.inputs
            else:
                continue
            for n in device.inputs:
                if device.inputs[n] is None:
                    self.error_count += 1
                    device_name = self.names.get_name_string(a)
                    device_port = self.names.get_name_string(n)
                    print("{}'s input ".format(device_name) +
                          device_port + " is floating")
                else:
                    continue

    def set_dtype_input_values(self, GND):
        """Set all inputs of d-type if they are not connected
        at the end of connection function"""
        x = self.devices.get_device(GND)
        device_ids = self.devices.find_devices(self.devices.D_TYPE)
        # Search all dtype devices
        for a in device_ids:
            # Iterate for all devices found
            device_id = a
            device = self.devices.get_device(a)
            for n in device.inputs:
                # sets all not connected ('None') inputs to ground
                if device.inputs[n] is None:
                    self.network.make_connection(GND, None, device_id, n)
                else:
                    continue

    def network_error_check(self, error_check, position=None,
                            connect_device=None, port_id=None,
                            line_check=None):
        """Checks if there are any errors reported from network.py"""
        # If there were no errors found
        if error_check is self.network.NO_ERROR:
            pass
        # If one of the device is not found
        elif error_check is self.network.DEVICE_ABSENT:
            self.error_count += 1
            self.call_error(position)
            print("Device not defined")
            pass
        # If output is connected to output
        elif error_check is self.network.OUTPUT_TO_OUTPUT:
            self.error_count += 1
            self.call_error(position, line_check)
            print("Expected an input to be connected")
            pass
        # If input of connecting device is already connected
        elif error_check is self.network.INPUT_CONNECTED:
            self.error_count += 1
            self.scanner.error_location()
            print("Input is already connected to another port")
            pass
        # If one of the port is absent
        elif error_check is self.network.PORT_ABSENT:
            if port_id is not None and port_id not in connect_device.inputs:
                port = self.names.get_name_string(port_id)
                # Gets the port number if it has a number
                if port.isalpha():
                    pass
                else:
                    num = [x for x in port if x.isdigit()]
                    num = "".join(num)
                # If port of non-dtype device is connected to
                # dtype device inputs
                if port_id in self.devices.dtype_input_ids:
                    self.error_count += 1
                    self.call_error(self.SEMANTIC)
                    name = self.names.get_name_string(connect_device.device_id)
                    print(port + " is not an input of " + name)
                # If input port number is greater than allowed
                # number of inputs
                elif port.isnumeric():
                    if int(num) > 16 or int(num) < 0:
                        self.error_count += 1
                        self.call_error(self.SEMANTIC)
                        print("Incorrect input. Expected integer"
                              " between 1 and 16")
                        # If port is not found
                else:
                    self.error_count += 1
                    self.call_error(self.SEMANTIC)
                    name = self.names.get_name_string(connect_device.device_id)
                    name = ".".join([name, port])
                    print("{} not found".format(name))
            else:
                self.error_count += 1
                self.call_error(self.SEMANTIC)
                name = self.names.get_name_string(connect_device.device_id)
                print("Invalid port for {}".format(name))
        # For all other errors
        else:
            self.error_count += 1
            self.call_error(self.SEMANTIC)
            print("Invalid input or output.")
            pass

    def monitor_error_check(self, error_check):
        """Checks if there are any errors returned from monitor.py"""
        if error_check is self.monitors.NO_ERROR:
            pass
        elif error_check is self.monitors.NOT_OUTPUT:
            self.error_count += 1
            self.call_error(self.SEMANTIC)
            print("Expected an output")
            pass
        elif error_check is self.network.DEVICE_ABSENT:
            self.error_count += 1
            self.call_error(self.SEMANTIC)
            print("Device not defined")
            pass
        elif error_check is self.monitors.MONITOR_PRESENT:
            self.error_count += 1
            self.call_error(self.SEMANTIC)
            print("Selected output is already getting monitored")
            pass

    def set_ground(self):
        """Makes an arbitrary switch representing ground"""
        GND = 0
        while True:
            # Adds ground signal in names list, after
            # the last position in the list
            if self.names.get_name_string(GND) is not None:
                GND += 1
            else:
                self.devices.make_switch(GND, 0)
                # Makes switch
                return GND

    def call_error(self, error_type, line_check=None):
        """Calls error functions in scanner.py"""
        if error_type is self.scanner.INCORRECT_KEYWORD:
            self.scanner.error_location(error_type, line_check)
        elif error_type is self.scanner.NO_CONNECT:
            self.scanner.error_location(error_type)
        elif error_type in self.scanner.error_type_list:
            self.scanner.error_location(None, line_check)
        elif error_type is self.SEMANTIC:
            self.scanner.error_location(None, line_check)
        elif error_type is self.POSITION:
            self.scanner.error_location(error_type - 50, line_check)
        else:
            self.scanner.error_locaiton(error_type)

        if error_type is self.POSITION:
            pass
        elif error_type in self.scanner.error_type_list:
            self.scanner.display_error(error_type)
        else:
            pass

    def network_arrow_check(self, first_device_id, arrow_check):
        """Checks any error up to arrow, for connection"""
        if arrow_check.type is self.scanner.ARROW:
            # Checks if arrow is present indicating connection
            pass
        elif arrow_check.type is self.scanner.DOT:
            self.error_count += 1
            outputcheck = self.scanner.get_symbol()
            # Checks if non-dtype output is connected to d-type
            # outputs
            if outputcheck.id in self.devices.dtype_output_ids:
                self.call_error(self.SEMANTIC)
                name = self.names.get_name_string(first_device_id)
                port = self.names.get_name_string(outputcheck.id)
                print(port + " is not an output of " + name)
            # For all other possible errors
            else:
                self.call_error(self.SEMANTIC)
                print("Expected an output")
            # Skips until arrow is found
            while True:
                if arrow_check.type is not self.scanner.ARROW:
                    arrow_check = self.scanner.get_symbol()
                else:
                    break
        # Calls syntax error as only one output should be present
        elif arrow_check.type is self.scanner.COMMA:
            self.call_error(self.scanner.INVALID_VARIABLE)
        elif self.MISSING is 'MONITOR':
            self.call_error(self.scanner.INCORRECT_KEYWORD, self.LINE+1)
        # For all other errors - Syntax
        else:
            self.call_error(self.scanner.NO_CONNECT)
