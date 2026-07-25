# apps/authentication/authentication.py
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed

class SingleActiveSessionJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        header = self.get_header(request)
        if header is None:
            return None

        raw_token = self.get_raw_token(header)
        if raw_token is None:
            return None

        validated_token = self.get_validated_token(raw_token)
        user = self.get_user(validated_token)

        # Extraction du jti du token actuel
        jti = validated_token.get("jti")

        # Validation de concomitance stricte
        if user.active_jti and user.active_jti != jti:
            raise AuthenticationFailed(
                "Cette session n'est plus active. Une connexion a été établie sur un autre appareil.",
                code="concurrent_session"
            )

        return user, validated_token