from names import Names
import pytest


@pytest.fixture
def new_names():
    """Return a new names instance."""
    return Names()


@pytest.fixture
def name_string_list():
    """Return a list of example names."""
    return ["Alice", "Bob", "Eve"]


@pytest.fixture
def used_names(name_string_list):
    """Return a names instance, after three names have been added."""
    my_name = Names()
    my_name.lookup(name_string_list)
    return my_name


def test_get_name_string_raises_exceptions(used_names):
    """Test if get_string raises expected exceptions."""
    with pytest.raises(TypeError):
        used_names.get_name_string(1.4)
    with pytest.raises(TypeError):
        used_names.get_name_string("hello")
    with pytest.raises(ValueError):
        used_names.get_name_string(-1)


@pytest.mark.parametrize("name_id, expected_string", [
    (0, "Alice"),
    (1, "Bob"),
    (2, "Eve"),
    (3, None)
])
def test_get_name_string(used_names, new_names, name_id, expected_string):
    """Test if get_string returns the expected string."""
    # Name is present
    assert used_names.get_name_string(name_id) == expected_string
    # Name is absent
    assert new_names.get_name_string(name_id) is None


def test_lookup_raises_exceptions(used_names):
    """Test if lookup raises expected exceptions."""
    with pytest.raises(TypeError):
        used_names.lookup(1.5)
    with pytest.raises(TypeError):
        used_names.lookup(2)


def test_lookup(used_names, new_names, expected_name_id=[0, 1, 2, 3], string_list=["Alice", "Bob", "Eve", None]):
    """Test if lookup returns expected index."""
    assert used_names.lookup(string_list) == expected_name_id
    assert new_names.lookup(string_list) == [0, 1, 2, 3]


def test_query_raises_exception(used_names):
    """Test if query raises expected exceptions."""
    with pytest.raises(TypeError):
        used_names.query(1.4)
    with pytest.raises(TypeError):
        used_names.query(2)


@pytest.mark.parametrize("expected_name_id, string", [
    (0, "Alice"),
    (1, "Bob"),
    (2, "Eve"),
    (None, None)
])
def test_query(used_names, new_names, expected_name_id, string):
    """Test if lookup returns expected index."""
    assert used_names.query(string) == expected_name_id
    assert new_names.query(string) is None
