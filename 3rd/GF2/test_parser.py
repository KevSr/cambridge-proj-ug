from names import Names
from devices import Devices
from network import Network
from monitors import Monitors
from scanner import Scanner
from parse import Parser
import pytest


@pytest.fixture
def new_parser():
    """Return a new parser instance."""
    
    file_name = 'file.txt'
    new_names = Names()
    new_devices = Devices(new_names)
    new_network = Network(new_names, new_devices)
    new_monitors = Monitors(new_names, new_devices, new_network) 
    new_scanner = Scanner(file_name, new_names) 
    return Parser(new_names, new_devices, new_network, new_monitors, new_scanner) 

@pytest.fixture
def parser_with_devices(new_parser):
    """Return a parser class instance set up with one of each type of devices"""
    #1. G1 is AND gate with 1 input
    #2. G2 is NAND gate with 2 inputs
    #3. G3 is OR gate with 3 inputs
    #4. G4 is NOR gate with 4 inputs
    #5. G5 is SWITCH with initial state = 1
    #6. G6 is CLOCK with simulation cycle = 4
    #7. G7 is DTYPE
    #8. G8 is XOR gate

    f = open(new_parser.scanner.path, 'w+')
    f.write('G1 = AND, 1;\nG2 = NAND, 2;\nG3 = OR, 3;\nG4 = NOR, 4;\nG5 = SWITCH, 1;\nG6 = CLOCK, 4;\nG7 = DTYPE;\nG8 = XOR;\n\nCONNECT')
    f.close()

    new_parser.scanner.advance()
    new_parser.set_devices()
    new_parser.scanner.f.seek(0,0)
    new_parser.scanner.current_position = 0
    new_parser.scanner.current_line = 0
    return new_parser


def test_parse_network(new_parser):
    """Test if parse_network parses the sample circuit definition file correctly"""
    
    f = open(new_parser.scanner.path, 'w+')
    f.write('DEVICES\nG1 = AND, 2; \nSW1 = SWITCH, 0;\nSW2 = SWITCH, 0;\n\nCONNECT\nSW1 -> G1.I1;\nSW2 -> G1.I2;\n\nMONITOR\nG1;\n\nEND\n')
    f.close()    
    
    assert new_parser.parse_network() != 0

@pytest.mark.parametrize("txt", [('DEVICES\n CONNECT\n MONITOR\n'), ('DEVICES\n MONITOR\n END\n')])
#1. missing END
#2. missing CONNECT

def test_parse_network_raises_syntaxerror(new_parser, txt):
    """Test if parse_network raises exception when keywords are missing"""
    f = open(new_parser.scanner.path, 'w+')
    f.write(txt)
    f.close()    
    
    with pytest.raises(SyntaxError):
        new_parser.parse_network()

@pytest.mark.parametrize("txt", [('G1 = AND;'), ('G1 = NAND;'), ('G1 = OR;'), ('G1 = NOR;'), ('G1 = SWITCH;'), ('G1 = CLOCK;'), ('G1 = DTYPE,1;'), ('G1 = XOR,1;'), ('G1 = XOR,1;\nG1 = CLOCK;'), ('DTYPE = DTYPE;'), ('G1 = DTYPE'), ('G1 -> DTYPE;')])
#1,2,3,4,5,6. Input specification is required for AND, NAND, OR, NOR, SWITCH and CLOCK (i.e comma is expected)
#7,8. Input specification not required for DTYPE, XOR
#9. same device name used defined more than once
#10. Defining an invalid device name (i.e same name as device type like DTYPE)
#11. missing semicolon
#12. invalid symbol for setting up devices (i.e any symbol other than =)       
            
def test_set_devices_raises_syntaxerror(new_parser, txt):
    """Test if set_devices raises expected syntax error."""

    f = open(new_parser.scanner.path, 'w+')
    f.write(txt)
    f.close()
    new_parser.scanner.advance()
    
    with pytest.raises(SyntaxError):
        new_parser.set_devices()

@pytest.mark.parametrize("txt", [('G1 = AND, 0;'), ('G1 = AND, 17;'), ('G1 = CLOCK, 0;'), ('G1 = SWITCH, 2;')])
#1,2. Gate input out of range (Not within 1 to 16)
#3. Invalid clock cycle number (i.e <0)
#4. Invalid switch initial state (not binary)

def test_set_devices_raises_valueerror(new_parser, txt):
    """Test if set_devices raises expected value error"""
    f = open(new_parser.scanner.path, 'w+')
    f.write(txt)
    f.close()
    new_parser.scanner.advance()
    
    with pytest.raises(ValueError):
        new_parser.set_devices()
        
        
def test_set_devices(parser_with_devices):
    """Test if set_devices correctly assign devices type and parameter under devices class instance"""
    assert parser_with_devices.devices.devices_list[0].device_kind == parser_with_devices.devices.AND
    assert len(parser_with_devices.devices.devices_list[0].inputs) == 1
    assert parser_with_devices.devices.devices_list[1].device_kind == parser_with_devices.devices.NAND
    assert len(parser_with_devices.devices.devices_list[1].inputs) == 2
    assert parser_with_devices.devices.devices_list[2].device_kind == parser_with_devices.devices.OR
    assert len(parser_with_devices.devices.devices_list[2].inputs) == 3
    assert parser_with_devices.devices.devices_list[3].device_kind == parser_with_devices.devices.NOR
    assert len(parser_with_devices.devices.devices_list[3].inputs) == 4
    assert parser_with_devices.devices.devices_list[4].device_kind == parser_with_devices.devices.SWITCH
    assert parser_with_devices.devices.devices_list[4].switch_state == 1
    assert parser_with_devices.devices.devices_list[5].device_kind == parser_with_devices.devices.CLOCK
    assert parser_with_devices.devices.devices_list[5].clock_half_period == 4
    assert parser_with_devices.devices.devices_list[6].device_kind == parser_with_devices.devices.D_TYPE
    assert len(parser_with_devices.devices.devices_list[6].inputs) == 4
    assert len(parser_with_devices.devices.devices_list[6].outputs) == 2
    assert parser_with_devices.devices.devices_list[7].device_kind == parser_with_devices.devices.XOR
    assert len(parser_with_devices.devices.devices_list[7].inputs) == 2
    

@pytest.mark.parametrize("txt", [('G1 -> G2.I;\nMONITOR'), ('G1 -> G2.I3;\nMONITOR'), ('G9 -> G2.I1;\nMONITOR'), ('G2.I1 -> G2.I2;\nMONITOR'), ('G1 -> G2;\nMONITOR'), ('G1 -> G2.I1;\nG2 -> G2.I1;\nMONITOR')])
#1. invalid input name
#2. Non existent input port being connected
#3. non existent device 
#4. Input connected to Input
#5. output connected to output
#6. connecting to input port that is connected to another output port


def test_set_connections_count_error(parser_with_devices, txt):
    """Test if set_connections is able to record and count errors encountered under CONNECT block in definition file"""
    f = open(parser_with_devices.scanner.path, 'w+')
    f.write(txt)
    f.close()
    parser_with_devices.scanner.advance()

    parser_with_devices.set_connections()
    assert parser_with_devices.error_count == 1

@pytest.mark.parametrize("txt", [('G1 - G2.I1;\nMONITOR'), ('G1 = G2.I1;\nMONITOR'),('G1 > G2.I1;\nMONITOR'), ('G1 -> G2.I1\nMONITOR')])
#1,2,3. connection symbol (->) is inccorect
#4. missing semicolon

def test_set_connections_raise_syntaxerror(parser_with_devices, txt):
    """Test if set_connectionns raises expected syntax error"""
    f = open(parser_with_devices.scanner.path, 'w+')
    f.write(txt)
    f.close()
    parser_with_devices.scanner.advance()
    
    with pytest.raises(SyntaxError):
        parser_with_devices.set_connections()


@pytest.mark.parametrize("txt", [('G1\nEND')])
#1. missing semicolon


def test_set_monitors_raise_syntaxerror(parser_with_devices, txt):
    """Test if set_monitors raises expected syntax error"""
    f = open(parser_with_devices.scanner.path, 'w+')
    f.write(txt)
    f.close()
    parser_with_devices.scanner.advance()

    with pytest.raises(SyntaxError):
        parser_with_devices.set_monitor()


@pytest.mark.parametrize("txt", [('G9;\nEND'), ('G1.I1;\nEND'), ('G7.DATA;\nEND')])
#1. non existent output
#2. monitoring input is not allowed
#3. DATA is an input

def test_set_monitors_count_error(parser_with_devices, txt):
    """Test if set_monitors is able to record and count errors encountered under MONITOR block in definition file"""
    f = open(parser_with_devices.scanner.path, 'w+')
    f.write(txt)
    f.close()
    parser_with_devices.scanner.advance()

    parser_with_devices.set_monitor()
    assert parser_with_devices.error_count == 13 #12 erros from floaing inputs in G1, G2, G3, G4, G8