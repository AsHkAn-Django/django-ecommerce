from rest_framework.views import APIView
from rest_framework.response import Response


class CompeletedAPIView(APIView):
    def get(self, request):
        return Response({"status": "success", "message": "Payment Completed"})


class CanceledAPIView(APIView):
    def get(self, request):
        return Response({"status": "canceled", "message": "Payment Canceled"})
