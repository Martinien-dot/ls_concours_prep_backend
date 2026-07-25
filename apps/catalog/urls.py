from django.urls import path
from .views import ConcoursListView, AnneeListView, EpreuveListView, EpreuveDetailView

urlpatterns = [
    path('concours/', ConcoursListView.as_view(), name='catalog_concours_list'),
    path('annees/', AnneeListView.as_view(), name='catalog_annee_list'),
    path('epreuves/', EpreuveListView.as_view(), name='catalog_epreuve_list'),
    path('epreuves/<int:pk>/', EpreuveDetailView.as_view(), name='catalog_epreuve_detail'),
]