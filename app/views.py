from concurrent import futures
from random import randint
from time import sleep
from typing import cast

import requests
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response

from app.models import LightRequest
from calc_service.settings import CALLBACK_KEY, CALLBACK_URL

REQUIRED_ILLUMINATION_LUX = 500

executor = futures.ThreadPoolExecutor(max_workers=10)


def get_lamp_numbers(light_request: LightRequest) -> LightRequest:
    for lrtl in light_request["light_request_to_lamp"]:
        lrtl["number"] = int(
            (REQUIRED_ILLUMINATION_LUX * lrtl["area_m2"])
            / lrtl["lamp"]["luminous_flux_lm"]
        )
    light_request["light_request_to_lamp"] = sorted(
        light_request["light_request_to_lamp"],
        key=lambda lrtl: lrtl["lamp"]["power_w"] * lrtl["number"],
    )
    i = 0
    while (
        sum(
            map(
                lambda lrtl: lrtl["lamp"]["power_w"] * lrtl["number"],
                light_request["light_request_to_lamp"],
            )
        )
        > light_request["max_total_power_w"]
    ):
        if light_request["light_request_to_lamp"][i]["number"] > 0:
            light_request["light_request_to_lamp"][i]["number"] -= 1
        i = (i + 1) % len(light_request["light_request_to_lamp"])
    sleep(randint(3, 8))  # emulate long calculations
    return light_request


def lamp_numbers_callback(task: futures.Future[LightRequest]):
    try:
        result = task.result()
    except futures._base.CancelledError:
        return

    url = CALLBACK_URL.format(result["id"])
    data = {
        "key": CALLBACK_KEY,
        "light_request_to_lamp": [
            {"lamp_id": lrtl["lamp"]["id"], "number": lrtl["number"]}
            for lrtl in result["light_request_to_lamp"]
        ],
    }
    requests.put(url, json=data, timeout=3)


@api_view(["POST"])
def lamp_numbers(request: Request):
    try:
        json = cast(dict, request.data)
        light_request = LightRequest(
            id=json["id"],
            max_total_power_w=json["max_total_power_w"],
            light_request_to_lamp=json["light_request_to_lamp"],
        )
        task = executor.submit(get_lamp_numbers, light_request)
        task.add_done_callback(lamp_numbers_callback)
        return Response(status=status.HTTP_200_OK)
    except Exception:
        return Response(status=status.HTTP_400_BAD_REQUEST)
