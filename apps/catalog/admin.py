import threading
from django.contrib import admin, messages
from django.db import transaction, close_old_connections
from .models import Concours, Annee, Epreuve
from .services.hls_service import transcode_and_upload_epreuve_hls


@admin.register(Concours)
class ConcoursAdmin(admin.ModelAdmin):
    list_display = ('id', 'nom', 'description')
    search_fields = ('nom',)


@admin.register(Annee)
class AnneeAdmin(admin.ModelAdmin):
    list_display = ('id', 'valeur')
    ordering = ('-valeur',)


@admin.register(Epreuve)
class EpreuveAdmin(admin.ModelAdmin):
    list_display = ('id', 'concours', 'annee', 'titre', 'is_video_processed')
    list_filter = ('concours', 'annee', 'is_video_processed')
    search_fields = ('titre', 'concours__nom')
    readonly_fields = ('corrige_video_hls_id', 'is_video_processed')

    class Media:
        js = ('catalog/js/upload_progress.js',)

    def save_model(self, request, obj, form, change):
        # 1. Détecter si on est en mode "mise à jour" ET si la vidéo a été modifiée
        if change and 'corrige_raw_video' in form.changed_data:
            # Réinitialiser les statuts pour forcer le nouveau traitement HLS
            obj.is_video_processed = False
            obj.corrige_video_hls_id = None

        # 2. Sauvegarder l'instance normalement (cela met aussi à jour les PDF si modifiés)
        super().save_model(request, obj, form, change)

        # 3. Lancer le traitement HLS si une vidéo est présente et non traitée
        if obj.corrige_raw_video and not obj.is_video_processed:
            epreuve_id = obj.id

            def start_background_transcoding():
                def run_transcoding():
                    close_old_connections()
                    try:
                        epreuve_instance = Epreuve.objects.get(id=epreuve_id)
                        transcode_and_upload_epreuve_hls(epreuve_instance)
                    except Exception as e:
                        print(f"[HLS Transcoding Error] Epreuve {epreuve_id}: {str(e)}")
                    finally:
                        close_old_connections()

                thread = threading.Thread(target=run_transcoding)
                thread.daemon = True
                thread.start()

            transaction.on_commit(start_background_transcoding)

            messages.info(
                request,
                "Les modifications ont été enregistrées. Le nouveau traitement vidéo s'exécute en arrière-plan. "
                "Veuillez rafraîchir la page dans quelques instants."
            )