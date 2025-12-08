from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

import time
import random
import requests

from concurrent import futures

CALLBACK_URL = "http://0.0.0.0:8000/stocks/"

executor = futures.ThreadPoolExecutor(max_workers=1)

def get_random_status(pk):
    time.sleep(5)
    return {
      "id": pk,
      "status": bool(random.getrandbits(1)),
    }

def status_callback(task):
    try:
      result = task.result()
      print(result)
    except futures._base.CancelledError:
      return

    nurl = str(CALLBACK_URL+str(result["id"])+'/put/')
    answer = {"is_growing": result["status"]}
    requests.put(nurl, data=answer, timeout=3)

@api_view(['POST'])
def set_status(request):
    if "pk" in request.data.keys():
        id = request.data["pk"]

        task = executor.submit(get_random_status, id)
        task.add_done_callback(status_callback)
        return Response(status=status.HTTP_200_OK)
    return Response(status=status.HTTP_400_BAD_REQUEST)
