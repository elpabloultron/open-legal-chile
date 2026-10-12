"""Concordancias legales que el motor del grafo lee de la doctrina (`construir_grafo_desde_doctrina`).

«Art. 20 CPR» se leía como «Art. 20 CP» (la alternancia de siglas no cerraba en un límite de
palabra), y una cita partida en líneas («(Art.⏎   291 CPP)») dejaba el salto en la etiqueta del
nodo. Todo en tmp_path: no toca doctrina/ ni el grafo publicado."""

from legal_graphify import LegalGraphifyEngine

DOC = """# MANUAL DE PRUEBA
**Tratadista:** Autor de Prueba | **Área:** Derecho Constitucional | **Materia:** Acciones

---

## 🏛️ Recurso de Protección
**Definición Canónica:**
Acción cautelar de los derechos fundamentales (Art. 20 CPR) que conoce la Corte de Apelaciones.
En materia penal se invoca el (Art.
                                         291 CPP) y el Art. 391 CP.
"""


def test_las_concordancias_no_confunden_la_constitucion_con_el_codigo_penal(tmp_path):
    (tmp_path / "constitucional").mkdir()
    (tmp_path / "constitucional" / "manual.md").write_text(DOC, encoding="utf-8")
    motor = LegalGraphifyEngine(doctrina_dir=str(tmp_path))
    motor.construir_grafo_desde_doctrina()
    nodos = dict(motor.graph.nodes(data=True))
    assert "norma_art_20_cpr" in nodos and "norma_art_20_cp" not in nodos
    assert nodos["norma_art_391_cp"]["label"] == "Art. 391 CP"
    assert nodos["norma_art_291_cpp"]["label"] == "Art. 291 CPP"      # la etiqueta, en una sola línea
