from typing import TypedDict


class Lamp(TypedDict):
    id: int
    power_w: float
    luminous_flux_lm: float
    scattering_angle_deg: float


class LightRequestToLamp(TypedDict):
    request_id: int
    lamp: Lamp
    area_m2: float
    number: int


class LightRequest(TypedDict):
    id: int
    max_total_power_w: float
    light_request_to_lamp: list[LightRequestToLamp]
