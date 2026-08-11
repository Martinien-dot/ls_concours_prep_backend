from rest_framework import generics, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from core.storage_backends import PrivateVideoStorage
from .models import Concours, Annee, Epreuve
from .serializers import ConcoursSerializer, AnneeSerializer, EpreuveSerializer


class ConcoursListView(generics.ListAPIView):
    """List all available exam competitions (e.g., ENS, CNC, ENAM)."""
    queryset = Concours.objects.all()
    serializer_class = ConcoursSerializer
    permission_classes = (permissions.IsAuthenticated,)


class AnneeListView(generics.ListAPIView):
    """List available examination years in descending order."""
    queryset = Annee.objects.all().order_by('-valeur')
    serializer_class = AnneeSerializer
    permission_classes = (permissions.IsAuthenticated,)


class EpreuveListView(generics.ListAPIView):
    """
    List exam papers with optional filtering by `concours` (ID) and `annee` (ID).
    """
    serializer_class = EpreuveSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        queryset = Epreuve.objects.select_related('concours', 'annee').all()
        concours_id = self.request.query_params.get('concours')
        annee_id = self.request.query_params.get('annee')

        if concours_id:
            queryset = queryset.filter(concours_id=concours_id)
        if annee_id:
            queryset = queryset.filter(annee_id=annee_id)

        return queryset


class EpreuveDetailView(generics.RetrieveAPIView):
    """Retrieve details for a single exam paper."""
    queryset = Epreuve.objects.select_related('concours', 'annee').all()
    serializer_class = EpreuveSerializer
    permission_classes = (permissions.IsAuthenticated,)


class EpreuveStreamView(APIView):
    """
    Returns a temporary pre-signed Cloudflare R2 URL for streaming an Epreuve's HLS video solution.
    Requires an active Premium subscription (`is_premium=True`).
    """
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, pk):
        epreuve = get_object_or_404(Epreuve, pk=pk)

        # 1. Access Control: Require Premium membership
        if not request.user.is_premium:
            return Response(
                {"detail": "Un abonnement Premium actif est requis pour visionner la vidéo de cette épreuve."},
                status=status.HTTP_403_FORBIDDEN
            )

        # 2. Check video availability and processing status
        if not epreuve.is_video_processed or not epreuve.corrige_video_hls_id:
            return Response(
                {"detail": "La vidéo corrigée n'est pas encore disponible ou est en cours de traitement."},
                status=status.HTTP_409_CONFLICT
            )

        # 3. Generate 1-hour pre-signed URL from Cloudflare R2
        r2_storage = PrivateVideoStorage()
        stream_url = r2_storage.url(epreuve.corrige_video_hls_id)

        return Response({
            "epreuve_id": epreuve.id,
            "concours": epreuve.concours.nom,
            "annee": epreuve.annee.valeur,
            "titre": epreuve.titre,
            "stream_url": stream_url,
            "format": "hls"
        }, status=status.HTTP_200_OK)