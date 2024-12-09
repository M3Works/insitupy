from insitupy.variables.base_variables import ExtendableVariables, \
    MeasurementDescription


class BaseMetadataVariables(ExtendableVariables):
    """
    Variables expected to be found in file headers
    These are variables associated with larger dataset
    """
    DATETIME = MeasurementDescription(
        'datetime', "Combined date and time",
        ["Date/Local Standard Time", "date/local_standard_time", "datetime",
         "date&time", "date/time", "date/local_time"],
        True
    )
    DATE = MeasurementDescription(
        'date', "Measurement Date (only date column)",
        ['date_dd_mmm_yy', 'date']
    )
    TIME = MeasurementDescription(
        'time', "Measurement time",
        ['time_gmt', 'time']
    )
    TIME_BOUND_PIT = MeasurementDescription(
        "Time start/end",
        "Time of first or last pit measurement",
        ["Time start/end", "time_start/end"]
    )
    SITE_NAME = MeasurementDescription(
        "site_name", "Name of campaign site",
        ['location'], True
    )
    SITE_ID = MeasurementDescription(
        "site_id", "ID within campaign site",
        ['site'], True
    )
    PIT_ID = MeasurementDescription(
        "pit_id", "ID of snow pit",
        ['pitid'], True
    )
