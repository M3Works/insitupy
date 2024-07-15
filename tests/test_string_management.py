import numpy as np
import pytest

from insitupy.campaigns.strings import StringManager


@pytest.mark.parametrize(
    "in_str, expected", [
        ('SMP instrument #', 'smp_instrument_#'),
        ('Dielectric Constant A', 'dielectric_constant_a'),
        ('Specific surface area (m^2/kg)', 'specific_surface_area'),
        # Ensure we remove a csv byte order mark in latin encoding
        ("ï»¿Camera", "camera"),
        (' Temperature \n', 'temperature')
    ]
)
def test_standardize_key(in_str, expected):
    """
    Test whether we can clean out the column header from a csv and standardize them
    """
    assert StringManager.standardize_key(in_str) == expected


@pytest.mark.parametrize('args, kwargs', [
    # Test multiple values being returned
    (
        ['Density [kg/m^3], Date [yyyymmdd]', '[]', ['kg/m^3', 'yyyymmdd']],
        {'errors': False}
    ),
    # Test single value being return with parenthese
    (['Time (seconds)', '()', ['seconds']], {'errors': False}),
    # Test Single encapsulator used as both
    (['Name "Surveyor"', '"', ['Surveyor']], {'errors': False}),
    # Test nothing returned
    (['Name', '()', []], {'errors': False}),
    # Test our value error for incorrect encaps
    (['Name', '()()', []], {'errors': True}), ])
def test_get_encapsulated(args, kwargs):
    """
    Test where we can remove chars in a string
    """
    s, encaps, expected = args
    # Errors out to test exception
    errors = kwargs['errors']

    if not errors:
        results = StringManager.get_encapsulated(s, encaps)
        for r, e in zip(results, expected):
            assert r == e
    else:
        with pytest.raises(ValueError):
            results = StringManager.get_encapsulated(s, encaps)


@pytest.mark.parametrize(
    's, encaps, expected', [
        ('Density [kg/m^3], Date [yyyymmdd]', '[]', 'Density , Date '),
        ('Time (seconds)', '()', 'Time '),
        ('Name "Surveyor"', '"', 'Name '),
        # test for mm and comments exchange
        ('grain_size (mm), comments', '()', 'grain_size , comments')
    ])
def test_strip_encapsulated(s, encaps, expected):
    """
    Test where we can remove chars in a string
    """
    r = StringManager.strip_encapsulated(s, encaps)
    assert r == expected


def test_parse_none():
    """
    Test we can convert nones and nans to None and still pass through everything
    else.
    """
    # Assert these are converted to None
    for v in ['NaN', '', 'NONE', np.nan]:
        assert StringManager.parse_none(v) is None

    # Assert these are unaffected by function
    for v in [10.5, 'Comment']:
        assert StringManager.parse_none(v) == v


@pytest.mark.parametrize("str_line, encapsulator, expected", [
    # Test simple 50/50
    ("1A", None, 1),
    # Use the ignore encapsulator
    ('1"A"', '""', 0),
    # Check for the div by zero
    ('A', None, 1),

])
def test_get_alpha_ratio(str_line, encapsulator, expected):
    result = StringManager.get_alpha_ratio(str_line, encapsulator=encapsulator)
    assert result == expected


@pytest.mark.parametrize(
    "line, header_sep, header_indicator, previous_alpha_ratio,"
    "expected_columns, expected", [
        # Test using a header indicator is the end all.
        ("# flags, ", None, '#', None, None, True),
        ("flags, ", None, '#', None, None, False),

        # Simple looking for 2 columns
        ("# flags, ", ',', None, None, 2, True),
        # Test with a real entry from stratigraphy which has lots of chars
        ("35.0,33.0,< 1 mm,DF,F,D,NaN", ',', '#', 7, 0.5, False),
        # Test a complicated string with encapsulation right after a normal header
        ('107.0,85.0,< 1 mm,FC,4F,D,"Variable."', ',', '#', 7, 1, False),
    ])
def test_line_is_header(
    line, header_sep, header_indicator, previous_alpha_ratio,
    expected_columns, expected
):
    result = StringManager.line_is_header(
        line, header_sep, header_indicator, previous_alpha_ratio,
        expected_columns
    )
    assert result == expected
