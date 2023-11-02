import sys
import traceback

from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler

from .settings.base import LOGGEER


def my_exception_handler(exc, context):
    # Call REST framework's default exception handler first,
    # if isinstance(exc, DRFValidationError):
    # if hasattr(exc, 'message_dict'):
    #     exc = DRFValidationError(detail=exc.message_dict)
    # else:
    #     exc = DRFValidationError(detail=exc.message)
    # to get the standard error response.
    response = exception_handler(exc, context)
    exception_type, exception_object, exception_traceback = sys.exc_info()
    LOGGEER.debug(traceback.format_exc())
    custom_response = {
        "error": {"message": str(exc)},
        "status": "0",
        "message": "failed",
    }
    if response is not None:
        if isinstance(exc, ValidationError):
            for err in response.data:
                response.data[err] = response.data[err][0]
            custom_response["error"] = response.data

    return Response(custom_response, status=status.HTTP_400_BAD_REQUEST)
