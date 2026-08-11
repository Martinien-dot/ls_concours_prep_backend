from django.db import models


class Concours(models.Model):
    nom = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.nom


class Annee(models.Model):
    valeur = models.IntegerField(unique=True)

    def __str__(self):
        return str(self.valeur)


class Epreuve(models.Model):
    concours = models.ForeignKey(Concours, on_delete=models.CASCADE, related_name='epreuves')
    annee = models.ForeignKey(Annee, on_delete=models.CASCADE, related_name='epreuves')
    titre = models.CharField(max_length=255)
    sujet_pdf = models.FileField(upload_to='pdfs/sujets/', null=True, blank=True)
    corrige_pdf = models.FileField(upload_to='pdfs/corriges/', null=True, blank=True)

    # Video Correction Fields
    corrige_raw_video = models.FileField(upload_to='raw_videos/', null=True, blank=True)
    corrige_video_hls_id = models.CharField(max_length=255, blank=True, null=True)
    is_video_processed = models.BooleanField(default=False)

    class Meta:
        unique_together = ('concours', 'annee', 'titre')

    def __str__(self):
        return f"{self.concours.nom} {self.annee.valeur} - {self.titre}"