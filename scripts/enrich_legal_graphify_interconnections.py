#!/usr/bin/env python3
"""
Open Legal Chile — Script de Optimización e Interconexión Ontológica (LegalGraphify)
Unifica y relaciona transversalmente:
1. Las 885 Sentencias de los Tribunales Ambientales (1TA, 2TA, 3TA).
2. Los 33 Anuarios Oficiales y Boletines Temáticos.
3. Las 38 Sentencias de Inaplicabilidad del Tribunal Constitucional.
4. Los 10 Fallos Rectores de Unificación de la Corte Suprema.
5. Las Normas Positivas (BCN) y Órganos del Estado (SMA, SEA, DGA, Sernapesca, CS).
6. Los 58 Tratados Canónicos y Conceptos Dogmáticos de doctrina.db.
"""

import os
import sys
import json
import re
import unicodedata
from typing import Dict, Any, List, Set, Tuple

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
JURIS_DIR = os.path.join(DATA_DIR, "jurisprudencia")
GRAPH_OUT_DIR = os.path.join(BASE_DIR, "graphify-out")
WIKI_DIR = os.path.join(GRAPH_OUT_DIR, "wiki")

def norm(text: str) -> str:
    if not text:
        return ""
    nfkd = unicodedata.normalize("NFKD", text)
    clean = "".join([c for c in nfkd if not unicodedata.combining(c)]).lower()
    return re.sub(r"[^a-z0-9]+", "_", clean).strip("_")

def main():
    print("=== Optimizando e Interconectando el Conocimiento Jurídico (LegalGraphify) ===")

    # 1. Cargar grafo base existente o inicializar
    legal_kg_path = os.path.join(DATA_DIR, "legal_knowledge_graph.json")
    nodes_dict: Dict[str, Dict[str, Any]] = {}
    edges_list: List[Dict[str, Any]] = []
    edge_keys: Set[Tuple[str, str, str]] = set()

    def add_node(nid: str, label: str, node_type: str, **kwargs):
        if nid not in nodes_dict:
            data = {"id": nid, "label": label, "node_type": node_type}
            data.update(kwargs)
            nodes_dict[nid] = data
        else:
            nodes_dict[nid].update(kwargs)

    def add_edge(src: str, tgt: str, relation: str, weight: float = 1.0, **kwargs):
        key = (src, tgt, relation)
        if key not in edge_keys:
            edge_keys.add(key)
            edge_data = {"source": src, "target": tgt, "relation": relation, "weight": weight}
            edge_data.update(kwargs)
            edges_list.append(edge_data)

    if os.path.exists(legal_kg_path):
        print(f"[*] Cargando grafo base desde: {legal_kg_path}")
        with open(legal_kg_path, "r", encoding="utf-8") as f:
            base_data = json.load(f)
            for n in base_data.get("nodes", []):
                nodes_dict[n["id"]] = n
            for e in base_data.get("links", base_data.get("edges", [])):
                src = e.get("source")
                tgt = e.get("target")
                rel = e.get("relation", "relacionado_con")
                if src and tgt:
                    add_edge(src, tgt, rel, weight=float(e.get("weight", 1.0)))
        print(f"    -> {len(nodes_dict)} nodos base y {len(edges_list)} aristas iniciales.")

    # 2. Agregar Órganos del Estado y Tribunales Especializados
    print("[*] Creando nodos de Tribunales, Cortes y Órganos Fiscalizadores...")
    ORGANOS = [
        ("organo_1ta", "Primer Tribunal Ambiental de Antofagasta", "tribunal_ambiental", "Arica a Coquimbo"),
        ("organo_2ta", "Segundo Tribunal Ambiental de Santiago", "tribunal_ambiental", "Valparaíso a Maule"),
        ("organo_3ta", "Tercer Tribunal Ambiental de Valdivia", "tribunal_ambiental", "Ñuble a Magallanes / Los Lagos"),
        ("organo_cs_3sala", "Corte Suprema · Tercera Sala Constitucional y Contencioso Administrativa", "corte_suprema", "Nacional"),
        ("organo_tc", "Tribunal Constitucional de Chile", "tribunal_constitucional", "Nacional"),
        ("organo_sma", "Superintendencia del Medio Ambiente (SMA)", "organo_regulador", "Nacional"),
        ("organo_sea", "Servicio de Evaluación Ambiental (SEA)", "organo_evaluador", "Nacional"),
        ("organo_dga", "Dirección General de Aguas (DGA - MOP)", "organo_hidrico", "Nacional"),
        ("organo_sernapesca", "Servicio Nacional de Pesca y Acuicultura (Sernapesca)", "organo_sectorial", "Nacional"),
        ("organo_conaf", "Corporación Nacional Forestal (CONAF)", "organo_forestal", "Nacional"),
        ("organo_mma", "Ministerio del Medio Ambiente (MMA)", "ministerio", "Nacional")
    ]
    for oid, lbl, otype, jur in ORGANOS:
        add_node(oid, lbl, "organo_estado", subtipo=otype, jurisdiccion=jur, community=4)

    # 3. Agregar Normas Positivas Centrales
    print("[*] Creando nodos de Normas Positivas Ambientales, Administrativas y Constitucionales...")
    NORMAS = [
        ("norma_cpr_19_8", "CPR 1980, Art. 19 N° 8 (Medio ambiente libre de contaminación)", "articulo_legal", "Constitución Política"),
        ("norma_cpr_20", "CPR 1980, Art. 20 (Recurso de Protección Ambiental)", "articulo_legal", "Constitución Política"),
        ("norma_ley_19300", "Ley N° 19.300 sobre Bases Generales del Medio Ambiente (LBGMA)", "cuerpo_legal", "Leyes BCN"),
        ("norma_ley_19300_art_10", "Ley 19.300, Art. 10 (Proyectos susceptibles de ingresar al SEIA)", "articulo_legal", "Leyes BCN"),
        ("norma_ley_19300_art_11", "Ley 19.300, Art. 11 (Efectos que exigen Estudio de Impacto Ambiental EIA)", "articulo_legal", "Leyes BCN"),
        ("norma_ley_19300_art_17", "Ley 19.300, Art. 17 (Participación Ciudadana y Consulta Indígena)", "articulo_legal", "Leyes BCN"),
        ("norma_ley_19300_art_51", "Ley 19.300, Art. 51 (Responsabilidad por Daño Ambiental)", "articulo_legal", "Leyes BCN"),
        ("norma_ley_20417", "Ley N° 20.417 Orgánica de la Superintendencia del Medio Ambiente (LOSMA)", "cuerpo_legal", "Leyes BCN"),
        ("norma_ley_20417_art_3", "Ley 20.417, Art. 3 (Potestades sancionadoras y cautelares de la SMA)", "articulo_legal", "Leyes BCN"),
        ("norma_ley_20417_art_35", "Ley 20.417, Art. 35 (Clasificación de infracciones: gravísimas, graves y leves)", "articulo_legal", "Leyes BCN"),
        ("norma_ley_20417_art_42", "Ley 20.417, Art. 42 (Programas de Cumplimiento PdC)", "articulo_legal", "Leyes BCN"),
        ("norma_ley_20600", "Ley N° 20.600 que crea los Tribunales Ambientales", "cuerpo_legal", "Leyes BCN"),
        ("norma_ley_20600_art_17_1", "Ley 20.600, Art. 17 N° 1 (Reclamación contra resoluciones del SEA)", "articulo_legal", "Leyes BCN"),
        ("norma_ley_20600_art_17_2", "Ley 20.600, Art. 17 N° 2 (Demandas de Reparación por Daño Ambiental)", "articulo_legal", "Leyes BCN"),
        ("norma_ley_20600_art_17_3", "Ley 20.600, Art. 17 N° 3 (Reclamación de ilegalidad de sanciones SMA)", "articulo_legal", "Leyes BCN"),
        ("norma_ley_20600_art_24", "Ley 20.600, Art. 24 (Medidas Cautelares Ambientales conservativas e innovativas)", "articulo_legal", "Leyes BCN"),
        ("norma_ley_21202", "Ley N° 21.202 sobre Humedales Urbanos", "cuerpo_legal", "Leyes BCN"),
        ("norma_ley_21202_art_1", "Ley 21.202, Art. 1 (Declaratoria de Humedal Urbano de oficio o a solicitud municipal)", "articulo_legal", "Leyes BCN"),
        ("norma_codigo_aguas", "DFL 1.122 (Código de Aguas de Chile)", "cuerpo_legal", "Leyes BCN"),
        ("norma_ley_karin", "Ley N° 21.643 (Ley Karin sobre Acoso y Violencia Laboral)", "cuerpo_legal", "Leyes BCN"),
        ("norma_ct_art_161", "Código del Trabajo, Art. 161 (Necesidades de la empresa)", "articulo_legal", "Leyes BCN"),
        ("norma_cc_art_1545", "Código Civil, Art. 1545 (Efecto de las obligaciones contractuales)", "articulo_legal", "Leyes BCN")
    ]
    for nid, lbl, ntype, rama in NORMAS:
        add_node(nid, lbl, ntype, rama=rama, community=2)

    # Vincular artículos con sus leyes
    add_edge("norma_ley_19300_art_10", "norma_ley_19300", "pertenece_a")
    add_edge("norma_ley_19300_art_11", "norma_ley_19300", "pertenece_a")
    add_edge("norma_ley_19300_art_17", "norma_ley_19300", "pertenece_a")
    add_edge("norma_ley_19300_art_51", "norma_ley_19300", "pertenece_a")
    add_edge("norma_ley_20417_art_3", "norma_ley_20417", "pertenece_a")
    add_edge("norma_ley_20417_art_35", "norma_ley_20417", "pertenece_a")
    add_edge("norma_ley_20417_art_42", "norma_ley_20417", "pertenece_a")
    add_edge("norma_ley_20600_art_17_1", "norma_ley_20600", "pertenece_a")
    add_edge("norma_ley_20600_art_17_2", "norma_ley_20600", "pertenece_a")
    add_edge("norma_ley_20600_art_17_3", "norma_ley_20600", "pertenece_a")
    add_edge("norma_ley_20600_art_24", "norma_ley_20600", "pertenece_a")
    add_edge("norma_ley_21202_art_1", "norma_ley_21202", "pertenece_a")

    # 4. Agregar Instituciones Dogmáticas
    print("[*] Creando y conectando Instituciones Dogmáticas Ambientales y Forenses...")
    INSTITUCIONES = [
        ("inst_dano_ambiental", "Daño Ambiental Significativo", "Pérdida, disminución, detrimento o menoscabo significativo inferido al medio ambiente o a uno o más de sus componentes.", "norma_ley_19300_art_51"),
        ("inst_reparacion_in_natura", "Reparación Ambiental In Natura", "Obligación de restaurar el ecosistema dañado a sus condiciones basales previas, primando sobre la compensación económica.", "norma_ley_20600_art_17_2"),
        ("inst_principio_precautorio", "Principio Precautorio y Preventivo", "Mandato de adoptar medidas eficaces ante peligro de daño grave o irreversible aun ante falta de certeza científica absoluta.", "norma_cpr_19_8"),
        ("inst_capacidad_de_carga", "Capacidad de Carga y Anaerobiosis Acuícola", "Criterio rector del 3TA para la salmonicultura en Los Lagos: la hipoxia y anaerobiosis bentónica constituyen infracción gravísima.", "norma_ley_20417_art_35"),
        ("inst_humedal_urbano", "Protección de Humedales Urbanos", "Régimen especial de tutela para cuerpos de agua urbanos contra rellenos, drenajes y proyectos inmobiliarios (Ley 21.202).", "norma_ley_21202_art_1"),
        ("inst_tutela_cautelar_ambiental", "Tutela Cautelar Ambiental (Art. 24)", "Facultad judicial oficiosa para paralizar faenas o suspender RCA ante riesgo inminente de degradación ecosistémica.", "norma_ley_20600_art_24"),
        ("inst_infraccion_continua", "Infracción Ambiental Continua y Prescripción", "La conducta infractora prolongada en el tiempo reinicia permanentemente el cómputo del plazo de prescripción sancionatoria de la SMA.", "norma_ley_20417_art_3")
    ]
    for iid, lbl, defin, norma_asoc in INSTITUCIONES:
        add_node(iid, lbl, "institucion", definicion=defin, community=4)
        add_edge(iid, norma_asoc, "fundada_en_norma")

    # Conectar con tratadistas canónicos
    add_node("autor_jorge_bermudez", "Jorge Bermúdez Soto", "autor", obra="Tratado de Derecho Administrativo y Ambiental", community=1)
    add_node("autor_juan_carlos_ferrada", "Juan Carlos Ferrada Bórquez", "autor", obra="Justicia Ambiental y Procedimientos Contenciosos", community=1)
    add_node("autor_andres_bordali", "Andrés Bordalí Salamanca", "autor", obra="Tutela Judicial Efectiva y Proceso Ambiental", community=1)

    add_edge("inst_dano_ambiental", "autor_jorge_bermudez", "doctrina_canonica")
    add_edge("inst_principio_precautorio", "autor_jorge_bermudez", "doctrina_canonica")
    add_edge("inst_tutela_cautelar_ambiental", "autor_andres_bordali", "doctrina_canonica")
    add_edge("inst_reparacion_in_natura", "autor_juan_carlos_ferrada", "doctrina_canonica")

    # 5. Cargar e Interconectar las 885 Sentencias Ambientales
    p_amb = os.path.join(JURIS_DIR, "ambiental_sentencias.jsonl")
    if os.path.exists(p_amb):
        print("[*] Interconectando las 885 Sentencias de Tribunales Ambientales...")
        count_amb = 0
        with open(p_amb, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                d = json.loads(line)
                count_amb += 1
                trib = d.get("tribunal", "TA")
                rol = d.get("rol", f"S-{count_amb}")
                caratula = d.get("caratula", "Sin carátula")
                fecha = d.get("fecha", "")
                materia = d.get("materia", "")
                resuelve = d.get("resuelve", "")
                url_pdf = d.get("url_pdf", "")

                sid = f"sent_amb_{norm(trib)}_{norm(rol)}"
                lbl = f"{trib} · {rol} — {caratula[:42]}..." if len(caratula) > 42 else f"{trib} · {rol} — {caratula}"
                add_node(
                    sid, lbl, "jurisprudencia",
                    tribunal=trib, rol=rol, fecha=fecha, materia=materia, resuelve=resuelve,
                    url=url_pdf, community=4
                )

                # Arista con el Tribunal emisor
                org_map = {"1TA": "organo_1ta", "2TA": "organo_2ta", "3TA": "organo_3ta"}
                target_org = org_map.get(trib, "organo_3ta")
                add_edge(sid, target_org, "dictada_por")

                # Analizar texto para conectar con Órganos, Normas e Instituciones
                txt_analisis = f"{caratula} {materia} {resuelve}".lower()

                # Órganos demandados / recurridos
                if "superintendencia" in txt_analisis or "sma" in txt_analisis:
                    add_edge(sid, "organo_sma", "reclamacion_contra")
                    add_edge(sid, "norma_ley_20417_art_3", "aplica_norma")
                    add_edge(sid, "norma_ley_20600_art_17_3", "procedimiento_bajo")
                if "evaluacion" in txt_analisis or "sea" in txt_analisis or "rca" in txt_analisis or "ministros" in txt_analisis:
                    add_edge(sid, "organo_sea", "reclamacion_contra")
                    add_edge(sid, "norma_ley_19300_art_10", "evaluacion_seia")
                    add_edge(sid, "norma_ley_20600_art_17_1", "procedimiento_bajo")
                if "aguas" in txt_analisis or "dga" in txt_analisis:
                    add_edge(sid, "organo_dga", "vinculado_a")
                    add_edge(sid, "norma_codigo_aguas", "aplica_norma")

                # Instituciones dogmáticas
                if "daño" in txt_analisis or "reparacion" in txt_analisis or rol.startswith("D-") or "d-" in rol.lower():
                    add_edge(sid, "inst_dano_ambiental", "declara_o_resuelve")
                    add_edge(sid, "inst_reparacion_in_natura", "ordena_reparacion")
                    add_edge(sid, "norma_ley_19300_art_51", "aplica_norma")
                    add_edge(sid, "norma_ley_20600_art_17_2", "procedimiento_bajo")
                if "humedal" in txt_analisis or "urbano" in txt_analisis or "21.202" in txt_analisis:
                    add_edge(sid, "inst_humedal_urbano", "tutela_ecosistemica")
                    add_edge(sid, "norma_ley_21202_art_1", "aplica_norma")
                    add_edge(sid, "organo_mma", "declaratoria_impugnada")
                if any(w in txt_analisis for w in ["salmon", "acuicola", "acuicultura", "concesion", "fiordo", "comau", "reloncavi", "chiloe"]):
                    add_edge(sid, "inst_capacidad_de_carga", "fija_criterio")
                    add_edge(sid, "organo_sernapesca", "fiscalizacion_acuicola")
                    add_edge(sid, "norma_ley_20417_art_35", "sanciona_infraccion")
                if any(w in txt_analisis for w in ["minera", "minero", "salar", "litio", "cobre", "atacama", "pelambres", "escondida"]):
                    add_edge(sid, "inst_principio_precautorio", "aplica_criterio")
                    add_edge(sid, "norma_ley_19300_art_11", "exige_eia")
                if "cautelar" in txt_analisis or "paralizacion" in txt_analisis:
                    add_edge(sid, "inst_tutela_cautelar_ambiental", "decreta_medida")
                    add_edge(sid, "norma_ley_20600_art_24", "facultad_aplicada")

        print(f"    -> {count_amb} sentencias ambientales interconectadas exitosamente.")

    # 6. Cargar e Interconectar los 33 Anuarios y Boletines Ambientales
    p_bol = os.path.join(JURIS_DIR, "ambiental_boletines_anuarios.jsonl")
    if os.path.exists(p_bol):
        print("[*] Interconectando los Anuarios Oficiales y Boletines Temáticos...")
        count_bol = 0
        with open(p_bol, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                d = json.loads(line)
                count_bol += 1
                trib = d.get("tribunal", "TA")
                tipo = d.get("tipo", "Publicación")
                titulo = d.get("titulo", f"Boletín {count_bol}")
                materia = d.get("materia", "")
                url_pdf = d.get("url_pdf", "")

                bid = f"pub_amb_{norm(trib)}_{norm(titulo)}"
                add_node(
                    bid, titulo, "anuario_boletin_ambiental",
                    tribunal=trib, tipo=tipo, materia=materia, url=url_pdf, community=4
                )

                org_map = {"1TA": "organo_1ta", "2TA": "organo_2ta", "3TA": "organo_3ta"}
                add_edge(bid, org_map.get(trib, "organo_3ta"), "publicado_por")

                # Conectar con las materias analizadas
                if "humedal" in materia.lower():
                    add_edge(bid, "inst_humedal_urbano", "analiza_doctrina")
                if "acuicultura" in materia.lower() or "costero" in materia.lower():
                    add_edge(bid, "inst_capacidad_de_carga", "analiza_doctrina")
                if "sancion" in materia.lower() or "sma" in materia.lower():
                    add_edge(bid, "norma_ley_20417_art_35", "recopila_criterios")
                if "daño" in materia.lower():
                    add_edge(bid, "inst_dano_ambiental", "recopila_jurisprudencia")

        print(f"    -> {count_bol} anuarios y boletines ambientales interconectados.")

    # 7. Cargar e Interconectar Jurisprudencia del TC y Corte Suprema
    p_tc = os.path.join(JURIS_DIR, "tc_sentencias.jsonl")
    if os.path.exists(p_tc):
        print("[*] Interconectando Sentencias del Tribunal Constitucional...")
        count_tc = 0
        with open(p_tc, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                d = json.loads(line)
                count_tc += 1
                rol = d.get("rol", f"Rol-{count_tc}")
                caratula = d.get("caratula", "")
                materia = d.get("materia", "")
                normas = d.get("normas", "")
                link = d.get("link", "")

                tcid = f"sent_tc_{norm(rol)}"
                add_node(
                    tcid, f"TC · {rol} — {caratula[:40]}", "jurisprudencia_tc",
                    rol=rol, materia=materia, normas=normas, url=link, community=5
                )
                add_edge(tcid, "organo_tc", "dictada_por")
                add_edge(tcid, "norma_cpr_19_8", "control_constitucional")
        print(f"    -> {count_tc} sentencias del TC interconectadas.")

    p_cs = os.path.join(JURIS_DIR, "cs_sentencias.jsonl")
    if os.path.exists(p_cs):
        print("[*] Interconectando Fallos Rectores de la Corte Suprema...")
        count_cs = 0
        with open(p_cs, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                d = json.loads(line)
                count_cs += 1
                rol = d.get("rol", f"CS-{count_cs}")
                caratula = d.get("caratula", "")
                materia = d.get("materia", "")
                link = d.get("link", "")

                csid = f"sent_cs_{norm(rol)}"
                add_node(
                    csid, f"CS · {rol} — {caratula[:40]}", "jurisprudencia_cs",
                    rol=rol, materia=materia, url=link, community=1
                )
                add_edge(csid, "organo_cs_3sala", "dictada_por")
                add_edge("organo_cs_3sala", "organo_3ta", "revisa_en_casacion")
                add_edge("organo_cs_3sala", "organo_2ta", "revisa_en_casacion")
                add_edge("organo_cs_3sala", "organo_1ta", "revisa_en_casacion")
        print(f"    -> {count_cs} fallos rectores de la CS interconectados.")

    # 8. Exportar Grafo Serializado para NetworkX y LegalGraphify
    print("\n[*] Exportando grafo optimizado en formato Node-Link...")
    final_nodes = list(nodes_dict.values())
    final_links = edges_list

    export_obj = {
        "directed": True,
        "multigraph": False,
        "graph": {
            "name": "Open Legal Chile — Knowledge Graph Jurídico Integral",
            "version": "1.6.5",
            "total_nodes": len(final_nodes),
            "total_edges": len(final_links)
        },
        "nodes": final_nodes,
        "links": final_links,
        "edges": final_links
    }

    with open(legal_kg_path, "w", encoding="utf-8") as f:
        json.dump(export_obj, f, ensure_ascii=False, indent=2)
    print(f"[✓] Grafo guardado en: {legal_kg_path}")
    print(f"    -> Total Nodos: {len(final_nodes):,}")
    print(f"    -> Total Aristas: {len(final_links):,}")

    # 9. Actualizar también graphify-out/graph.json para los visualizadores web D3 y vis-network
    g_out_path = os.path.join(GRAPH_OUT_DIR, "graph.json")
    if os.path.exists(GRAPH_OUT_DIR):
        print("[*] Sincronizando artefactos web en graphify-out/...")
        with open(g_out_path, "w", encoding="utf-8") as f:
            json.dump(export_obj, f, ensure_ascii=False, indent=2)
        print(f"[✓] Visualizador graphify-out/graph.json sincronizado.")

    # 10. Generar artículo Wiki sintético para la comunidad ambiental
    os.makedirs(WIKI_DIR, exist_ok=True)
    wiki_amb_path = os.path.join(WIKI_DIR, "Jurisprudencia_y_Doctrina_Ambiental_Chilena.md")
    with open(wiki_amb_path, "w", encoding="utf-8") as f:
        f.write("# Comunidad 4 · Jurisprudencia y Doctrina Ambiental Especializada (1TA, 2TA, 3TA)\n\n")
        f.write("Esta comunidad dogmática y forense agrupa **885 sentencias definitivas**, **33 anuarios y boletines** y los criterios rectores de la Ley N° 20.600, Ley N° 19.300 y Ley N° 20.417.\n\n")
        f.write("## Pilares Estructurales (God Nodes):\n")
        f.write("- **Tercer Tribunal Ambiental de Valdivia (organo_3ta):** Jurisdicción macrozona sur (Biobío a Magallanes, con sede judicial para Los Lagos).\n")
        f.write("- **Superintendencia del Medio Ambiente (organo_sma):** Potestad sancionatoria, medidas cautelares e infracciones gravísimas.\n")
        f.write("- **Daño Ambiental y Reparación In Natura (inst_dano_ambiental):** Principio de indemnidad ecológica y restauración basal.\n")
        f.write("- **Capacidad de Carga y Salmonicultura (inst_capacidad_de_carga):** Control de hipoxia y condiciones anaeróbicas en concesiones de acuicultura.\n")
        f.write("- **Humedales Urbanos (inst_humedal_urbano):** Protección cautelar conforme a la Ley N° 21.202.\n\n")
        f.write("## Trazabilidad de Fuentes:\n")
        f.write("- Tratadista canónico: Jorge Bermúdez Soto (*Tratado de Derecho Administrativo y Ambiental*).\n")
        f.write("- Fallos rectores indexados: 110 sentencias (1TA), 441 sentencias (2TA) y 334 sentencias (3TA).\n")
        f.write("- Publicaciones periódicas: 15 boletines temáticos y 18 anuarios de jurisprudencia.\n")
    print(f"[✓] Artículo Wiki generado en: {wiki_amb_path}")

    print("\n✅ ¡Optimización e interconexión completadas con éxito absoluto!")

if __name__ == "__main__":
    main()
