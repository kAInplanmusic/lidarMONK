#!/usr/bin/env python3
"""Inspect local iPhone originals without claiming unknown depth units are metres."""
import argparse
import json
import shutil
import subprocess
from pathlib import Path

HEIF = {'.heic', '.heif', '.avif'}
VIDEO = {'.mov', '.mp4', '.m4v', '.3gp', '.avi', '.mkv', '.webm', '.mts', '.m2ts', '.prores'}
IMAGES = {'.jpg', '.jpeg', '.png', '.tif', '.tiff', '.dng', '.raw', '.cr2', '.cr3', '.nef', '.nrw', '.arw', '.raf', '.rw2', '.orf', '.webp', '.jxl', '.bmp', '.gif'}

def metadata(path):
    if not shutil.which('exiftool'):
        return {'status': 'ExifTool nicht installiert; ausführliche Metadatenprüfung übersprungen'}
    try:
        cmd = ['exiftool', '-json', '-G1', '-a', '-s', '--', str(path)]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=45, check=True)
        data = json.loads(proc.stdout)[0]
        # Report only relevant keys; camera/location metadata stays on device.
        terms = ('depth', 'disparity', 'auxiliary', 'camera', 'lens', 'imagewidth', 'imageheight', 'filetype', 'makernote')
        relevant = {k: v for k, v in data.items() if any(t in k.lower() for t in terms) and not isinstance(v, (dict, list))}
        return {'status': 'Metadaten ausgelesen; keine Bestätigung metrischer Tiefe', 'fields': relevant}
    except (OSError, ValueError, subprocess.SubprocessError, IndexError) as exc:
        return {'status': 'Metadatenprüfung fehlgeschlagen', 'error': str(exc)}


def inspect(path, output_dir=None):
    path = Path(path)
    result = {'file': path.name, 'bytes': path.stat().st_size, 'kind': path.suffix.lower(),
              'status': 'nicht ausgewertet', 'metric_depth': False, 'warnings': [], 'items': []}
    result['metadata'] = metadata(path)
    if path.suffix.lower() in HEIF:
        try:
            import pillow_heif
        except ImportError:
            result['status'] = 'Abhängigkeit pillow-heif fehlt'
            result['warnings'].append('Ohne HEIF-Decoder kann nicht festgestellt werden, ob eine Tiefenkarte enthalten ist.')
            return result
        try:
            container = pillow_heif.open_heif(str(path), convert_hdr_to_8bit=False)
            for index, image in enumerate(container):
                info = image.info
                depth_images = info.get('depth_images', [])
                auxiliary = info.get('aux', {})
                record = {'image_index': index, 'primary': bool(info.get('primary')), 'size': list(image.size),
                          'depth_images': [], 'auxiliary_types': list(auxiliary.keys())}
                for depth_index, depth in enumerate(depth_images):
                    d = {'index': depth_index, 'size': list(depth.size), 'mode': depth.mode,
                         'unit': 'unbekannt', 'source': 'unbekannt'}
                    if output_dir is not None:
                        output_dir = Path(output_dir)
                        output_dir.mkdir(parents=True, exist_ok=True)
                        # Each source has its own directory; never overwrite earlier exports.
                        dest = output_dir / f'{path.stem}-bild{index}-tiefe{depth_index}.png'
                        if dest.exists():
                            n = 1
                            while dest.with_stem(dest.stem + f'-{n}').exists(): n += 1
                            dest = dest.with_stem(dest.stem + f'-{n}')
                        try:
                            depth.to_pillow().save(dest)
                            d['preview_file'] = str(dest)
                            d['preview_note'] = 'Dekodiertes Graustufenbild; kein metrischer Tiefenexport.'
                        except Exception as exc:
                            d['preview_error'] = str(exc)
                    record['depth_images'].append(d)
                result['items'].append(record)
            count = sum(len(x['depth_images']) for x in result['items'])
            result['status'] = f'{count} Tiefenzusatzbild(er) vom Decoder erkannt' if count else 'Keine vom Decoder unterstützte Tiefenkarte erkannt'
            result['warnings'].append('Unbekannte/unsupported HEIF-Zusatzbilder können übersehen werden; ein negativer Befund ist kein Ausschluss.')
            result['warnings'].append('Werte und Sensortyp sind nicht kalibriert/verifiziert; ein 5-m-Anteil kann nicht berechnet werden.')
        except Exception as exc:
            result['status'] = 'HEIF-Datei konnte nicht vollständig geprüft werden'
            result['warnings'].append(str(exc))
    elif path.suffix.lower() in VIDEO:
        if not shutil.which('ffprobe'):
            result['status'] = 'ffprobe fehlt'; result['warnings'].append('Videospuren können nicht aufgelistet werden.')
        else:
            try:
                cmd = ['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(path)]
                run = subprocess.run(cmd, capture_output=True, text=True, timeout=45, check=True)
                data = json.loads(run.stdout)
                for stream in data.get('streams', []):
                    result['items'].append({k: stream.get(k) for k in ('index', 'codec_name', 'codec_type', 'width', 'height', 'tags') if stream.get(k) is not None})
                result['status'] = f"{len(result['items'])} Videodatei-Spur(en) aufgelistet"
                result['warnings'].append('Spurliste allein weist keine nutzbaren LiDAR-Tiefenwerte nach; Spezialspuren werden nicht dekodiert.')
            except (subprocess.SubprocessError, ValueError, OSError) as exc:
                result['status'] = 'Videoanalyse fehlgeschlagen'; result['warnings'].append(str(exc))
    else:
        result['status'] = 'Metadatenprüfung' if path.suffix.lower() in IMAGES else 'Unbekanntes Format: nur allgemeine Metadatenprüfung'
        result['warnings'].append('Eingebettete Tiefenkarten werden in diesem Format noch nicht decodiert; Metadaten allein sind kein Nachweis für nutzbare Tiefenwerte.')
    return result


def main():
    parser = argparse.ArgumentParser(description='Originale iPhone-Dateien lokal auf Tiefenbilder oder Videospuren untersuchen')
    parser.add_argument('files', nargs='+', help='HEIC/HEIF/AVIF oder MOV/MP4')
    parser.add_argument('--export-depth', metavar='ORDNER', help='Erkannte Tiefenbilder als nichtmetrische PNG-Kopie exportieren')
    args = parser.parse_args()
    results = []
    for name in args.files:
        try: results.append(inspect(name, args.export_depth))
        except OSError as exc: results.append({'file': name, 'status': 'Dateifehler', 'warnings': [str(exc)]})
    print(json.dumps(results, ensure_ascii=False, indent=2))

if __name__ == '__main__': main()
