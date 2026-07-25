from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import ScopedRateThrottle
from .serializers import ActivateCodeSerializer
from .services import activate_premium_code


class ActivateCodeView(generics.GenericAPIView):
    """
    Validates a submitted Mobile Money access code and grants 30 days of Premium.
    Rate-limited to 5 attempts per minute.
    """
    serializer_class = ActivateCodeSerializer
    permission_classes = (IsAuthenticated,)
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = 'premium_code_activation'

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        raw_code = serializer.validated_data['code']
        user = activate_premium_code(request.user, raw_code)

        return Response({
            'message': 'Premium access activated successfully.',
            'is_premium': user.is_premium,
            'premium_until': user.premium_until,
        }, status=status.HTTP_200_OK)