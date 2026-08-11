import os
import subprocess
import tempfile
from core.storage_backends import PrivateVideoStorage


def transcode_and_upload_epreuve_hls(epreuve) -> str:
    """
    Transcodes an Epreuve's raw MP4 video into HLS (.m3u8 + .ts segments) using FFmpeg,
    uploads the HLS package to private Cloudflare R2 storage, and saves the playlist key
    in `corrige_video_hls_id`.
    """
    if not epreuve.corrige_raw_video:
        raise ValueError("Cette épreuve n'a aucun fichier vidéo brut rattaché.")

    with tempfile.TemporaryDirectory() as temp_dir:
        # 1. Download/stream the video from storage (R2) into a temporary local file
        input_temp_path = os.path.join(temp_dir, 'source_raw.mp4')
        with open(input_temp_path, 'wb') as temp_file:
            for chunk in epreuve.corrige_raw_video.chunks():
                temp_file.write(chunk)

        output_playlist = os.path.join(temp_dir, 'index.m3u8')
        segment_pattern = os.path.join(temp_dir, 'segment_%03d.ts')

        # 2. Execute FFmpeg command using the temporary local file
        # L'ajout du filtre -vf 'scale=trunc(iw/2)*2:trunc(ih/2)*2' garantit
        # des dimensions paires requises par libx264.
        ffmpeg_cmd = [
            'ffmpeg', '-y',
            '-i', input_temp_path,
            '-vf', 'scale=trunc(iw/2)*2:trunc(ih/2)*2',
            '-c:v', 'libx264', '-crf', '22', '-preset', 'fast',
            '-c:a', 'aac', '-b:a', '128k',
            '-hls_time', '4',
            '-hls_playlist_type', 'vod',
            '-hls_segment_filename', segment_pattern,
            output_playlist
        ]

        result = subprocess.run(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg transcoding failed: {result.stderr.decode('utf-8')}")

        # 3. Upload generated HLS files to Cloudflare R2 under 'media/videos/hls/epreuves/<id>/'
        r2_storage = PrivateVideoStorage()
        r2_folder_key = f"hls/epreuves/{epreuve.id}"

        for file_name in os.listdir(temp_dir):
            if file_name == 'source_raw.mp4':
                continue  # Skip uploading the local raw source copy

            local_file_path = os.path.join(temp_dir, file_name)
            if os.path.isfile(local_file_path):
                r2_file_key = f"{r2_folder_key}/{file_name}"
                with open(local_file_path, 'rb') as f:
                    r2_storage.save(r2_file_key, f)

        # 4. Save master playlist path in `corrige_video_hls_id`
        master_playlist_key = f"{r2_folder_key}/index.m3u8"
        epreuve.corrige_video_hls_id = master_playlist_key
        epreuve.is_video_processed = True
        epreuve.save()

        return master_playlist_key