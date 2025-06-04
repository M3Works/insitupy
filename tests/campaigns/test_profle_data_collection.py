from unittest.mock import MagicMock, patch

import pytest

from insitupy.campaigns import ProfileDataCollection
from insitupy.io.metadata import MetaDataParser
from insitupy.profiles.base import ProfileData


@pytest.fixture
def mock_metadata_parser():
    mock_parser = MagicMock(spec=MetaDataParser)
    return mock_parser


@pytest.fixture
def mock_read_csv():
    with patch.object(ProfileDataCollection, '_read_csv') as mock_read_csv:
        mock_read_csv.return_value = ([], None)
        yield mock_read_csv


class TestProfileDataCollection:
    def test_profile_data_class(self):
        assert ProfileDataCollection.PROFILE_DATA_CLASS == ProfileData

    def test_from_csv_reads_csv_with_correct_params(self, mock_read_csv):
        filename = "test.csv"

        ProfileDataCollection.from_csv(filename=filename)

        mock_read_csv.assert_called_once()
        call_args = mock_read_csv.call_args[0]
        assert filename == call_args[0]
        assert isinstance(call_args[1], MetaDataParser)

    @patch(
        'insitupy.campaigns.ProfileDataCollection.'
        'PROFILE_DATA_CLASS.META_PARSER'
    )
    def test_from_csv_passes_params_to_meta_parser(
        self, mock_meta_parser, mock_read_csv
    ):
        filename = "test.csv"

        ProfileDataCollection.from_csv(filename=filename)

        mock_meta_parser.assert_called_once()
        assert mock_meta_parser.call_args[0][0] == 'US/Mountain'
        kwargs = mock_meta_parser.call_args.kwargs
        assert kwargs['primary_variable_file'] is None
        assert kwargs['metadata_variable_file'] is None
        assert kwargs['header_sep'] == ','
        assert kwargs['_id'] is None
        assert kwargs['campaign_name'] is None
        assert kwargs['allow_map_failures'] is False
        assert kwargs['allow_split_lines'] is True

    def test_from_csv_returns_collection_of_profiles(
        self, mock_metadata_parser, mock_read_csv
    ):
        metadata = MagicMock()
        profile1 = MagicMock()
        profile2 = MagicMock()
        mock_read_csv.return_value = ([profile1, profile2], metadata)

        result = ProfileDataCollection.from_csv(filename="test.csv")

        assert isinstance(result, ProfileDataCollection)
        assert result.profiles == [profile1, profile2]
        assert result.metadata == metadata

    def test_from_csv_ignores_profiles_with_variable_code_ignore(
        self, mock_metadata_parser, mock_read_csv
    ):
        metadata = MagicMock()
        profile1 = MagicMock(variable=MagicMock(code="DEPTH"))
        profile2 = MagicMock(variable=MagicMock(code="ignore"))
        mock_read_csv.return_value = ([profile1, profile2], metadata)

        result = ProfileDataCollection.from_csv(filename="test.csv")

        assert len(result.profiles) == 1
        assert result.profiles[0].variable.code == "DEPTH"
