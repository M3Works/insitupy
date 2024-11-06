from insitupy.variables.base_primary_variables import BasePrimaryVariables
from insitupy.variables.base_variables import MeasurementDescription


class SnowExPrimaryVariables(BasePrimaryVariables):
    """
    Extend the primary variables to include more mappings
    for snowex
    """
    # TODO: Some of these move to snowexdb
    # TODO: unify with snowexdb

    EQUIVALENT_DIAMETER = MeasurementDescription(
        'equivalent_diameter', "",
        ['deq']
    )

    INSTRUMENT = MeasurementDescription(
        'instrument', "Instrument of measurement",
        ['smp_serial_number', 'measurement_tool', 'instrument']
    )
