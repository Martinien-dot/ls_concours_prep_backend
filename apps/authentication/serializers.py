from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth import get_user_model

User = get_user_model()


class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'password')

    def create(self, validated_data):
        # Inscription publique : rôle forcé à STUDENT pour éviter toute élévation de privilèges
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            role=User.Role.STUDENT
        )
        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)

        # Extraction du jti du token d'accès généré
        access_token_str = data['access']
        access_token = AccessToken(access_token_str)
        jti = access_token['jti']

        # Mise à jour du jti actif de l'utilisateur pour invalider immédiatement les autres sessions
        self.user.active_jti = jti
        self.user.save(update_fields=['active_jti'])

        # Données de profil incluses dans la réponse du login
        data['user'] = {
            'id': self.user.id,
            'email': self.user.email,
            'username': self.user.username,
            'role': self.user.role,
            'is_premium': self.user.is_premium,
            'premium_until': self.user.premium_until,
        }
        return data


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'role', 'is_premium', 'premium_until')
        # Empêche la modification de ces champs sensibles par une simple requête PATCH/PUT
        read_only_fields = ('role', 'is_premium', 'premium_until')