# El mapa de conocimiento del corpus

El dataset [`pablobenavidesj/doctrina-jurisprudencia-chile`](https://huggingface.co/datasets/pablobenavidesj/doctrina-jurisprudencia-chile)
tiene unos 80 mil archivos. Hay fichas de la Corte Suprema, sentencias del Tribunal Constitucional y
de los Tribunales Ambientales, doctrina, revistas, guías de la Academia Judicial y publicaciones
ambientales. El **mapa** los inventaría todos.

Cada archivo queda con:

- un ID canónico;
- sus metadatos;
- las normas y los roles que cita.

Sobre esas filas se arma la **capa conectora** de LegalGraphify, con normas, autores, revistas,
ministros, salas, tribunales y recursos.

El mapa vive **en el propio dataset**, en `data/mapa/`. El repositorio solo guarda un puntero a la
revisión publicada ([`mapa_corpus/puntero.json`](../mapa_corpus/puntero.json)).

## IDs canónicos

| Entrada | ID | Ejemplo |
|---|---|---|
| Ficha de la Corte Suprema | `cs:<n>-<año>` (sin puntos de miles) | `cs:10641-2024` |
| Sentencia del TC | `tc:<n>`. Se toma el rol del **cuerpo** del fallo; la cabecera del archivo a veces es de otra causa | `tc:2402` |
| Sentencia ambiental | `ta:<1ta\|2ta\|3ta>:<letra>-<n>-<año>` | `ta:3ta:r-21-2021` |
| Doctrina, revistas, guías | `doc:`, `guia:`, `bib:`, `pub:` + ruta | `doc:revistas/rchd/2020/x` |
| Norma | `norma:<cuerpo>[:<art>[:n<numeral>]]` | `norma:cc:2314`, `norma:cpr:19:n3`, `norma:ley-19300:11bis`, `norma:dl-3500:19`, `norma:cpr:2-transitorio` |
| Autor | `autor:<tokens ordenados>` | `autor:barros_bourie_enrique` |
| Ministro | `ministro:<nombre>` | `ministro:maria-gajardo-harboe` |
| Sala, recurso, tribunal, revista, órgano | `sala:cs-3`, `recurso:proteccion`, `tribunal:ca-valparaiso`, `revista:rchd`, `organo:tc` | |

Las normas y los roles salen de una **gramática determinista**, sin LLM, en
[`citas_legales.py`](../citas_legales.py): `normas_canonicas`, `roles_canonicos`, `rol_canonico` y
`resolver_consulta`.

- **Nombres de cuerpos.** Gana el nombre más largo: el «Código de Procedimiento Civil» no es el
  «Código Civil» y la «Ley Orgánica Constitucional…» no es la Constitución.
- **Leyes y artículos.** Se reconocen las leyes con punto de miles y los artículos `bis`, `ter` y
  transitorios.
- **Constitución.** Se leen los numerales y los incisos de la CPR.
- **Roles.** Un rol solo se atribuye a la Corte Suprema si el contexto lo dice. Con «Corte de
  Apelaciones», un RIT o un «Juzgado», no se atribuye.

Se mide contra un conjunto de referencia anotado a mano con fragmentos reales del dataset
(`tests/fixtures/mapa/referencia_*.jsonl`). La precisión y la exhaustividad tienen un piso en
`tests/test_mapa_ids.py`.

## Formato publicado (`data/mapa/`)

```
estado.json                  revisión fuente, huella, versión de reglas, conteos, calidad y
                             sha256 de cada archivo
entradas/<partición>.jsonl.gz  una fila por archivo (cs-<era>, tc, ta-<k>ta, doc-rev-<sigla>, …)
entidades/<tipo>.jsonl.gz      normas, autores, revistas, ministros, salas, tribunales, recursos
grafo/nodos-<tipo>.jsonl.gz    capa conectora de LegalGraphify
grafo/aristas-<rel>.jsonl.gz   cita_norma, cita_rol, escrito_por, integra_sala, conoce_recurso, …
grafo/alias.jsonl.gz           IDs del grafo curado del repo → ID canónico del mapa
grafo/comunidades.jsonl.gz     Louvain con semilla fija sobre curado + capa
```

**Determinismo.** Todo es determinista:

- JSON con claves ordenadas, en NFC y sin floats;
- filas ordenadas por ID;
- gzip con `mtime=0`.

Dos construcciones del mismo dataset dan los mismos bytes. Por eso, si nada cambió, no hay commit.

**Fichas de la Corte Suprema.** Las 70 mil fichas salen del índice
`data/jurisprudencia/cs_sentencias_2anios.jsonl`. Sus fallos no son nodos del grafo: entran como
aristas agregadas y ponderadas (`integra_sala`, `conoce_recurso`, …) y se materializan **bajo
demanda**, en una vista por consulta.

## Ciclo incremental (`python -m mapa_corpus`)

```bash
python -m mapa_corpus estado    --trabajo <dir>        # ¿cambió el dataset? → plan.json
python -m mapa_corpus construir --trabajo <dir>        # baja solo lo nuevo, reescribe solo lo tocado
python -m mapa_corpus validar   --trabajo <dir>        # IDs, rutas, aristas, comunidades, humo
python -m mapa_corpus publicar  --trabajo <dir> [--dry-run]   # 1 commit en HF + tag mapa-<n> + puntero
python -m mapa_corpus actualizar --trabajo <dir>       # los cuatro pasos
python -m mapa_corpus verificar-puntero                # el puntero apunta a un mapa íntegro
```

**`estado`** compara el inventario actual de HF con el último mapa publicado. El inventario sale de
**una** llamada a la API: `blob_id`, tamaño y sha256 LFS de cada archivo. La base es el mapa
publicado, no el puntero, para no rehacer trabajo mientras un PR del puntero sigue abierto.

- **Sin cambios** cuando la huella del inventario filtrado coincide con la de la base, igual que el
  grafo curado. La huella deja fuera `data/mapa/**`, `graphify/**` y `.gitattributes`: así la
  publicación del mapa no se detecta a sí misma como un cambio.
- **Construcción completa** cuando cambian las reglas de extracción.
- **No hace nada** si el último commit del dataset tiene menos de 45 minutos («fuente en
  movimiento»).

**`construir`** descarga cada archivo fijado al sha de la fuente y lo verifica contra su blob git o
su sha256 LFS. Guarda una caché por `blob_id` y respeta el cupo de HF con un limitador que lee el
encabezado `ratelimit`. Sin token, la primera construcción completa tarda unos 35 minutos; las
siguientes procesan solo el delta.

**`publicar`** se niega si NetworkX o `huggingface_hub` no están en las versiones de
[`constraints-constructor.txt`](../mapa_corpus/constraints-constructor.txt): otra versión de
Louvain cambiaría las comunidades sin que cambie el corpus.

- El commit lleva `parent_commit`: si `main` del dataset avanzó entretanto, HF lo rechaza y la
  corrida queda «superada».
- Cada publicación deja un tag `mapa-<n>`, y nunca se aplasta el historial del dataset. Así las
  revisiones que fijan los paquetes ya instalados no desaparecen.

## La Action diaria

[`.github/workflows/mapa-hf.yml`](../.github/workflows/mapa-hf.yml) corre todos los días a las
07:23 UTC y también a mano (`workflow_dispatch`, con modo `delta` o `completo`).

**Job `construir`.** No tiene token de escritura. Corre `estado`, `construir`, `validar` y las
pruebas del mapa, con la caché de fuentes en `actions/cache`.

**Job `publicar`.** Corre en el environment `hf-publicar`, el único con el token de escritura.
Publica en HF y abre el PR `mapa/puntero`, que cambia solo `mapa_corpus/puntero.json`.

**Job `mapa-puntero` de la CI** ([`ci.yml`](../.github/workflows/ci.yml)). Cuando un PR cambia el
puntero, lo verifica con lectura pública:

- el sha256 del estado y el de cada archivo;
- que exista el `sha_fuente`;
- la validación completa del mapa;
- consultas de humo.

Si una corrida falla, se abre o se comenta un issue.

**Secretos que hay que crear una vez:**

| Dónde | Nombre | Para qué |
|---|---|---|
| Environment `hf-publicar` | `HF_TOKEN` | Token *fine-grained* con escritura **solo** en el dataset |
| Secrets (opcional) | `HF_TOKEN_LECTURA` | Más cupo de descargas para construir |
| Variables + Secrets | `MAPA_APP_ID` + `MAPA_APP_PRIVATE_KEY` | GitHub App que abre el PR del puntero (un PR abierto con `GITHUB_TOKEN` no dispara la CI) |
| Secrets (alternativa) | `MAPA_PR_TOKEN` | PAT *fine-grained* con `contents` y `pull-requests` de escritura |

La **primera publicación** se lanza a mano: Actions → «Mapa del corpus HF» → *Run workflow*, con
`modo=completo`. Así las versiones de las dependencias son las fijadas. Al fusionar el PR del
puntero, todos los clientes pasan a consultar el mapa.

## Cómo lo consulta Open Legal Chile

[`mapa_corpus/cliente.py`](../mapa_corpus/cliente.py) descarga el mapa de la revisión del puntero y
lo verifica contra `sha256_estado` y el sha256 de cada archivo. Arma un índice SQLite con FTS5
([`mapa_corpus/indice.py`](../mapa_corpus/indice.py)) en `~/.openlegal/mapa/<revisión>/` y conserva
dos revisiones.

**Las consultas nunca usan la red.** Solo `asegurar()` descarga, y corre en un hilo de fondo al
arrancar el servidor MCP. Mientras el mapa no esté listo:

1. se usa la última caché lista, con un aviso de qué fuente y de qué fecha es;
2. si no hay ninguna, las herramientas siguen con sus fuentes de siempre y lo dicen en la clave
   `mapa` de su respuesta.

Variables de entorno:

| Variable | Efecto |
|---|---|
| `OPENLEGAL_MAPA=off` | Sin mapa (la suite de pruebas lo fija así) |
| `OPENLEGAL_MAPA=main` | Sigue el último mapa publicado en `main`, fijado a su sha al descargarlo (el puntero es un piso) |
| `OPENLEGAL_MAPA_LOCAL=<dir>` | Usa un mapa construido en disco (`python -m mapa_corpus construir`) |
| `OPENLEGAL_MAPA_DIR=<dir>` | Dónde vive la caché (por defecto `~/.openlegal/mapa`) |

Para operar la caché a mano:

- `openlegal cache mapa` muestra el estado y `openlegal cache mapa --refrescar` fuerza la descarga;
- `suite_doctor` informa si el mapa está listo, como aviso y nunca como error.
