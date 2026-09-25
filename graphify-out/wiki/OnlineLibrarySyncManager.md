# OnlineLibrarySyncManager

> 28 nodes · cohesion 0.10

## Key Concepts

- **OnlineLibrarySyncManager** (20 connections) — `online_library_sync.py`
- **consultar_huggingface_dataset()** (7 connections) — `online_library_sync.py`
- **.compilar_manifiesto_corpus()** (6 connections) — `online_library_sync.py`
- **.generar_dataset_train_jsonl()** (6 connections) — `online_library_sync.py`
- **.publicar_en_huggingface()** (6 connections) — `online_library_sync.py`
- **Any** (6 connections)
- **resolver_token_hf()** (5 connections) — `online_library_sync.py`
- **TestOnlineLibrarySync** (5 connections) — `tests/test_ecosystem_expansion.py`
- **.preparar_bundle_google_drive()** (4 connections) — `online_library_sync.py`
- **.preparar_dataset_card_huggingface()** (4 connections) — `online_library_sync.py`
- **estado_huggingface()** (3 connections) — `online_library_sync.py`
- **main()** (3 connections) — `online_library_sync.py`
- **.empaquetar_tar_gz()** (3 connections) — `online_library_sync.py`
- **.test_compilar_manifiesto()** (2 connections) — `tests/test_ecosystem_expansion.py`
- **.test_preparar_card_y_bundle()** (2 connections) — `tests/test_ecosystem_expansion.py`
- **.test_publicar_hf_sin_token()** (2 connections) — `tests/test_ecosystem_expansion.py`
- **.__init__()** (1 connections) — `online_library_sync.py`
- **Crea un archivo comprimido .tar.gz con todos los archivos Markdown y su…** (1 connections) — `online_library_sync.py`
- **Genera los archivos JSONL estructurados (data/train.jsonl y…** (1 connections) — `online_library_sync.py`
- **Genera el README.md estándar para publicar el dataset en Hugging Face Datasets…** (1 connections) — `online_library_sync.py`
- **Busca el token de Hugging Face, en orden: parámetro, entorno, archivo local. El…** (1 connections) — `online_library_sync.py`
- **Organiza una carpeta limpia lista para ser sincronizada con Google Drive o…** (1 connections) — `online_library_sync.py`
- **Publica el corpus de Markdown, el dataset estructurado en JSONL (train e…** (1 connections) — `online_library_sync.py`
- **Punto de entrada CLI para empaquetar y sincronizar la biblioteca en Markdown.** (1 connections) — `online_library_sync.py`
- **Comprueba la conexión con Hugging Face sin publicar nada. Devuelve la cuenta,…** (1 connections) — `online_library_sync.py`
- *... and 3 more nodes in this community*

## Relationships

- [mcp_server.py](mcp_server.py.md) (8 shared connections)
- [os](os.md) (7 shared connections)
- [LegalGraphifyEngine](LegalGraphifyEngine.md) (2 shared connections)
- [handle_tool_call](handle_tool_call.md) (1 shared connections)

## Source Files

- `online_library_sync.py`
- `tests/test_ecosystem_expansion.py`

## Audit Trail

- EXTRACTED: 55 (96%)
- INFERRED: 2 (4%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*