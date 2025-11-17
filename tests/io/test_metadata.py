import pytest
from insitupy.io.metadata import MetaDataParser


@pytest.fixture
def metadata_parser():
    """Fixture to initialize the MetaDataParser with default settings."""
    return MetaDataParser()


META_LINES = [
    "Site,Site1",
    "Pit ID,1234",
    "date/time,2025-10-08 12:34:56",
]
META_LINES_PARSED = {
    "site_id": "Site1",
    "pit_id": "1234",
    "datetime": "2025-10-08 12:34:56",
}


class TestMetaDataParser:
    def test_preparse_meta_returns_dict(self, metadata_parser):
        result = metadata_parser._preparse_meta(META_LINES)

        assert result == META_LINES_PARSED, "Metadata lines parsed incorrectly."

    def test_preparse_meta_with_empty_lines(self, metadata_parser):
        meta_lines = META_LINES + [
            "",
            "  ,"
        ]

        result = metadata_parser._preparse_meta(meta_lines)

        assert result == META_LINES_PARSED, "Empty lines were not ignored correctly."

    def test_preparse_meta_with_time_and_date_key(self, metadata_parser):
        """
        Ensure that times are not improperly split into separate entries.
        """
        meta_lines = [
            "Time,12:34:56",
            "Date,2025-10-09",
        ]

        result = metadata_parser._preparse_meta(meta_lines)

        expected = {
            "time": "12:34:56",
            "date": "2025-10-09",
        }
        assert result == expected, "Time or date keys processed incorrectly."

    def test_preparse_meta_with_no_key_value_pairs(self, metadata_parser):
        meta_lines = META_LINES + [
            "Time,,",
            "Time start/end,,, ,",
        ]

        result = metadata_parser._preparse_meta(meta_lines)

        assert result == META_LINES_PARSED, (
            "Lines without key-value pairs were not skipped."
        )
