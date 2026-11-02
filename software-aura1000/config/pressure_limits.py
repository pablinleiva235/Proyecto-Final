"""Pressure setpoint limits derived from the oxygen flow."""

PRESSURE_MINIMUM_BY_O2_FLOW = (
    (0.0, 0.83),
    (1.0, 1.14),
    (2.0, 1.51),
    (3.0, 1.86),
    (4.0, 2.23),
    (5.0, 2.63),
    (6.0, 3.0),
)

THROTTLE_REST_PRESSURE_THRESHOLD_TORR = 0.08


def minimum_process_pressure(o2_flow):
    """Return the linearly interpolated minimum pressure, in Torr."""
    flow = float(o2_flow)
    if flow <= PRESSURE_MINIMUM_BY_O2_FLOW[0][0]:
        return PRESSURE_MINIMUM_BY_O2_FLOW[0][1]
    for (flow_a, pressure_a), (flow_b, pressure_b) in zip(
        PRESSURE_MINIMUM_BY_O2_FLOW, PRESSURE_MINIMUM_BY_O2_FLOW[1:]
    ):
        if flow <= flow_b:
            ratio = (flow - flow_a) / (flow_b - flow_a)
            return pressure_a + ratio * (pressure_b - pressure_a)
    return PRESSURE_MINIMUM_BY_O2_FLOW[-1][1]
