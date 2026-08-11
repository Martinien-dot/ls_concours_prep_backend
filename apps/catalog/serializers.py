from rest_framework import serializers
from .models import Concours, Annee, Epreuve


class ConcoursSerializer(serializers.ModelSerializer):
    class Meta:
        model = Concours
        fields = ('id', 'nom', 'description')


class AnneeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Annee
        fields = ('id', 'valeur')


class EpreuveSerializer(serializers.ModelSerializer):
    sujet_pdf_url = serializers.SerializerMethodField()
    corrige_pdf_url = serializers.SerializerMethodField()
    is_premium_unlocked = serializers.SerializerMethodField()

    class Meta:
        model = Epreuve
        fields = (
            'id',
            'concours',
            'annee',
            'titre',
            'sujet_pdf_url',
            'corrige_pdf_url',
            'corrige_video_hls_id',
            'is_video_processed',
            'is_premium_unlocked',
        )

    def get_sujet_pdf_url(self, instance) -> str | None:
        return instance.sujet_pdf.url if instance.sujet_pdf else None

    def get_corrige_pdf_url(self, instance) -> str | None:
        return instance.corrige_pdf.url if instance.corrige_pdf else None

    def get_is_premium_unlocked(self, instance) -> bool:
        request = self.context.get('request')
        return bool(request and request.user.is_authenticated and request.user.is_premium)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')

        # Redact premium media URLs if user lacks active Premium status
        user_is_premium = request and request.user.is_authenticated and request.user.is_premium
        if not user_is_premium:
            data['corrige_pdf_url'] = None
            data['corrige_video_hls_id'] = None

        return data