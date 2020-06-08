from scanner import Scanner
from names import Names
import pytest


@pytest.fixture
def new_names():
    """Return a new names instance."""
    return Names() 

@pytest.fixture
def file_name():
    """Return a new names instance."""
    return 'file.txt' 

@pytest.fixture
def new_scanner(file_name, new_names):
    """Return a new names instance."""
    return Scanner(file_name, new_names) 

@pytest.mark.parametrize("txt, expected_name_string_list, expected_id", [('DEVICES\nX1 =', ["DEVICES", "CONNECT", "MONITOR", "END", "X1"],[0,1,2,3,4])])
# Sample definition file with expected name string and corresponding ID

def test_get_symbol(new_scanner, file_name, txt, expected_name_string_list, expected_id):
    """Test if get_symbol is able to extract the next symbol correctly with the correct ID"""
    f = open(file_name, 'w+')
    f.write(txt)
    f.close()    
    new_scanner.advance()
    symbol1 = new_scanner.get_symbol()
    symbol2 = new_scanner.get_symbol()
    for i in range(len(expected_name_string_list)):
         assert new_scanner.names.name_string_list[i] == expected_name_string_list[i]
    assert symbol1.id == expected_id[0]
    assert symbol2.id == expected_id[4]

@pytest.mark.parametrize("txt", [("@"), ("$"), ("^"), ("#"), ("-")])
# Lines of sample definition file with invalid character

def test_get_symbol_raises_SyntaxError(new_scanner, file_name, txt):
    """Test if get_symbol raises expected syntax error"""
    f = open(file_name, 'w+')
    f.write(txt)
    f.close()
    new_scanner.advance()
    with pytest.raises(SyntaxError):
        new_scanner.get_symbol()

@pytest.mark.parametrize("txt, expected_current_char", [('     DEVICES', ["D"])])
# Lines of sample definition file with spaces

def test_skip_spaces(new_scanner, file_name, txt, expected_current_char):
    """Test if skip_spaces is able to skip whitespaces and stop when the next character is a non whitespace character"""
    f = open(file_name, 'w+')
    f.write(txt)
    f.close()    
    new_scanner.advance()
    new_scanner.skip_spaces()
    assert new_scanner.current_character == expected_current_char[0]
    
    
@pytest.mark.parametrize("txt, expected_current_char", [('//     DEVICES//D', ["D"])])
# Lines of sample definition file with comment

def test_skip_comments(new_scanner, file_name, txt, expected_current_char):
    f = open(file_name, 'w+')
    f.write(txt)
    f.close()    
    new_scanner.advance()
    new_scanner.skip_comments()
    assert new_scanner.current_character == expected_current_char[0]
    
    
@pytest.mark.parametrize("txt", [('DEVICES'), ('X1'), ('XOR')])
# Lines of sample definition file with name string

def test_get_name(new_scanner, file_name, txt):
    """Test if get_name is able to extract the next name string"""
    f = open(file_name, 'w+')
    f.write(txt)
    f.close()    
    new_scanner.advance()
    assert new_scanner.get_name() == txt
    
@pytest.mark.parametrize("txt", [(112), (3)])
# Lines of sample definition file with integer number

def test_get_number(new_scanner, file_name, txt):
    """Test if get_number is able to extract the next integer number"""
    f = open(file_name, 'w+')
    f.write(str(txt))
    f.close()    
    new_scanner.advance()
    assert new_scanner.get_number() == txt
