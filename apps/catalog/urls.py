from django.urls import path
from .views import (
    ConcoursListView,
    AnneeListView,
    EpreuveListView,
    EpreuveDetailView,
    EpreuveStreamView,
)

urlpatterns = [
    path('concours/', ConcoursListView.as_view(), name='concours-list'),
    path('annees/', AnneeListView.as_view(), name='annee-list'),
    path('epreuves/', EpreuveListView.as_view(), name='epreuve-list'),
    path('epreuves/<int:pk>/', EpreuveDetailView.as_view(), name='epreuve-detail'),
    path('epreuves/<int:pk>/stream/', EpreuveStreamView.as_view(), name='epreuve-stream'),
]