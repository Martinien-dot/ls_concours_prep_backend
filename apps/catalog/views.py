from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .models import Concours, Annee, Epreuve
from .serializers import ConcoursSerializer, AnneeSerializer, EpreuveSerializer


class ConcoursListView(generics.ListAPIView):
    """List all available exam competitions (e.g., ENS)."""
    queryset = Concours.objects.all()
    serializer_class = ConcoursSerializer
    permission_classes = (IsAuthenticated,)


class AnneeListView(generics.ListAPIView):
    """List available examination years."""
    queryset = Annee.objects.all().order_by('-valeur')
    serializer_class = AnneeSerializer
    permission_classes = (IsAuthenticated,)


class EpreuveListView(generics.ListAPIView):
    """
    List exam papers with optional filtering by concours_id and annee_id.
    """
    serializer_class = EpreuveSerializer
    permission_classes = (IsAuthenticated,)

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
    permission_classes = (IsAuthenticated,)