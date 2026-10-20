from lerner_lab_to_nwb.seiler_2024.seiler_2024fiberphotometryinterface import (
    DLS_FIBER_COORDINATES_IN_MM,
    DMS_FIBER_COORDINATES_IN_MM,
    LATERAL_SNC_INJECTION_COORDINATES_IN_MM,
    MEDIAL_SNC_INJECTION_COORDINATES_IN_MM,
)


def test_coordinates_match_methods():
    # Methods: DMS (AP 0.8, ML 1.5, DV −2.8), DLS (AP −0.1, ML 2.8, DV −3.5),
    # medial SNc (AP −3.1, ML 0.8, DV −4.7), lateral SNc (AP −3.1, ML 1.3, DV −4.2)
    assert DMS_FIBER_COORDINATES_IN_MM == (0.8, 1.5, -2.8)
    assert DLS_FIBER_COORDINATES_IN_MM == (-0.1, 2.8, -3.5)
    assert MEDIAL_SNC_INJECTION_COORDINATES_IN_MM == (-3.1, 0.8, -4.7)
    assert LATERAL_SNC_INJECTION_COORDINATES_IN_MM == (-3.1, 1.3, -4.2)
