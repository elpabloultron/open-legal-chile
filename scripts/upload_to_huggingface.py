#!/usr/bin/env python3
"""
Publicador oficial de Open Legal Chile en Hugging Face Datasets Hub
(pablobenavidesj/doctrina-jurisprudencia-chile)

Sube de forma integral:
1. Dataset Card (README.md) con Dataset Viewer interactivo para 5 splits.
2. Jurisprudencia completa de Tribunales Ambientales (885 sentencias en data/jurisprudencia/ambiental_sentencias.jsonl).
3. Jurisprudencia del Tribunal Constitucional (38 sentencias en data/jurisprudencia/tc_sentencias.jsonl).
4. Jurisprudencia de la Corte Suprema (10 fallos rectores en data/jurisprudencia/cs_sentencias.jsonl).
5. Compendio dogmático y forense de Criterios Jurisprudenciales de las Cortes (doctrina/ambiental/).
6. Obras doctrinales y Guías de la Academia Judicial.
7. Artefactos del Knowledge Graph (LegalGraphify).

Uso:
  python scripts/upload_to_huggingface.py [--token HF_TOKEN] [--repo REPO_ID]
"""

import os
import sys
import argparse

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from online_library_sync import OnlineLibrarySyncManager, resolver_token_hf

def main():
    parser = argparse.ArgumentParser(description="Publicar dataset en Hugging Face")
    parser.add_argument("--token", "-t", type=str, default=None, help="Token con rol Write de Hugging Face")
    parser.add_argument("--repo", "-r", type=str, default="pablobenavidesj/doctrina-jurisprudencia-chile", help="ID del repositorio en Hugging Face")
    args = parser.parse_args()

    token = resolver_token_hf(args.token)
    if not token:
        print("\n❌ Error: No se encontró ningún token de Hugging Face.")
        print("\nPara obtener tu token:")
        print("1. Ingresa a: https://huggingface.co/settings/tokens")
        print("2. Crea un token con rol 'Write'.")
        print("3. Ejecuta cualquiera de estas opciones:")
        print("   a) python scripts/upload_to_huggingface.py --token TU_TOKEN_AQUI")
        print("   b) export HF_TOKEN=TU_TOKEN_AQUI && python scripts/upload_to_huggingface.py")
        print("   c) printf '%s' 'TU_TOKEN_AQUI' > ~/.openlegal/hf_token\n")
        sys.exit(1)

    print(f"\n🚀 Iniciando sincronización y subida a Hugging Face ({args.repo})...")
    mgr = OnlineLibrarySyncManager()
    
    # 1. Preparar Dataset Card actualizada
    card_path = mgr.preparar_dataset_card_huggingface(repo_id=args.repo)
    print(f"✓ Dataset Card generada en: {card_path}")

    # 2. Publicar dataset completo
    res = mgr.publicar_en_huggingface(repo_id=args.repo, token=token)
    if res.get("exito"):
        print("\n✅ ¡ÉXITO! Dataset publicado exitosamente.")
        print(f"🔗 URL: {res.get('url')}")
        if res.get("space_url"):
            print(f"🪐 Space Visualizador: {res.get('space_url')}")
    else:
        print(f"\n❌ Error al publicar: {res.get('error')}")
        if res.get("instrucciones"):
            print(f"ℹ️  {res.get('instrucciones')}")
        sys.exit(1)

if __name__ == "__main__":
    main()
