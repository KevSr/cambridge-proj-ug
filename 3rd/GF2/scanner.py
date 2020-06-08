"""Read the circuit definition file and translate the characters into symbols.

Used in the Logic Simulator project to read the characters in the definition
file and translate them into symbols that are usable by the parser.

Classes
-------
Scanner - reads definition file and translates characters into symbols.
Symbol - encapsulates a symbol and stores its properties.
"""


import sys


class Symbol:

    """Encapsulate a symbol and store its properties.

    Parameters
    ----------
    No parameters.

    Public methods
    --------------
    No public methods.
    """

    def __init__(self):
        """Initialise symbol properties."""
        self.type = None
        self.id = None
        self.line_number = None
        self.position = None


class Scanner:

    """Read circuit definition file and translate the characters into symbols.

    Once supplied with the path to a valid definition file, the scanner
    translates the sequence of characters in the definition file into symbols
    that the parser can use. It also skips over comments and irrelevant
    formatting characters, such as spaces and line breaks.

    Parameters
    ----------
    path: path to the circuit definition file.
    names: instance of the names.Names() class.

    Public methods
    -------------
    get_symbol(self): Translates the next sequence of characters into a symbol
                      and returns the symbol.
    """

    def __init__(self, path, names):
        """Open specified file and initialise reserved words and IDs."""
        self.names = names

        """Open and return the file specified by path."""
        self.path = path
        try:
            self.f = open(self.path, "r")
        except IndexError:
            sys.exit()

        self.symbol_type_list = [self.COMMA, self.SEMICOLON, self.DOT,
                                 self.ARROW, self.EQUALS, self.KEYWORD,
                                 self.NUMBER, self.NAME, self.EOF] = range(9)

        self.error_type_list = [self.NO_NUMBER, self.NO_ARROW,
                                self.UNKNOWN_SYM, self.NO_NAME, self.NO_EQUAL,
                                self.NO_SEMICOLON, self.NO_COMMA, self.NO_DOT,
                                self.INCORRECT_KEYWORD, self.NO_KEYWORD,
                                self.INVALID_VARIABLE, self.NO_CONNECT, self.NO_EOF] = range(13)

        self.keywords_list = ["DEVICES", "CONNECT", "MONITOR", "END"]

        [self.DEVICES_ID, self.CONNECT_ID, self.MONITOR_ID,
         self.END_ID] = self.names.lookup(self.keywords_list)

        self.current_character = ""

        # start at zero for Python indexing,
        # where current_line = 1 refers to line 1
        self.current_line = 0
        self.current_position = 0



    def get_symbol(self):
        """Translate the next sequence of characters into a symbol."""
        symbol = Symbol()
        self.skip_spaces()  # current character now not whitespace
        self.skip_comments()

        if self.current_character.isalpha():  # name
            name_string = self.get_name()
            if name_string in self.keywords_list:
                symbol.type = self.KEYWORD
            else:
                symbol.type = self.NAME
            [symbol.id] = self.names.lookup([name_string])

        elif self.current_character.isdigit():  # number
            symbol.id = self.get_number()
            symbol.type = self.NUMBER

        elif self.current_character == "=":  # punctuation
            symbol.type = self.EQUALS
            self.advance()

        elif self.current_character == ".":  # punctuation
            symbol.type = self.DOT
            self.advance()

        elif self.current_character == ",":  # punctuation
            symbol.type = self.COMMA
            self.advance()

        elif self.current_character == ";":  # punctuation
            symbol.type = self.SEMICOLON
            self.advance()

        elif self.current_character == "-":  # punctuation
            self.advance()
            if self.current_character == ">":
                symbol.type = self.ARROW
                self.advance()
            else:
                self.error_location()
                self.display_error(self.NO_ARROW)
                raise SyntaxError

        elif self.current_character == "":  # end of file
            if self.current_line == 0 and self.current_position == 0:
                self.advance()
            else:
                symbol.type = self.EOF

        elif self.current_character == '\n':
            self.advance()

        else:
            self.error_location()
            self.display_error(self.UNKNOWN_SYM)
            raise SyntaxError

        symbol.line_number = self.current_line
        symbol.position = self.current_position

        return symbol

    def skip_spaces(self):
        """Set current_character to the next non-whitespace
        character in definition file, f."""
        while True:
            if self.current_character.isspace() is True:
                self.advance()
            else:
                return

    def skip_comments(self):
        """Set current_character to the next non-comment character in definition file,
        if comments are denoted by //...//"""
        if self.current_character == "/":
            self.advance()
            if self.current_character == "/":
                self.advance()
                while True:
                    if self.current_character is "/":
                        self.advance()
                        if self.current_character is "/":
                            self.advance()
                            self.skip_spaces()
                            return
                    else:
                        self.advance()
                        

    def get_name(self):
        """Seek the next name string in input_file. Return the name string
        and set the next non-alphanumeric character to current_character."""
        name = ""  # initialise the name to return
        while True:
            if self.current_character.isalnum():
                name += str(self.current_character)
                self.advance()
            else:
                return name

    def get_number(self):
        """Seek the next number in definition file.
        Return the integer number and set the next non-digit character. """
        number = 0  # initialise the number to return
        while True:
            if self.current_character.isdigit():
                number = 10*number + int(self.current_character)
                self.advance()
            else:
                return number

    def advance(self):
        self.current_character = self.f.read(1)
        self.current_position += 1
        if self.current_character == "\n":
            self.current_line += 1
            self.current_position = 0

    # for Daren:
    def error_location(self, error_type=None, line_check=None):
        """ Returns the line where scanner has reached as well as
        the current position of the scanner"""
        with open(self.path, "r") as file:
            if line_check is not None and line_check is not self.current_line:
                pass
            else:
                line_check = self.current_line
            if error_type is None:
                print("Line : {}".format(line_check))
                print(file.read().split('\n')[line_check])
                print(" "*(self.current_position-1) + "^")
            elif error_type is self.INCORRECT_KEYWORD:
                print("Line : {}".format(line_check))
                print(file.read().split('\n')[line_check])
                print("^")
            elif error_type is self.NO_CONNECT:
                keyword_line = self.current_line-1
                position = self.current_position - error_type
                print("Line : {}".format(keyword_line))
                print(file.read().split('\n')[keyword_line])
                print(" "*(self.current_position-position - 3) + "^")
            elif isinstance(error_type, int):
                print("Line : {}".format(line_check))
                print(file.read().split('\n')[line_check])
                position = self.current_position - error_type
                print(" "*(self.current_position-position - 1) + "^")

    def display_error(self, error_type):
        if error_type == self.NO_NUMBER:
            raise SyntaxError("Expected a number")
        elif error_type == self.NO_ARROW:
            print("Expected a '>'")
        elif error_type == self.UNKNOWN_SYM:
            print("Unknown Symbol")

        elif error_type == self.INCORRECT_KEYWORD:
            raise SyntaxError("Incorrect Keyword")
        elif error_type == self.INVALID_VARIABLE:
            raise SyntaxError("Expected only an output")
        elif error_type == self.NO_CONNECT:
            raise SyntaxError("This is not the symbol for connection")
        #for parser
        elif error_type == self.NO_NAME:
            raise SyntaxError("Expected a device name")
        elif error_type == self.NO_EQUAL:
            raise SyntaxError("Expected '='")
        elif error_type == self.NO_DOT:
            print("Expected '.'")
        elif error_type == self.NO_SEMICOLON:
            raise SyntaxError("Expected ';'")
        elif error_type == self.NO_KEYWORD:
            print("Expected keyword")
        elif error_type == self.NO_COMMA:
            raise SyntaxError("Expected ','")
        elif error_type == self.NO_EOF:
            print("Expected 'END'")
