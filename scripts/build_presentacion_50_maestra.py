#!/usr/bin/env python3
"""
Constructor de la Presentación Maestra de 50 Láminas
Open Legal Chile — Charla Magistral en la Universidad de Los Lagos

Genera presentacion.html con:
- 50 láminas magistrales completas, espaciosas y con animaciones interactivas vivas.
- 50 notas de orador alineadas 1 a 1 en el array NOTAS.
- Cobertura exhaustiva: LLMs a fondo, límites, ReAct, Harness, MCP, LegalGraphify,
  75 herramientas, 19 agentes, 885 sentencias de Tribunales Ambientales (1TA, 2TA y 3TA Valdivia),
  privacidad, secreto profesional, posicionamiento nacional y global, y prueba en vivo.
- Estricto cumplimiento ortotipográfico RAE/ASALE y diseño institucional.
"""

import os
import re

BACKUP_PATH = "/home/pablo/Escritorio/charla-open-legal-chile/presentacion.html.bak.50laminas"
OUTPUT_PATH = "/home/pablo/Escritorio/charla-open-legal-chile/presentacion.html"

def main():
    with open(BACKUP_PATH, "r", encoding="utf-8") as f:
        bak_content = f.read()

    # 1. Extraer las láminas originales del backup
    pattern = r'lamina\(`([\s\S]*?)`,\s*"([^"]*)"\);'
    original_laminas = list(re.finditer(pattern, bak_content))
    print(f"Láminas base extraídas del backup: {len(original_laminas)}")

    # 2. Las 50 notas oficiales y completas
    notas_match = re.search(r'const NOTAS = \[([\s\S]*?)\];', bak_content)
    raw_notas = re.findall(r'"([^"]*)"', notas_match.group(1))
    print(f"Notas oficiales en backup: {len(raw_notas)}")

    # 3. Construir la lista de las 50 láminas
    # Tomamos las 41 láminas del backup y las enriquecemos/ordenamos para que calcen exactamente con las 50 notas:
    
    # Láminas 1 a 26: corresponden a las notas 1 a 26
    # Entre la lámina 26 (conectores) y 27 (herramientas), insertamos la Lámina Ambiental (nota 27 modificada / adaptada)
    
    # Revisemos la correspondencia exacta nota por nota:
    # Nota 1: Portada [red]
    # Nota 2: Por qué nació [porque]
    # Nota 3: Para qué es [paraQue]
    # Nota 4: El puente [puente]
    # Nota 5: El mapa [mapa]
    # Nota 6: ¿Qué es un LLM? [llm]
    # Nota 7: Límites estructurales [limites]
    # Nota 8: Riesgo deontológico [riesgo]
    # Nota 9: Paradigma ReAct [bucle]
    # Nota 10: ¿Qué es un agente? [agente]
    # Nota 11: El Harness [harness]
    # Nota 12: MCP [mcp]
    # Nota 13: MCP por dentro [mcpDetalle]
    # Nota 14: Herramienta (tool) [tool]
    # Nota 15: Skill [skill]
    # Nota 16: Quién es quién [compara]
    # Nota 17: Separador capas [red2]
    # Nota 18: RAG plano vs GraphRAG [grafo]
    # Nota 19: El grafo en números [miniGrafo]
    # Nota 20: Ahorro de tokens medido [ahorro]
    # Nota 21: Cómo operan las citas [citas]
    # Nota 22: El camino de una pregunta [flujo]
    # Nota 23: Un caso, de punta a punta [caso]
    # Nota 24: Separador Las herramientas [red3]
    # Nota 25: De dónde salen los datos [api]
    # Nota 26: 10 conectores [conectores]
    # NUEVA LÁMINA 27: Jurisprudencia Tribunales Ambientales (1TA, 2TA, 3TA Valdivia) [ambiental]
    # Lámina 28 (antes 27): Las 75 herramientas [herramientas]
    # Lámina 29 (antes 28): 19 agentes especializados [agentes]
    # Lámina 30 (antes 29): La mesa de entrada [mesa]
    # Lámina 31 (antes 30): Escritos en Word [documentos]
    # Lámina 32 (antes 31): Doctrina FTS5 [doctrina]
    # Lámina 33 (antes 32): El grafo como herramienta [grafoHerramientas]
    # Lámina 34 (antes 33): Estudio, docencia y clínica [estudio]
    # Lámina 35 (antes 34): Hugging Face [huggingface]
    # Lámina 36 (antes 35): Cumplimiento y vigilancia [cumplimiento]
    # Lámina 37 (antes 36): Separador Privacidad [red5]
    # Lámina 38 (antes 37): La regla de oro [frontera]
    # Lámina 39 (antes 38): Derechos ARCO [arco]
    # Lámina 40 (antes 39): Qué sale y qué no [sale]
    # Lámina 41 (antes 40): Secreto profesional y compuerta humana [compuerta]
    # Lámina 42 (antes 41): Estado de desarrollo v1.6.5 GA [red4]
    # NUEVA LÁMINA 43: Radiografía operativa de 5 capas [radiografia]
    # NUEVA LÁMINA 44: Posicionamiento a nivel nacional [posNacional]
    # NUEVA LÁMINA 45: Posicionamiento a nivel internacional [posGlobal]
    # NUEVA LÁMINA 46: Tabla comparativa de arquitectura [tablaComparativa]
    # NUEVA LÁMINA 47: Las cifras clave del sistema [cifrasClave]
    # NUEVA LÁMINA 48: Las reglas de oro de subsunción tripartita [reglasOro]
    # NUEVA LÁMINA 49: Prueba en vivo [pruebaEnVivo]
    # NUEVA LÁMINA 50: Cierre institucional y auditoría [cierre]

    laminas_dict = {}
    for m in original_laminas:
        body = m.group(1)
        tag = m.group(2)
        laminas_dict[tag] = body

    # Actualizar portada (Lámina 1) para la Universidad de Los Lagos
    laminas_dict["red"] = """
<div class="a" style="position:absolute;inset:0"><canvas class="red" id="redPortada"></canvas></div>
<div class="encima a" style="margin-top:auto">
  <div class="ceja">Facultad de Ciencias Jurídicas y Políticas · Universidad de Los Lagos</div>
  <h1 class="a">Open Legal Chile</h1>
</div>
<div class="encima a" style="margin-top:auto;max-width:880px">
  <p class="a" style="font-size:clamp(17px,2.1vw,23px);line-height:1.45;color:#E8E5DD">
    Inteligencia artificial soberana, Model Context Protocol y doctrina canónica para el derecho chileno.
  </p>
</div>
<div class="encima a" style="margin-top:auto">
  <div class="regla a"></div>
  <p class="a" style="font-size:13px;color:#9AA7B4;margin-top:10px">
    Pablo Benavides Jorquera · Septiembre 2026 · Producción Estable (v1.6.5 GA) · 259 pruebas en verde
  </p>
</div>"""

    # Definir las 9 láminas adicionales enriquecidas:
    
    # 27. [ambiental]
    lamina_ambiental = """
<div class="a"><div class="ceja">Jurisprudencia Especializada</div><h2 class="a">Tribunales Ambientales: 885 sentencias cosechadas y criterios de las cortes</h2>
<p class="a" style="margin-top:6px">Análisis de la macrozona norte, centro y sur: 1TA (Antofagasta), 2TA (Santiago) y 3TA (Valdivia / Los Lagos).</p></div>
<div class="cuerpo" style="display:grid;grid-template-columns:1.15fr 0.85fr;gap:20px">
  <div class="tarjeta a" style="display:flex;flex-direction:column;gap:10px">
    <b style="font-size:13.5px;color:var(--tinta)">Cosecha oficial de sentencias definitivas y resoluciones</b>
    <div id="ambTribunales" style="display:grid;grid-template-columns:1fr;gap:8px"></div>
    <p class="gris" id="ambNota" style="font-size:11.8px;min-height:1.8em">—</p>
  </div>
  <div class="tarjeta a acento" style="display:flex;flex-direction:column;gap:9px;border-left-color:var(--verde)">
    <div class="ceja" style="color:var(--verde)">Criterios rectores para la Región de Los Lagos (3TA)</div>
    <div style="font-size:12px;line-height:1.45;display:flex;flex-direction:column;gap:7px">
      <div style="padding:6px 8px;background:var(--papel);border-radius:4px">
        <b style="color:var(--azul)">• Salmonicultura y fondos marinos:</b> Sanciones por condiciones anaeróbicas y escapes masivos en fiordos y canales de Chiloé y Reloncaví.
      </div>
      <div style="padding:6px 8px;background:var(--papel);border-radius:4px">
        <b style="color:var(--verde)">• Humedales Urbanos (Ley 21.202):</b> Medidas cautelares automáticas e innovativas que paralizan loteos y rellenos en Osorno, Puerto Varas y Llanquihue.
      </div>
      <div style="padding:6px 8px;background:var(--papel);border-radius:4px">
        <b style="color:var(--rojo)">• Reparación in natura (Art. 17 N° 2):</b> Planes de restauración ecológica obligatorios bajo supervisión judicial estricta.
      </div>
    </div>
  </div>
</div>"""

    # 43. [radiografia]
    lamina_radiografia = """
<div class="a"><div class="ceja">Arquitectura de Producción</div><h2 class="a">Radiografía operativa de 5 capas integradas</h2>
<p class="a" style="margin-top:6px">Una pila tecnológica completa y soberana: desde el protocolo de red hasta la subsunción forense.</p></div>
<div class="cuerpo" style="display:grid;grid-template-columns:repeat(5, 1fr);gap:10px;align-items:stretch" id="radCapas">
  <div class="tarjeta a" style="display:flex;flex-direction:column;gap:6px;padding:12px 10px">
    <div class="ceja" style="color:var(--azul)">Capa 1 · Red</div>
    <b style="font-size:13px">MCP Oficial</b>
    <p style="font-size:11px;color:var(--gris)">75 herramientas forenses y estatales tipadas sobre Model Context Protocol.</p>
  </div>
  <div class="tarjeta a" style="display:flex;flex-direction:column;gap:6px;padding:12px 10px">
    <div class="ceja" style="color:var(--bronce)">Capa 2 · Agentes</div>
    <b style="font-size:13px">19 Perfiles</b>
    <p style="font-size:11px;color:var(--gris)">Agentes especializados en modo soberano (100% offline) o asistido (ReAct).</p>
  </div>
  <div class="tarjeta a" style="display:flex;flex-direction:column;gap:6px;padding:12px 10px">
    <div class="ceja" style="color:var(--verde)">Capa 3 · Doctrina</div>
    <b style="font-size:13px">58 Tratados</b>
    <p style="font-size:11px;color:var(--gris)">11.853 fichas de instituciones y FTS5/BM25 sobre 8,77 millones de palabras.</p>
  </div>
  <div class="tarjeta a" style="display:flex;flex-direction:column;gap:6px;padding:12px 10px">
    <div class="ceja" style="color:var(--rojo)">Capa 4 · Grafos</div>
    <b style="font-size:13px">LegalGraphify</b>
    <p style="font-size:11px;color:var(--gris)">17.006 nodos y 358 comunidades Leiden. Ahorro medido de tokens hasta 90,5%.</p>
  </div>
  <div class="tarjeta a" style="display:flex;flex-direction:column;gap:6px;padding:12px 10px">
    <div class="ceja" style="color:var(--tinta)">Capa 5 · Forense</div>
    <b style="font-size:13px">OJV y Word</b>
    <p style="font-size:11px;color:var(--gris)">Salida formal en .docx con notas al pie, intake de causas y OCR de fojas escaneadas.</p>
  </div>
</div>"""

    # 44. [posNacional]
    lamina_posNacional = """
<div class="a"><div class="ceja">Posicionamiento Estratégico</div><h2 class="a">Posicionamiento nacional: Frente a los silos comerciales cerrados</h2>
<p class="a" style="margin-top:6px">Por qué Open Legal Chile transforma la práctica forense frente a las bases tradicionales.</p></div>
<div class="cuerpo" style="display:grid;grid-template-columns:1fr 1fr;gap:20px">
  <div class="tarjeta a" style="display:flex;flex-direction:column;gap:10px;border-left:4px solid var(--rojo)">
    <b style="font-size:14px;color:var(--rojo)">El modelo comercial tradicional (vLex, Thomson, Tirant)</b>
    <div style="font-size:12px;color:var(--gris);display:flex;flex-direction:column;gap:8px">
      <p><b>• Silos cerrados de pago:</b> La ley y la doctrina pública quedan encerradas tras muros de pago corporativos.</p>
      <p><b>• Fuga de causas a la nube:</b> Subir expedientes judiciales a servidores extranjeros viola el secreto profesional (Art. 247 CP).</p>
      <p><b>• Falta de auditabilidad:</b> Cajas negras propietarias que no permiten verificar cómo razona el algoritmo.</p>
    </div>
  </div>
  <div class="tarjeta a acento" style="display:flex;flex-direction:column;gap:10px;border-left:4px solid var(--verde)">
    <b style="font-size:14px;color:var(--verde)">La propuesta soberana de Open Legal Chile</b>
    <div style="font-size:12px;color:var(--tinta);display:flex;flex-direction:column;gap:8px">
      <p><b>• Código abierto y gratuito (Apache-2.0):</b> Infraestructura pública y comunitaria para la academia y los colegios de abogados.</p>
      <p><b>• Soberanía 100% local (Zero-Telemetry):</b> El expediente del cliente no sale de la oficina; opera offline si se requiere.</p>
      <p><b>• Citas verificables en cada línea:</b> Enlaces directos a BCN, OJV, CGR y Hugging Face en cada dictamen o escrito.</p>
    </div>
  </div>
</div>"""

    # 45. [posGlobal]
    lamina_posGlobal = """
<div class="a"><div class="ceja">Posicionamiento Global</div><h2 class="a">Civil Law codificado frente a la hegemonía del Common Law</h2>
<p class="a" style="margin-top:6px">La IA anglosajona no entiende el derecho continental: Open Legal Chile defiende la soberanía dogmática.</p></div>
<div class="cuerpo" style="display:grid;grid-template-columns:1.05fr 0.95fr;gap:20px">
  <div class="tarjeta a" style="display:flex;flex-direction:column;gap:8px">
    <b style="font-size:13.5px;color:var(--tinta)">El colonialismo algorítmico (Harvey, CoCounsel, Lexis+)</b>
    <div style="font-size:12px;color:var(--gris);display:flex;flex-direction:column;gap:6px">
      <p>• Diseñados exclusivamente para el sistema de precedentes judiciales obligatorios (*stare decisis*).</p>
      <p>• Extrapolan conceptos espurios ajenos e inexistentes en Chile (prohibido en Civil Law): *discovery*, *punitive damages*, *subpoena*, *at-will employment*.</p>
      <p>• Desconocen la primacía de la Ley (Art. 1 Código Civil) y el efecto relativo de las sentencias (Art. 3 inc. 2 CC).</p>
    </div>
  </div>
  <div class="tarjeta a acento" style="display:flex;flex-direction:column;gap:8px;border-left-color:var(--azul)">
    <div class="ceja" style="color:var(--azul)">La solución: Ontología Codificada</div>
    <p class="serif" style="font-size:15px;line-height:1.45;color:var(--tinta)">
      «El Derecho Continental Codificado exige relacionar la regla general del Código con sus excepciones y la doctrina canónica. Solo un grafo de conocimiento (LegalGraphify) preserva la estructura del Civil Law».
    </p>
    <div style="font-size:11.5px;color:var(--verde);font-weight:600;margin-top:auto">
      ✓ Publicado globalmente en Hugging Face Datasets Hub para toda la comunidad hispanohablante.
    </div>
  </div>
</div>"""

    # 46. [tablaComparativa]
    lamina_tablaComparativa = """
<div class="a"><div class="ceja">Evaluación Comparativa</div><h2 class="a">Matriz comparativa: Soluciones comerciales vs. Open Legal Chile</h2>
<p class="a" style="margin-top:6px">Contraste objetivo de arquitectura, privacidad, costos y especialización jurídica.</p></div>
<div class="cuerpo" style="justify-content:center">
  <div class="tarjeta a" style="width:100%;overflow-x:auto;padding:14px">
    <table style="width:100%;border-collapse:collapse;font-size:12px">
      <thead>
        <tr style="border-bottom:2px solid var(--linea);text-align:left">
          <th style="padding:8px">Dimensión</th>
          <th style="padding:8px;color:var(--rojo)">Modelos Comerciales (Harvey / vLex)</th>
          <th style="padding:8px;color:var(--verde)">Open Legal Chile (v1.6.5 GA)</th>
        </tr>
      </thead>
      <tbody>
        <tr style="border-bottom:1px solid var(--linea)">
          <td style="padding:8px;font-weight:600">Sistema Jurídico</td>
          <td style="padding:8px;color:var(--gris)">Common Law adaptado o búsqueda de texto plano</td>
          <td style="padding:8px;font-weight:600;color:var(--verde)">Civil Law chileno nativo + Subsunción tripartita</td>
        </tr>
        <tr style="border-bottom:1px solid var(--linea)">
          <td style="padding:8px;font-weight:600">Privacidad y Secreto</td>
          <td style="padding:8px;color:var(--rojo)">Nube foránea comercial (Riesgo Art. 247 CP)</td>
          <td style="padding:8px;font-weight:600;color:var(--verde)">100% Local soberano (Zero-Telemetry)</td>
        </tr>
        <tr style="border-bottom:1px solid var(--linea)">
          <td style="padding:8px;font-weight:600">Interoperabilidad</td>
          <td style="padding:8px;color:var(--gris)">Chat web cerrado / Cajas negras propietarias</td>
          <td style="padding:8px;font-weight:600;color:var(--verde)">Estándar abierto MCP (Claude, Antigravity, Cursor)</td>
        </tr>
        <tr style="border-bottom:1px solid var(--linea)">
          <td style="padding:8px;font-weight:600">Modelo de Costos</td>
          <td style="padding:8px;color:var(--rojo)">Suscripciones de USD $500 - $1.200 / mes por usuario</td>
          <td style="padding:8px;font-weight:600;color:var(--verde)">Código abierto libre y gratuito (Apache-2.0 en PyPI)</td>
        </tr>
        <tr>
          <td style="padding:8px;font-weight:600">Auditoría de Fuentes</td>
          <td style="padding:8px;color:var(--gris)">Respuestas sin enlace verificable o citas alucinadas</td>
          <td style="padding:8px;font-weight:600;color:var(--verde)">Citas oficiales BCN, PJUD, CGR, DT con enlace</td>
        </tr>
      </tbody>
    </table>
  </div>
</div>"""

    # 47. [cifrasClave]
    lamina_cifrasClave = """
<div class="a"><div class="ceja">Métricas Consolidadas</div><h2 class="a">Las cifras del sistema: Madurez y solidez técnica</h2>
<p class="a" style="margin-top:6px">Un proyecto probado matemáticamente y respaldado por una suite integral de control de calidad.</p></div>
<div class="cuerpo" style="display:grid;grid-template-columns:repeat(4, 1fr);gap:16px;align-items:center" id="gridCifras">
  <div class="tarjeta a" style="text-align:center;padding:20px 10px">
    <div class="num" style="font-size:38px;color:var(--azul)">75</div>
    <div style="font-weight:700;font-size:13px;margin-top:4px">Herramientas MCP</div>
    <p style="font-size:11px;color:var(--gris);margin-top:4px">16 conectores estatales</p>
  </div>
  <div class="tarjeta a" style="text-align:center;padding:20px 10px">
    <div class="num" style="font-size:38px;color:var(--verde)">17.006</div>
    <div style="font-weight:700;font-size:13px;margin-top:4px">Nodos en el Grafo</div>
    <p style="font-size:11px;color:var(--gris);margin-top:4px">18.710 aristas tipadas</p>
  </div>
  <div class="tarjeta a" style="text-align:center;padding:20px 10px">
    <div class="num" style="font-size:38px;color:var(--bronce)">885</div>
    <div style="font-weight:700;font-size:13px;margin-top:4px">Sentencias Ambientales</div>
    <p style="font-size:11px;color:var(--gris);margin-top:4px">1TA, 2TA y 3TA Valdivia</p>
  </div>
  <div class="tarjeta a" style="text-align:center;padding:20px 10px">
    <div class="num" style="font-size:38px;color:var(--verde)">259</div>
    <div style="font-weight:700;font-size:13px;margin-top:4px">Pruebas en Verde</div>
    <p style="font-size:11px;color:var(--gris);margin-top:4px">100% éxito sin regresión</p>
  </div>
</div>"""

    # 48. [reglasOro]
    lamina_reglasOro = """
<div class="a"><div class="ceja">Estándar Forense</div><h2 class="a">Las tres reglas de oro: La subsunción tripartita</h2>
<p class="a" style="margin-top:6px">Toda respuesta de fondo se construye con el rigor de un Informe en Derecho (*Legal Memorandum*).</p></div>
<div class="cuerpo" style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px;align-items:stretch">
  <div class="tarjeta a" style="display:flex;flex-direction:column;gap:8px;border-top:4px solid var(--azul)">
    <div class="ceja" style="color:var(--azul)">Pilar 1 · Positivo</div>
    <b style="font-size:14px">Ley Chilena (BCN)</b>
    <p style="font-size:11.8px;color:var(--gris);line-height:1.45">
      Identificación rigurosa del cuerpo normativo, artículo, inciso y tenor literal vigente. Prohibición de inventar o aproximar normas.
    </p>
  </div>
  <div class="tarjeta a" style="display:flex;flex-direction:column;gap:8px;border-top:4px solid var(--verde)">
    <div class="ceja" style="color:var(--verde)">Pilar 2 · Dogmático</div>
    <b style="font-size:14px">Doctrina Canónica</b>
    <p style="font-size:11.8px;color:var(--gris);line-height:1.45">
      Subsunción teórica apoyada en los 58 tratados canónicos (*Barros, Somarriva, Ramos Pazos, Peñailillo*) y las guías de la Academia Judicial.
    </p>
  </div>
  <div class="tarjeta a" style="display:flex;flex-direction:column;gap:8px;border-top:4px solid var(--bronce)">
    <div class="ceja" style="color:var(--bronce)">Pilar 3 · Jurisprudencial</div>
    <b style="font-size:14px">Precedente Judicial / Adm.</b>
    <p style="font-size:11.8px;color:var(--gris);line-height:1.45">
      Criterio unificador de la Excma. Corte Suprema, Tribunal Constitucional o dictámenes vinculantes de Contraloría (CGR) y Dirección del Trabajo (DT).
    </p>
  </div>
</div>"""

    # 49. [pruebaEnVivo]
    lamina_pruebaEnVivo = """
<div class="a"><div class="ceja">Sesión Interactiva</div><h2 class="a">Prueba en vivo: Preguntas abiertas de la audiencia</h2>
<p class="a" style="margin-top:6px">Facultad de Ciencias Jurídicas y Políticas · Universidad de Los Lagos.</p></div>
<div class="cuerpo" style="display:grid;grid-template-columns:1.2fr 0.8fr;gap:20px;align-items:stretch">
  <div class="tarjeta a" style="display:flex;flex-direction:column;gap:10px">
    <b style="font-size:13.5px;color:var(--tinta)">Pon a prueba el sistema en tiempo real</b>
    <div class="consola" id="consolaEnVivo" style="flex:1;min-height:140px;font-size:12px;padding:12px;line-height:1.5">
      <span style="color:#569CD6">$</span> <span style="color:#DCDCDC">openlegal query --prompt</span> <span style="color:#CE9178">"..."</span><br><br>
      <span style="color:#6A9955"># Sugerencias de preguntas para la comisión y estudiantes:</span><br>
      • «¿Cuál es el criterio del 3TA sobre medidas cautelares en humedales urbanos de Osorno?»<br>
      • «¿Qué resolvió la Cuarta Sala de la Corte Suprema sobre el descuento AFC en el despido improcedente?»<br>
      • «¿Cómo aplica el principio de confianza legítima en las contratas públicas según la CGR?»
    </div>
  </div>
  <div class="tarjeta a acento" style="display:flex;flex-direction:column;justify-content:center;gap:12px;border-left-color:var(--bronce)">
    <div class="ceja" style="color:var(--bronce)">Regla de la prueba</div>
    <p class="serif" style="font-size:15px;line-height:1.45;color:var(--tinta)">
      «No hay libreto preparado ni respuestas enlatadas: cualquier pregunta jurídica real será procesada mostrando en vivo las fuentes oficiales del Estado».
    </p>
  </div>
</div>"""

    # 50. [cierre]
    lamina_cierre = """
<div class="a"><div class="ceja">Conclusión</div><h2 class="a">Open Legal Chile: El jurista y la tecnología soberana</h2>
<p class="a" style="margin-top:6px">Una herramienta al servicio de la justicia, el rigor dogmático y la educación jurídica pública.</p></div>
<div class="cuerpo" style="display:grid;grid-template-columns:1.1fr 0.9fr;gap:20px;align-items:center">
  <div class="tarjeta a" style="display:flex;flex-direction:column;gap:12px">
    <b style="font-size:16px;color:var(--tinta)">Disponible hoy para toda la comunidad jurídica</b>
    <div style="font-size:12.5px;line-height:1.6;display:flex;flex-direction:column;gap:6px">
      <div>📦 <b>PyPI:</b> <code>pip install openlegal-chile</code> (v1.6.5)</div>
      <div>🤗 <b>Hugging Face:</b> <code>pablobenavidesj/doctrina-jurisprudencia-chile</code></div>
      <div>🐙 <b>GitHub:</b> <code>github.com/elpabloultron/open-legal-chile</code></div>
      <div>⚖️ <b>Licencia:</b> Apache-2.0 (Código Abierto, Libre y Gratuito)</div>
    </div>
  </div>
  <div class="tarjeta a acento" style="text-align:center;padding:24px 16px;border-left-color:var(--verde)">
    <div class="ceja" style="color:var(--verde)">Agradecimientos</div>
    <p class="serif" style="font-size:17px;line-height:1.4;color:var(--tinta);margin:10px 0">
      «Muchas gracias a los profesores y estudiantes de la Universidad de Los Lagos».
    </p>
    <p class="gris" style="font-size:12px">Pablo Benavides Jorquera · Osorno / Puerto Montt · 2026</p>
  </div>
</div>"""

    # Lista ordenada de las 50 láminas con sus tags:
    orden_50 = [
        ("red", laminas_dict["red"]),
        ("porque", laminas_dict["porque"]),
        ("paraQue", laminas_dict["paraQue"]),
        ("puente", laminas_dict["puente"]),
        ("mapa", laminas_dict["mapa"]),
        ("llm", laminas_dict["llm"]),
        ("limites", laminas_dict["limites"]),
        ("riesgo", laminas_dict["riesgo"]),
        ("bucle", laminas_dict["bucle"]),
        ("agente", laminas_dict["agente"]),
        ("harness", laminas_dict["harness"]),
        ("mcp", laminas_dict["mcp"]),
        ("mcpDetalle", laminas_dict["mcpDetalle"]),
        ("tool", laminas_dict["tool"]),
        ("skill", laminas_dict["skill"]),
        ("compara", laminas_dict["compara"]),
        ("red2", laminas_dict["red2"]),
        ("grafo", laminas_dict["grafo"]),
        ("miniGrafo", laminas_dict["miniGrafo"]),
        ("ahorro", laminas_dict["ahorro"]),
        ("citas", laminas_dict["citas"]),
        ("flujo", laminas_dict["flujo"]),
        ("caso", laminas_dict["caso"]),
        ("red3", laminas_dict["red3"]),
        ("api", laminas_dict["api"]),
        ("conectores", laminas_dict["conectores"]),
        ("ambiental", lamina_ambiental),
        ("herramientas", laminas_dict["herramientas"]),
        ("agentes", laminas_dict["agentes"]),
        ("mesa", laminas_dict["mesa"]),
        ("documentos", laminas_dict["documentos"]),
        ("doctrina", laminas_dict["doctrina"]),
        ("grafoHerramientas", laminas_dict["grafoHerramientas"]),
        ("estudio", laminas_dict["estudio"]),
        ("huggingface", laminas_dict["huggingface"]),
        ("cumplimiento", laminas_dict["cumplimiento"]),
        ("red5", laminas_dict["red5"]),
        ("frontera", laminas_dict["frontera"]),
        ("arco", laminas_dict["arco"]),
        ("sale", laminas_dict["sale"]),
        ("compuerta", laminas_dict["compuerta"]),
        ("red4", laminas_dict["red4"]),
        ("radiografia", lamina_radiografia),
        ("posNacional", lamina_posNacional),
        ("posGlobal", lamina_posGlobal),
        ("tablaComparativa", lamina_tablaComparativa),
        ("cifrasClave", lamina_cifrasClave),
        ("reglasOro", lamina_reglasOro),
        ("pruebaEnVivo", lamina_pruebaEnVivo),
        ("cierre", lamina_cierre),
    ]

    print(f"Total láminas a generar: {len(orden_50)}")
    assert len(orden_50) == 50, f"Se esperaban 50 láminas, hay {len(orden_50)}"

    # Lista de las 50 notas de orador perfectamente sincronizadas
    notas_50 = [
        # 1 a 26
        raw_notas[0],   # 1. Portada
        raw_notas[1],   # 2. Por qué nació
        raw_notas[2],   # 3. Para qué es
        raw_notas[3],   # 4. El puente
        raw_notas[4],   # 5. El mapa
        raw_notas[5],   # 6. LLM
        raw_notas[6],   # 7. Límites
        raw_notas[7],   # 8. Riesgo
        raw_notas[8],   # 9. ReAct
        raw_notas[9],   # 10. Agente
        raw_notas[10],  # 11. Harness
        raw_notas[11],  # 12. MCP
        raw_notas[12],  # 13. MCP por dentro
        raw_notas[13],  # 14. Tool
        raw_notas[14],  # 15. Skill
        raw_notas[15],  # 16. Compara
        raw_notas[16],  # 17. Red 2
        raw_notas[17],  # 18. Grafo
        raw_notas[18],  # 19. MiniGrafo
        raw_notas[19],  # 20. Ahorro
        raw_notas[20],  # 21. Citas
        raw_notas[21],  # 22. Flujo
        raw_notas[22],  # 23. Caso
        raw_notas[23],  # 24. Red 3
        raw_notas[24],  # 25. API
        raw_notas[25],  # 26. Conectores
        # 27. Ambiental (Especial Universidad de Los Lagos)
        "Jurisprudencia de los Tribunales Ambientales: 885 sentencias cosechadas de 1TA (110), 2TA (441) y 3TA Valdivia (334). Explicar los criterios rectores en la Región de Los Lagos: anaerobiosis por salmonicultura en Chiloé y Reloncaví, protección cautelar de humedales urbanos (Ley 21.202 en Osorno y Puerto Varas) y reparación in natura ecosistémica.",
        # 28 a 42 (antes 27 a 41)
        raw_notas[28],  # 28. Herramientas
        raw_notas[29],  # 29. Agentes
        raw_notas[30],  # 30. Mesa
        raw_notas[31],  # 31. Documentos
        raw_notas[32],  # 32. Doctrina
        raw_notas[33],  # 33. Grafo herramientas
        raw_notas[34],  # 34. Estudio docencia clínica
        raw_notas[35],  # 35. Hugging Face
        raw_notas[36],  # 36. Cumplimiento
        raw_notas[37],  # 37. Red 5
        raw_notas[38],  # 38. Frontera
        raw_notas[39],  # 39. ARCO
        raw_notas[40],  # 40. Sale
        raw_notas[41],  # 41. Compuerta
        raw_notas[42],  # 42. Red 4 (v1.6.5 GA)
        # 43 a 50 (las notas de cierre)
        raw_notas[43],  # 43. Radiografía operativa
        raw_notas[44],  # 44. Posicionamiento nacional
        raw_notas[45],  # 45. Posicionamiento global
        "Matriz comparativa: contrastar punto por punto privacidad local, costo cero, modelo Civil Law codificado y estándar abierto MCP frente a las suscripciones comerciales de USD $1.200 al mes de soluciones cerradas.",
        raw_notas[46],  # 47. Cifras clave (repasar 75 tools, 17.006 nodos, 885 ambientales, 259 pruebas)
        raw_notas[47],  # 48. Reglas de oro (subsunción tripartita)
        raw_notas[48],  # 49. Prueba en vivo (preguntas de la audiencia)
        raw_notas[49],  # 50. Cierre institucional y auditoría
    ]

    print(f"Total notas generadas: {len(notas_50)}")
    assert len(notas_50) == 50, f"Se esperaban 50 notas, hay {len(notas_50)}"

    # 4. Construir el bloque de llamadas lamina(...)
    deck_code_parts = []
    for k, (tag, body) in enumerate(orden_50):
        deck_code_parts.append(f'    /* ── Lámina {k+1} ── */\n    lamina(`{body.strip()}`, "{tag}");')
    
    deck_code = "\n".join(deck_code_parts)

    # 5. Extraer cabecera hasta antes de lamina(...)
    idx_lamina = bak_content.find("lamina(`")
    header = bak_content[:idx_lamina]
    
    # Asegurar que en el CSS y controles todo esté limpio
    header = header.replace("n\n<!DOCTYPE html>", "<!DOCTYPE html>")

    # 6. Extraer el pie (desde el final de la última lámina hasta el final del archivo)
    idx_last_lamina = bak_content.rfind("lamina(`")
    idx_end_last = bak_content.find(");", idx_last_lamina) + 2
    footer = bak_content[idx_end_last:]

    # 7. Agregar funciones de animación adicionales en footer
    nuevas_funciones_escena = """
    function escenaAmbiental(s) {
      const c = s.querySelector("#ambTribunales"), nota = s.querySelector("#ambNota");
      if (!c) return;
      c.innerHTML = "";
      const TRIBS = [
        ["1TA · Antofagasta", "110 sentencias", "Minería, salares y cuencas hídricas", "Arica a Coquimbo"],
        ["2TA · Santiago", "441 sentencias", "Proyectos interregionales, PdC y ruidos", "Valparaíso a Maule"],
        ["3TA · Valdivia (Los Lagos)", "334 sentencias", "Salmonicultura, humedales Ley 21.202 y daño", "Ñuble a Magallanes"]
      ];
      TRIBS.forEach(([nom, count, mat, jur], k) => {
        const card = document.createElement("div");
        card.className = "tarjeta";
        card.style.cssText = "padding:9px 12px;opacity:0;transform:translateY(8px);transition:all .45s";
        card.innerHTML = `<div style="display:flex;justify-content:space-between;align-items:center"><b style="color:var(--verde);font-size:12.5px">${nom}</b><span style="font-weight:700;color:var(--tinta);font-size:14px">${count}</span></div>
          <p style="font-size:11px;color:var(--gris);margin:3px 0 0"><b>Foco:</b> ${mat}</p>
          <p style="font-size:10px;color:var(--gris);margin:1px 0 0"><b>Jurisdicción:</b> ${jur}</p>`;
        c.appendChild(card);
        T(() => { card.style.opacity = 1; card.style.transform = "none"; }, 300 + k * 180);
      });
      T(() => {
        if (nota) nota.textContent = "885 sentencias y resoluciones definitivas indexadas en Open Legal Chile y Hugging Face.";
      }, 300 + TRIBS.length * 180);
    }
"""

    # Insertar nuevas funciones de animación antes de animar(s)
    idx_animar = footer.find("function animar(s)")
    footer = footer[:idx_animar] + nuevas_funciones_escena + "\n" + footer[idx_animar:]

    # Actualizar la función animar(s) para reconocer todos los tags de las 50 láminas
    animar_replacement = """      const esc = s.dataset.escena;
      if (esc === "mapa") escenaMapa(s);
      if (esc === "limites") escenaLimites(s);
      if (esc === "bucle") escenaBucle(s);
      if (esc === "harness") escenaHarness(s);
      if (esc === "mcpDetalle") escenaMCPDetalle(s);
      if (esc === "tool") escenaTool(s);
      if (esc === "compara") escenaCompara(s);
      if (esc === "api") escenaAPI(s);
      if (esc === "llm") escenaLLM(s);
      if (esc === "grafo") escenaGrafo(s);
      if (esc === "mcp") escenaMCP(s);
      if (esc === "flujo") escenaFlujo(s);
      if (esc === "caso") escenaCaso(s);
      if (esc === "citas") escenaCitas(s);
      if (esc === "ahorro") escenaAhorro(s);
      if (esc === "porque") escenaPorQue(s);
      if (esc === "paraQue") escenaParaQue(s);
      if (esc === "puente") escenaPuente(s);
      if (esc === "riesgo") escenaRiesgo(s);
      if (esc === "agente") escenaAgente(s);
      if (esc === "skill") escenaSkill(s);
      if (esc === "miniGrafo") escenaMiniGrafo(s);
      if (esc === "conectores") escenaConectores(s);
      if (esc === "ambiental") escenaAmbiental(s);
      if (esc === "herramientas") escenaHerramientas(s);
      if (esc === "agentes") escenaAgentes(s);
      if (esc === "mesa") escenaMesa(s);
      if (esc === "documentos") escenaDocumentos(s);
      if (esc === "doctrina") escenaDoctrina(s);
      if (esc === "grafoHerramientas") escenaGrafoHerramientas(s);
      if (esc === "estudio") escenaEstudio(s);
      if (esc === "cumplimiento") escenaCumplimiento(s);
      if (esc === "huggingface") escenaHuggingFace(s);
      if (esc === "frontera") escenaFrontera(s);
      if (esc === "arco") escenaArco(s);
      if (esc === "sale") escenaSale(s);
      if (esc === "compuerta") escenaCompuerta(s);
      if (esc === "red" || esc === "red2" || esc === "red3" || esc === "red5" || esc === "red4") redDeNodos(s);"""

    footer = re.sub(
        r'const esc = s\.dataset\.escena;[\s\S]*?if \(esc === "red" \|\| esc === "red2" \|\| esc === "red3" \|\| esc === "red5" \|\| esc === "red4"\) redDeNodos\(s\);',
        animar_replacement,
        footer
    )

    # Actualizar el array NOTAS en footer con las 50 notas oficiales
    notas_code = "const NOTAS = [\n" + ",\n".join(f'      "{n}"' for n in notas_50) + "\n    ];"
    footer = re.sub(r'const NOTAS = \[[\s\S]*?\];', notas_code, footer)

    # 8. Ensamblar el archivo final
    final_html = header + deck_code + footer

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(final_html)

    print(f"✓ ÉXITO: {OUTPUT_PATH} generado con 50 láminas magistrales y 50 notas alineadas.")

if __name__ == "__main__":
    main()
