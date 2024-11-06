from insitupy.variables.base_variables import ExtendableVariables, \
    MeasurementDescription


class BasePrimaryVariables(ExtendableVariables):
    """
    Variables expected to be found in COLUMNS
    These are variables associated with the line-by-line
    measurements
    """
    # TODO optional multisample list to check

    SWE = MeasurementDescription(
        "SWE", "Snow Water Equivalent",
        ["swe_mm", "swe"]
    )
    DEPTH = MeasurementDescription(
        "depth", "top or center depth of measurement",
        [
            "depth", "top", "sample_top_height", "hs",
            "depth_m", 'snowdepthfilter(m)', 'snowdepthfilter',
            'height'
        ], True
    )
    BOTTOM_DEPTH = MeasurementDescription(
        "bottom_depth", "Lower edge of measurement",
        ["bottom", "bottom_depth"], True
    )
    DENSITY = MeasurementDescription(
        "density", "measured snow density",
        [
            "density", "density_a", "density_b", "density_c", "avg_density",
            "avgdensity", 'density_mean'
        ]
    )
    LAYER_THICKNESS = MeasurementDescription(
        "layer_thickness", "thickness of layer"
    )
    SNOW_TEMPERATURE = MeasurementDescription(
        "snow_temperature", "Snowpack Temperature",
        ["temperature", "temperature_deg_c"]
    )
    LWC = MeasurementDescription(
        "liquid_water_content", "Liquid water content",
        ["lwc_vol_a", "lwc_vol_b", "lwc", "lwc_vol"]
    )
    PERMITTIVITY = MeasurementDescription(
        "permittivity", "Permittivity",
        ["permittivity_a", "permittivity_b", "permittivity",
         'dielectric_constant', 'dielectric_constant_a',
         'dielectric_constant_b'], True
    )
    GRAIN_SIZE = MeasurementDescription(
        "grain_size", "Grain Size",
        ["grain_size"]
    )
    GRAIN_TYPE = MeasurementDescription(
        "grain_type", "Grain Type",
        ["grain_type"]
    )
    HAND_HARDNESS = MeasurementDescription(
        "hand_hardness", "Hand Hardness",
        ["hand_hardness"]
    )
    MANUAL_WETNESS = MeasurementDescription(
        "manual_wetness", "Manual Wetness",
        ["manual_wetness"]
    )
