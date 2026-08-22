---
name: brief-section-drafter
description: >
  Redactor de escritos judiciales y forenses para tribunales chilenos conforme
  a la Ley 20.886 de Tramitación Digital (Oficina Judicial Virtual - OJV) y los
  Códigos de Procedimiento (CPC, CPP, Código del Trabajo). Genera presuma,
  comparecencia, 'En lo principal' (Hechos, Derecho y Por Tanto) y otrosíes
  (Patrocinio y poder, documentos, exhortos, correo electrónico).
argument-hint: "[tipo de escrito, tribunal y pretensión o argumento a redactar]"
---

# /brief-section-drafter (Redactor Forense de Escritos Judiciales — Chile)

1. Cargar contexto del litigio o causa activa (`litigation-legal/CLAUDE.md`).
2. Identificar el tribunal competente (`S.J.L. en lo Civil`, `S.J.L. del Trabajo`, `I. Corte de Apelaciones`, `Excma. Corte Suprema`).
3. Estructurar el escrito según las formalidades de la **Ley 20.886 de Tramitación Digital (OJV)** y el **Código de Procedimiento Civil (CPC)**.
4. Desarrollar la argumentación jurídica con fundamentación legal estricta `[BCN - Norma, Art. XX]` y citas jurisprudenciales de tribunales superiores.
5. Formular peticiones concretas en el *POR TANTO* y estructurar los *OTROSÍES*.

---

## 1. Estructura Formal del Escrito Judicial Chileno (OJV)

```text
PROCEDIMIENTO  : [Ordinario / Ejecutivo / Laboral / Protección]
MATERIA        : [Cobro de pesos / Despido injustificado / Cumplimiento de contrato]
DEMANDANTE     : [Nombre o Razón Social], RUT: [XX.XXX.XXX-X]
ABOGADO PATROC.: [Nombre del Abogado/a], RUT: [XX.XXX.XXX-X]
DEMANDADO      : [Nombre o Razón Social], RUT: [XX.XXX.XXX-X]

                     S. J. L. [EN LO CIVIL / DEL TRABAJO] DE [CIUDAD]
                                   ([I. CORTE DE APELACIONES DE...])

[NOMBRE DEL COMPARECIENTE], [profesión u oficio], cédula nacional de identidad N° [RUT], domiciliado para estos efectos en [calle, número, comuna], en representación [convencional/legal] de [NOMBRE REPRESENTADO], según se acreditará, en autos sobre [materia], caratulados "[DEMANDANTE] con [DEMANDADO]", ROL [C/O/T/Laboral-XXX-YYYY], a US. respetuosamente digo:

EN LO PRINCIPAL: [Nombre de la presentación: Demanda / Contesta demanda / Deduce recurso de reposición con apelación en subsidio / Evacua traslado / Solicita medidas precautorias].
PRIMER OTROSÍ: Acompaña documentos bajo apercibimiento legal.
SEGUNDO OTROSÍ: Patrocinio y poder.
TERCER OTROSÍ: Notificaciones por correo electrónico (Ley 20.886).

                                  I. LOS HECHOS
[Relación circunstanciada, clara y cronológica de los antecedentes fácticos...]

                                 II. EL DERECHO
[Subsunción jurídica, análisis de artículos aplicables de los Códigos de la República y citas jurisprudenciales...]

                                   POR TANTO,
A US. RUEGO: Se sirva tener por deducida la presente [presentación/demanda/recurso], admitirla a tramitación y, en definitiva, [declarar / acoger / condenar a la contraparte a...], con expresa condenación en costas.

PRIMER OTROSÍ: A US. RUEGO se sirva tener por acompañados los siguientes documentos...
SEGUNDO OTROSÍ: A US. RUEGO tener presente que designo abogado patrocinante y confiero poder a...
TERCER OTROSÍ: A US. RUEGO ordenar que las resoluciones se notifiquen al correo electrónico [abogado@estudio.cl]...
```

---

## 2. Tipos de Escritos Procesales Soportados

### A. Escritos en Procedimiento Civil (CPC)
* **Demanda Ordinaria de Mayor Cuantía (Art. 254 CPC):** Requisitos formales intransables (designación del tribunal, individualización de partes, hechos circunstanciados, enunciación de fundamentos de derecho y peticiones concretas sometidas al fallo).
* **Demanda Ejecutiva (Art. 434 y ss. CPC):** Título ejecutivo perfecto o preparación de la vía ejecutiva, obligación líquida, actualmente exigible y no prescrita.
* **Excepciones Dilatorias (Art. 303 CPC):** Incompetencia, falta de capacidad/personería, litispendencia, ineptitud del libelo, beneficio de excusión.
* **Contestación de la Demanda (Art. 309 CPC):** Excepciones perentorias, defensas de fondo, allanamiento o reconvención.
* **Medidas Precautorias (Art. 290 CPC):** Secuestro, retención de bienes, prohibición de celebrar actos y contratos (acreditando presunción grave del derecho y peligro en la mora).

### B. Escritos en Procedimiento Laboral (Código del Trabajo)
* Demanda de Despido Injustificado, Indebido o Improcedente (Art. 168 y 446).
* Denuncia por Vulneración de Derechos Fundamentales con ocasión del despido / Tutela Laboral (Art. 485 y ss.).
* Contestación de demanda laboral y excepciones de caducidad/prescripción.

### C. Recursos Procesales
* **Recurso de Reposición (Art. 181 CPC):** Contra autos y decretos; reposición con apelación en subsidio contra sentencias interlocutorias cuando la ley lo permite (plazo 3 o 5 días).
* **Recurso de Apelación (Art. 186 y ss. CPC):** Fundamentos de hecho y de derecho y peticiones concretas de reforma de la resolución (plazo 5 o 10 días según el tipo de resolución).
* **Acción Constitucional de Protección (Art. 20 CPR):** Ante la I. Corte de Apelaciones respectiva dentro del plazo fatal de 30 días corridos desde el acto u omisión arbitrario o ilegal que afecte garantías constitucionales protegidas.

---

## 3. Cómputo de Plazos Procesales en Chile

> ⚠️ **Regla Fundamental de Plazos Procesales (Art. 66 CPC):**
> * En materia civil, los plazos de días son de **días hábiles** (se excluyen únicamente los días domingos y feriados; **los sábados son días hábiles judiciales**).
> * Los plazos son fatales por el solo ministerio de la ley (Art. 64 CPC).
> * En el Recurso de Protección el plazo es de **30 días corridos** (Auto Acordado CS).

---

## Formato de Salida del Escrito

El escrito generado se entrega con el formato textual listo para copiar, pegar y subir a la plataforma de la **Oficina Judicial Virtual (OJV)** o exportar a formato procesal (.docx / .pdf).
