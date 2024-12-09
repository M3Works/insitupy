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
        ["swe_mm", "swe"], auto_remap=True
    )
    DEPTH = MeasurementDescription(
        "depth", "top or center depth of measurement",
        [
            "depth", "top", "sample_top_height", "hs",
            "depth_m", 'snowdepthfilter(m)', 'snowdepthfilter',
            'height'
        ], auto_remap=True
    )
    BOTTOM_DEPTH = MeasurementDescription(
        "bottom_depth", "Lower edge of measurement",
        ["bottom", "bottom_depth"], auto_remap=True
    )
    DENSITY_A = MeasurementDescription(
        "density", "measured snow density",
        ["density_a"], auto_remap=False, match_on_code=False
    )
    DENSITY_B = MeasurementDescription(
        "density", "measured snow density",
        ["density_b"], auto_remap=False, match_on_code=False
    )
    DENSITY_C = MeasurementDescription(
        "density", "measured snow density",
        ["density_c"], auto_remap=False, match_on_code=False
    )
    DENSITY = MeasurementDescription(
        "density", "measured snow density",
        [
            "density", "avg_density",
            "avgdensity", 'density_mean'
        ], auto_remap=True
    )
    LAYER_THICKNESS = MeasurementDescription(
        "layer_thickness", "thickness of layer", auto_remap=True
    )
    SNOW_TEMPERATURE = MeasurementDescription(
        "snow_temperature", "Snowpack Temperature",
        ["temperature", "temperature_deg_c"], auto_remap=True
    )
    LWC_A = MeasurementDescription(
        "liquid_water_content", "Liquid water content",
        ["lwc_vol_a"], auto_remap=False, match_on_code=False
    )
    LWC_B = MeasurementDescription(
        "liquid_water_content", "Liquid water content",
        ["lwc_vol_b"], auto_remap=False, match_on_code=False
    )
    LWC = MeasurementDescription(
        "liquid_water_content", "Liquid water content",
        ["lwc", "lwc_vol"], auto_remap=True
    )
    PERMITTIVITY_A = MeasurementDescription(
        "permittivity", "Permittivity",
        ["permittivity_a", 'dielectric_constant_a'],
        auto_remap=False, match_on_code=False
    )
    PERMITTIVITY_B = MeasurementDescription(
        "permittivity", "Permittivity",
        ["permittivity_b", 'dielectric_constant_b'],
        auto_remap=False, match_on_code=False
    )
    PERMITTIVITY = MeasurementDescription(
        "permittivity", "Permittivity",
        ["permittivity", 'dielectric_constant'], True
    )
    GRAIN_SIZE = MeasurementDescription(
        "grain_size", "Grain Size",
        ["grain_size"], auto_remap=True
    )
    GRAIN_TYPE = MeasurementDescription(
        "grain_type", "Grain Type",
        ["grain_type"], auto_remap=True
    )
    HAND_HARDNESS = MeasurementDescription(
        "hand_hardness", "Hand Hardness",
        ["hand_hardness"], auto_remap=True
    )
    MANUAL_WETNESS = MeasurementDescription(
        "manual_wetness", "Manual Wetness",
        ["manual_wetness"], auto_remap=True
    )
