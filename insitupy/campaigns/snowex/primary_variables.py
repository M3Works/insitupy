from insitupy.variables.base_primary_variables import BasePrimaryVariables
from insitupy.variables.base_variables import MeasurementDescription


class SnowExPrimaryVariables(BasePrimaryVariables):
    """
    Extend the primary variables to include more mappings
    for snowex
    """

    EQUIVALENT_DIAMETER = MeasurementDescription(
        'equivalent_diameter', "",
        ['deq'], auto_remap=True
    )

    INSTRUMENT = MeasurementDescription(
        'instrument', "Instrument of measurement",
        ['smp_serial_number', 'measurement_tool', 'instrument'], auto_remap=True
    )
