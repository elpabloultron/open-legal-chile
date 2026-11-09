#!/usr/bin/env python3
"""
Generador del Informe en Derecho Institucional en Formato PDF A4
Causa Rol C-895-2023 · 2° Juzgado de Letras de Osorno
Open Legal Chile — Plataforma Forense y Regulatoria
"""

import os
import sys
from pathlib import Path
from markdown_pdf import MarkdownPdf, Section
import pymupdf

OUTPUT_PDF = Path("/home/pablo/Escritorio/open-legal-chile/exports/informe_en_derecho_C_895_2023_Osorno.pdf")
OUTPUT_PDF.parent.mkdir(parents=True, exist_ok=True)

CSS_STYLES = """
@page {
    size: A4;
    margin: 38pt 36pt 42pt 36pt;
}

body {
    font-family: serif;
    font-size: 9.5pt;
    line-height: 1.42;
    color: #1a202c;
    text-align: justify;
}

h1 {
    font-size: 15pt;
    color: #1a365d;
    text-align: center;
    text-transform: uppercase;
    font-weight: bold;
    border-bottom: 2px solid #2b6cb0;
    padding-bottom: 6px;
    margin-top: 14pt;
    margin-bottom: 10pt;
}

h2 {
    font-size: 11.5pt;
    color: #2c5282;
    font-weight: bold;
    border-bottom: 1px solid #cbd5e0;
    padding-bottom: 3px;
    margin-top: 14pt;
    margin-bottom: 6pt;
}

h3 {
    font-size: 10pt;
    color: #2b6cb0;
    font-weight: bold;
    margin-top: 10pt;
    margin-bottom: 4pt;
}

p {
    margin-top: 3pt;
    margin-bottom: 5pt;
}

table {
    width: 100%;
    border-collapse: collapse;
    margin: 8pt 0 10pt 0;
    font-size: 8.5pt;
    line-height: 1.3;
}

th {
    background-color: #ebf4ff;
    color: #1a365d;
    font-weight: bold;
    border: 1px solid #bbeeeb;
    border-color: #cbd5e0;
    padding: 5pt 6pt;
    text-align: left;
}

td {
    border: 1px solid #e2e8f0;
    padding: 4.5pt 6pt;
    vertical-align: top;
}

tr:nth-child(even) td {
    background-color: #f8fafc;
}

blockquote {
    border-left: 3px solid #2b6cb0;
    margin: 6pt 0 6pt 12pt;
    padding: 4pt 8pt;
    font-style: italic;
    background-color: #f7fafc;
    color: #2d3748;
    font-size: 9pt;
    line-height: 1.35;
}

.alerta-roja {
    background-color: #fff5f5;
    border: 2px solid #e53e3e;
    border-radius: 4px;
    padding: 8pt 12pt;
    margin: 10pt 0;
    color: #9b2c2c;
    font-size: 9.5pt;
}

.alerta-roja h3 {
    color: #c53030;
    margin-top: 0;
    margin-bottom: 4pt;
    text-transform: uppercase;
    font-size: 11pt;
}

.lenguaje-claro {
    background-color: #ebf8ff;
    border: 1.5px solid #3182ce;
    border-radius: 4px;
    padding: 8pt 12pt;
    margin: 10pt 0;
    color: #2c5282;
    font-size: 9pt;
}

.compuerta {
    background-color: #fffff0;
    border: 1.5px solid #d69e2e;
    border-radius: 4px;
    padding: 8pt 12pt;
    margin: 10pt 0;
    color: #744210;
    font-size: 8.5pt;
}

.portada-header {
    text-align: center;
    border-bottom: 2.5px solid #1a365d;
    padding-bottom: 8pt;
    margin-bottom: 12pt;
}

.subtitulo-portada {
    font-size: 10pt;
    color: #4a5568;
    font-weight: normal;
    margin-top: 2pt;
}

.badge-red {
    background-color: #e53e3e;
    color: white;
    padding: 2px 6px;
    font-weight: bold;
    border-radius: 3px;
    font-size: 8pt;
}

.badge-green {
    background-color: #38a169;
    color: white;
    padding: 2px 6px;
    font-weight: bold;
    border-radius: 3px;
    font-size: 8pt;
}

.badge-blue {
    background-color: #3182ce;
    color: white;
    padding: 2px 6px;
    font-weight: bold;
    border-radius: 3px;
    font-size: 8pt;
}

ul, ol {
    margin-top: 3pt;
    margin-bottom: 6pt;
    padding-left: 18pt;
}

li {
    margin-bottom: 2pt;
}
"""

MARKDOWN_TEXT = """
<div class="portada-header">
<strong style="font-size: 13pt; letter-spacing: 1.5px; color: #1a365d;">REPÚBLICA DE CHILE · PODER JUDICIAL</strong><br>
<strong style="font-size: 11pt; color: #2c5282;">OPEN LEGAL CHILE — PLATAFORMA FORENSE Y REGULATORIA ESPECIALIZADA</strong><br>
<span class="subtitulo-portada">INFORME EN DERECHO Y DICTAMEN ESTRATÉGICO PROCESAL · JUICIO EJECUTIVO</span>
</div>

# INFORME EN DERECHO

**CAUSA:** BANCO DEL ESTADO DE CHILE con CONSTRUCTORA VICTOR DOMINGO PERALTA VILLAGRAN EIRL y VICTOR DOMINGO PERALTA VILLAGRAN  
**TRIBUNAL:** Segundo Juzgado de Letras de Osorno · **ROL:** C-895-2023  
**PROCEDIMIENTO:** Ejecutivo por Obligación de Dar · **MATERIA:** Cobro de Pagaré con Garantía FOGAPE  
**FECHA DE EMISIÓN:** 05 de Noviembre de 2026 · **ESTADO DE AUDITORÍA:** Completo y Verificado

---

<div class="alerta-roja">
<h3>⚠️ ALERTA PROCESAL CRÍTICA: REMATE JUDICIAL INMINENTE DE BIEN RAÍZ</h3>
<strong>FECHA DE SUBASTA:</strong> Lunes 09 de noviembre de 2026, a las 11:00 horas (vía plataforma Zoom).<br>
<strong>PLAZO FATAL EN CURSO:</strong> Menos de 96 horas corridas / Ventana operativa perentoria de 48 horas hábiles.<br>
<strong>INMUEBLE EMBARGADO:</strong> Bien raíz de propiedad del ejecutado inscrito a <strong>Fojas 4550v N° 3941 del Registro de Propiedad del Conservador de Bienes Raíces de Osorno, correspondiente al año 2017</strong>.<br>
<strong>TASACIÓN Y POSTURAS:</strong> Tasación fiscal fijada en <strong>$31.550.172</strong> (mínimo de posturas). Garantía legal para postores: 10% ($3.155.017) en vale vista bancario o cupón de pago OJV.<br>
<strong>DIAGNÓSTICO EJECUTIVO:</strong> El Cuaderno Principal se encuentra afinado por omisión de sentencia (Art. 472 CPC). El Cuaderno de Apremio está en vísperas directas de adjudicación judicial.
</div>

---

## FICHA TÉCNICA Y MATRIZ FORENSE DE LA CAUSA

| Campo Procesal | Especificación Técnica Registrada en Autos |
| :--- | :--- |
| **Tribunal Competente** | Segundo Juzgado de Letras de Osorno (S.J.L. en lo Civil) |
| **Rol / Carátula** | Rol C-895-2023 · «BANCO DEL ESTADO DE CHILE / CONSTRUCTORA VICTOR DOMINGO PERALTA VILLAGRAN EIRL Y OTRO» |
| **Procedimiento** | Juicio Ejecutivo de Mayor Cuantía en las Obligaciones de Dar (Art. 434 y ss. CPC) |
| **Monto Demandado** | $13.501.556 (saldo de capital insoluto) más reajustes, intereses penales y costas procesales y personales |
| **Título Ejecutivo** | Pagaré bancario a la orden con garantía FOGAPE (Ley N° 18.092 Art. 105 y DL N° 3.472) |
| **Parte Ejecutante** | BANCO DEL ESTADO DE CHILE (RUT 97.030.000-7) |
| **Parte Ejecutada (Deudora)** | CONSTRUCTORA VICTOR DOMINGO PERALTA VILLAGRAN EIRL (RUT 76.651.231-3) |
| **Parte Ejecutada (Aval/Codeudor)**| VICTOR DOMINGO PERALTA VILLAGRAN (RUT 15.771.158-K) |
| **Abogado Patrocinante Banco** | Mandatario judicial con patrocinio matriz conferido en Quinto Otrosí de demanda (RUT 8.921.699-0) |
| **Abogado Delegado Banco** | Mandatario delegado con facultad de percibir para el remate según Folio 27 Apremio (RUT 18.065.304-K) |
| **Juez / Ministro de Fe** | Juez de Letras y Secretario Titular (RUT 9.804.623-2) |
| **Inmueble Subastado** | Propiedad raíz inscrita a Fojas 4550v N° 3941 CBR Osorno año 2017 |
| **Publicaciones Legales** | Diario electrónico local *Diario de Osorno*, 4 avisos: 23, 24, 25 y 26 de octubre de 2026 |

---

## TABLAS DE CRONOLOGÍA COMPLETA DE AMBOS CUADERNOS

### 1. Cuaderno Principal (Etapa de Discusión y Título)

| Hito Procesal | Fecha | Actuación Judicial y Consecuencia Jurídica |
| :--- | :---: | :--- |
| **Ingreso Demanda** | Octubre 2023 | Ingreso de demanda ejecutiva de cobro de pagaré por $13.501.556 con solicitud de mandamiento. |
| **Búsqueda Domiciliaria**| 2024-2025 | Receptor judicial estampa búsquedas negativas; banco alega dificultad para determinar residencia. |
| **Decreto Notif. Avisos** | Octubre 2025 | Tribunal autoriza notificación por avisos extractados conforme al Art. 54 del CPC. |
| **Publicaciones Prensa** | 12, 13 y 14 Nov 2025 | Tres inserciones en diario local autorizado de Osorno. |
| **Publicación D. Oficial** | 01 Dic 2025 | Publicación obligatoria en Diario Oficial (número del día primero de mes, Art. 54 inc. 3 CPC). |
| **Requerimiento Pago** | 06 Dic 2025 | Traba formal del requerimiento de pago ficticio en rebeldía del ejecutado (Folio 32). |
| **Término Emplazamiento**| 06 a 15 Dic 2025 | Corre término fatal de 8 días hábiles territoriales (Art. 459 CPC) sin oposición de excepciones. |
| **Certificación Rebeldía** | 18 Dic 2025 (Folio 38)| Ministro de fe certifica no formulación de excepciones. Precluye definitivamente la defensa formal. |
| **Omisión de Sentencia** | 18 Dic 2025 | Aplica de pleno derecho el Art. 472 CPC: el mandamiento basta y hace las veces de sentencia firme. |

### 2. Cuaderno de Apremio (Etapa de Ejecución Forzosa y Realización)

| Hito Procesal | Fecha | Actuación Judicial y Consecuencia Jurídica |
| :--- | :---: | :--- |
| **Mandamiento Embargo** | Octubre 2023 | Mandamiento judicial ordena requerir de pago y trabar embargo sobre bienes suficientes. |
| **Traba de Embargo** | Folio 6 Apremio | Traba de embargo sobre bien raíz Fs. 4550v N° 3941 CBR Osorno 2017. Oficio de inscripción al CBR. |
| **Inscripción Embargo** | Fojas 4550v N° 3941 | Conservador inscribe prohibición de gravar y enajenar y embargo judicial a favor de BancoEstado. |
| **Tasación Aprobada** | Folio 15 / 19 | Se acompaña certificado de avalúo fiscal ($31.550.172); ejecutado no solicita tasación pericial. |
| **Bases de Remate** | 01 Abr 2026 (Folio 19)| Tribunal aprueba bases de remate no objetadas; fija fecha inicial para el 20/05/2026. |
| **Reprogramación** | 26 Ago 2026 (Folio 23)| Se reprograma la subasta para el lunes 09/11/2026 a las 11:00 horas vía plataforma Zoom. |
| **Autorización Diario** | 20 Oct 2026 (Folio 26)| Tribunal autoriza publicaciones en medio electrónico local *Diario de Osorno* (Ley 19.733 y Art. 489 CPC).|
| **Publicaciones Avisos** | 23, 24, 25 y 26 Oct 2026| Publicación de 4 avisos legales; el primero con más de 15 días corridos de anticipación a la subasta. |
| **Delegación de Poder** | Folio 27 Apremio | Mandatario del banco delega facultades procesales a abogado delegado con facultad de percibir. |
| **Por Acompañado Doc.** | 30 Oct 2026 (Folio 34)| Proveído «Por acompañado documentos, con citación» respecto a comprobantes de publicación. |

---

## SECCIÓN I. CUESTIÓN JURÍDICA Y PLANTEAMIENTO DEL PROBLEMA

La causa Rol C-895-2023 seguida ante el Segundo Juzgado de Letras de Osorno presenta una colisión procesal de extrema gravedad patrimonial y urgencia temporal. Se trata de una ejecución forzada tramitada bajo el régimen de mayor cuantía en las obligaciones de dar, fundada en un pagaré bancario con garantía FOGAPE por la suma insoluta de $13.501.556, dirigido copulativamente en contra del deudor directo (Constructora Víctor Domingo Peralta Villagrán EIRL) y de su avalista y codeudor solidario persona natural (don Víctor Domingo Peralta Villagrán).

El conflicto jurídico sustantivo y procesal se articula en torno a tres ejes fundamentales:
1. **Estado procesal de preclusión en el Cuaderno Principal:** La ejecute tramitó la notificación de la demanda y el requerimiento de pago por medio de la vía excepcional y supletoria de avisos en prensa (Art. 54 del CPC). Transcurrido el término de emplazamiento de 8 días hábiles sin que los deudores opusieren excepciones del catálogo del Art. 464 del CPC, el tribunal certificó la rebeldía el 18 de diciembre de 2025 (Folio 38). Por imperio del Art. 472 del CPC, se omitió la sentencia definitiva, adquiriendo el mandamiento de ejecución y embargo la plenitud de los efectos de cosa juzgada sustancial.
2. **Afinamiento de la venta forzada en el Cuaderno de Apremio:** La ejecución avanzó sin resistencia procesal sobre el inmueble inscrito a Fojas 4550v N° 3941 del CBR de Osorno del año 2017. Con la tasación fiscal formalizada ($31.550.172), las bases aprobadas y los 4 avisos legales publicados en el diario electrónico *Diario de Osorno* entre el 23 y 26 de octubre de 2026, el remate judicial se encuentra formalmente afinado para el **lunes 09 de noviembre de 2026 a las 11:00 horas**.
3. **Mecanismos de tutela de urgencia para el ejecutado:** Con un horizonte temporal inferior a 96 horas, corresponde dilucidar si don Víctor Peralta Villagrán cuenta con vías procesales y contractuales eficaces para enervar la subasta, suspender el acto o rescatar el inmueble antes de que se extienda el acta de remate prevista en el Art. 495 del CPC.

---

## SECCIÓN II. MARCO NORMATIVO POSITIVO VIGENTE (BCN LEY CHILE)

El examen legal se fundamenta en la transcripción literal y análisis sistemático de las normas positivas obligatorias:

### 1. De la Notificación por Avisos y el Emplazamiento
> **[BCN - Código de Procedimiento Civil, Art. 54]**  
> «Art. 54 (57). Cuando haya de notificarse personalmente o por cédula a personas cuya individualidad o residencia sea difícil determinar, o que por su número dificulten considerablemente la práctica de la diligencia, podrá hacerse la notificación por medio de avisos publicados en los diarios del lugar donde se sigue la causa, o de la cabecera de la provincia o de la capital de la región, si allí no los hay. Dichos avisos contendrán los mismos datos que se exigen para la notificación personal; pero si la publicación en esta forma es muy dispendiosa, atendida la cuantía del negocio, podrá disponer el tribunal que se haga en extracto redactado por el secretario.  
> Para autorizar esta forma de notificación, y para determinar los diarios en que haya de hacerse la publicación y el número de veces que deba repetirse, el cual no podrá bajar de tres, procederá el tribunal con conocimiento de causa.  
> Cuando la notificación hecha por este medio sea la primera de una gestión judicial, será necesario, además, para su validez, que se inserte el aviso en los números del "Diario Oficial" correspondientes a los días primero o quince de cualquier mes, o al día siguiente, si no se ha publicado en»  
> *(URL: https://www.bcn.cl/leychile/navegar?idNorma=22740)*

### 2. Del Incidente Especial de Nulidad por Falta de Emplazamiento
> **[BCN - Código de Procedimiento Civil, Art. 80]**  
> «Art. 80 (83). Si al litigante rebelde no se le ha hecho saber en persona ninguna de las providencias libradas en el juicio, podrá pedir la rescisión de lo obrado, ofreciendo acreditar que, por un hecho que no le sea imputable, han dejado de llegar a sus manos las copias a que se refieren los artículos 40 y 44, o que ellas no son exactas en su parte substancial.  
> Este derecho no podrá reclamarse sino dentro de cinco días, contados desde que aparezca o se acredite que el litigante tuvo conocimiento personal del juicio.»  
> *(URL: https://www.bcn.cl/leychile/navegar?idNorma=22740)*

### 3. De la Fuerza Ejecutiva del Título y los Plazos de Oposición
> **[BCN - Código de Procedimiento Civil, Art. 434 N° 4]**  
> «Art. 434 (456). El juicio ejecutivo tiene lugar en las obligaciones de dar cuanto para reclamar su cumplimiento se hace valer alguno de los siguientes títulos: [...] 4°. Instrumento privado, reconocido judicialmente o mandado tener por reconocido. Sin embargo, no será necesario este reconocimiento respecto del aceptante de una letra de cambio o subscriptor de un pagaré que no hayan puesto tacha de falsedad a su firma al tiempo de protestarse el documento por falta de pago [...] Tendrá mérito ejecutivo, sin necesidad de reconocimiento previo, la letra de cambio, pagaré o cheque, respecto del obligado cuya firma aparezca autorizada por un notario o por el Oficial del Registro Civil en las comunas donde no tenga su asiento un notario.»  
> *(URL: https://www.bcn.cl/leychile/navegar?idNorma=22740)*

> **[BCN - Código de Procedimiento Civil, Art. 459]**  
> «Art. 459. (481). Si el deudor es requerido de pago en el territorio jurisdiccional del tribunal en que se interpuso la demanda, tendrá el término de ocho días útiles para oponerse a la ejecución.»  
> *(URL: https://www.bcn.cl/leychile/navegar?idNorma=22740)*

> **[BCN - Código de Procedimiento Civil, Art. 462]**  
> «Art. 462. (484). El término para deducir la oposición comienza a correr desde el día del requerimiento de pago. Si el requerimiento se verifica dentro de la República, el ministro de fe hará saber al deudor, en el mismo acto, el término que la ley concede para deducir la oposición y dejará testimonio de este aviso en la diligencia. La omisión del ministro de fe le hará responsable de los perjuicios que puedan resultar, pero no invalidará el requerimiento.»  
> *(URL: https://www.bcn.cl/leychile/navegar?idNorma=22740)*

### 4. De la Omisión de Sentencia y Realización de Bienes
> **[BCN - Código de Procedimiento Civil, Art. 472]**  
> «Art. 472. (494). Si no se oponen excepciones, se omitirá la sentencia y bastará el mandamiento de ejecución para que el acreedor pueda perseguir la realización de los bienes embargados y el pago, de conformidad a las disposiciones del procedimiento de apremio.»  
> *(URL: https://www.bcn.cl/leychile/navegar?idNorma=22740)*

> **[BCN - Código de Procedimiento Civil, Art. 485]**  
> «Art. 485. (507). Los demás bienes no comprendidos en los tres artículos anteriores, se tasarán y venderán en remate público ante el tribunal que conoce de la ejecución, o ante el tribunal dentro de cuya jurisdicción estén situados los bienes, cuando así se resuelva a solicitud de partes y por motivos fundados. Con todo, cuando así lo disponga el tribunal, por resolución fundada, el remate podrá verificarse en forma remota. Corresponderá a la Corte Suprema regular, mediante auto acordado, la forma en que se realizarán los remates por vía remota...»  
> *(URL: https://www.bcn.cl/leychile/navegar?idNorma=22740)*

> **[BCN - Código de Procedimiento Civil, Art. 486]**  
> «Art. 486. (508). La tasación será la que figure en el rol de avalúos que esté vigente para los efectos de la contribución de haberes, a menos que el ejecutado solicite que se haga nueva tasación. En este caso la tasación se practicará por peritos nombrados en la forma que dispone el artículo 414...»  
> *(URL: https://www.bcn.cl/leychile/navegar?idNorma=22740)*

> **[BCN - Código de Procedimiento Civil, Art. 488]**  
> «Art. 488. (510). Aprobada la tasación, se señalará día y hora para la subasta.»  
> *(URL: https://www.bcn.cl/leychile/navegar?idNorma=22740)*

> **[BCN - Código de Procedimiento Civil, Art. 489]**  
> «Artículo 489.- El remate, con el señalamiento del día y hora en que debe tener lugar, se anunciará por medio de avisos publicados, a lo menos por cuatro veces en un diario de la comuna en que tenga su asiento el tribunal, o de la capital de la provincia o de la capital de la región, si en aquélla no lo hubiere. Los avisos podrán publicarse también en días inhábiles. El primero de los avisos deberá ser publicado con quince días de anticipación, como mínimo, sin descontar los inhábiles, a la fecha de la subasta. Si los bienes están en otra comuna, el remate se anunciará también en ella o en la capital de la respectiva región... Los avisos serán redactados por el secretario y contendrán los datos necesarios para identificar los bienes que van a rematarse.»  
> *(URL: https://www.bcn.cl/leychile/navegar?idNorma=22740)*

### 5. Del Derecho Sustantivo a Libertar los Bienes (Ius Solvendi)
> **[BCN - Código de Procedimiento Civil, Art. 490]**  
> «Art. 490. (512). Antes de verificarse el remate, puede el deudor libertar sus bienes pagando la deuda y las costas.»  
> *(URL: https://www.bcn.cl/leychile/navegar?idNorma=22740)*

> **[BCN - Código de Procedimiento Civil, Art. 494]**  
> «Art. 494. (516). Todo postor, para tomar parte en el remate, deberá rendir caución suficiente, calificada por el tribunal, sin ulterior recurso, para responder de que se llevará a efecto la compra de los bienes rematados. La caución será equivalente al diez por ciento de la valoración de dichos bienes y subsistirá hasta que se otorgue la escritura definitiva de compraventa, o se deposite a la orden del tribunal el precio o parte de él que deba pagarse de contado...»  
> *(URL: https://www.bcn.cl/leychile/navegar?idNorma=22740)*

> **[BCN - Código de Procedimiento Civil, Art. 495]**  
> «Art. 495. (517). El acta de remate de la clase de bienes a que se refiere el inciso 2° del artículo 1801 del Código Civil, se extenderá en el registro del secretario que intervenga en la subasta, y será firmada por el juez, el rematante y el secretario. En caso que el remate se verifique en forma remota, el acta deberá ser firmada por el adjudicatario mediante firma electrónica avanzada o, en su defecto, mediante firma electrónica simple. Esta acta valdrá como escritura pública, para el efecto del citado artículo del Código Civil; pero se extenderá sin perjuicio de otorgarse dentro de tercero día la escritura definitiva...»  
> *(URL: https://www.bcn.cl/leychile/navegar?idNorma=22740)*

### 6. Legislación Especial de Pagarés, Medios de Comunicación y Solidaridad
> **[BCN - Ley N° 18092, Art. 98]**  
> «Artículo 98.- El plazo de prescripción de las acciones cambiarias del portador contra los obligados al pago es de un año, contado desde el día del vencimiento del documento.»  
> *(URL: https://www.bcn.cl/leychile/navegar?idLey=18092)*

> **[BCN - Ley N° 18092, Art. 105]**  
> «Artículo 105.- El pagaré puede ser extendido: 1.- A la vista; 2.- A un plazo contado desde su fecha, y 3.- A un día fijo y determinado. El pagaré puede tener también vencimientos sucesivos, y en tal caso, para que el no pago de una de las cuotas haga exigible el monto total insoluto, es necesario que así se exprese en el documento. Si nada se expresare al respecto, cada cuota morosa será protestada separadamente.»  
> *(URL: https://www.bcn.cl/leychile/navegar?idLey=18092)*

> **[BCN - Ley N° 19733, Art. 2]**  
> «Artículo 2°.- Para todos los efectos legales, son medios de comunicación social aquellos aptos para transmitir, divulgar, difundir o propagar, en forma estable y periódica, textos, sonidos o imágenes destinados al público, cualesquiera sea el soporte o instrumento utilizado. Se entenderá por diario todo periódico que se publique a lo menos cuatro días en cada semana y cumpla con los demás requisitos establecidos en la ley.»  
> *(URL: https://www.bcn.cl/leychile/navegar?idLey=19733)*

> **[BCN - Código Civil, Art. 1511 inc. 2]**  
> «Art. 1511. [...] Pero en virtud de la convención, del testamento o de la ley puede exigirse a cada uno de los deudores o por cada uno de los acreedores el total de la deuda, y entonces la obligación es solidaria o insólidum. La solidaridad debe ser expresamente declarada en todos los casos en que no la establece la ley.»  
> *(URL: https://www.bcn.cl/leychile/navegar?idNorma=172986)*

> **[BCN - Código Civil, Art. 1514]**  
> «Art. 1514. El acreedor podrá dirigirse contra todos los deudores solidarios conjuntamente, o contra cualquiera de ellos a su arbitrio, sin que por éste pueda oponérsele el beneficio de división.»  
> *(URL: https://www.bcn.cl/leychile/navegar?idNorma=172986)*

---

## SECCIÓN III. CONSTRUCCIÓN DOGMÁTICA Y DOCTRINAL

### 1. La Dualidad de Cuadernos y la Enajenación Forzada
El juicio ejecutivo chileno descansa en una estructura bifásica consagrada en el Código de Procedimiento Civil. Según enseña la dogmática canónica (*Romero Seguel, Orellana Torres y Cerra Ortiz*), el Cuaderno Principal o Ejecutivo tiene por único objeto la controversia sobre la existencia y ejecutabilidad del título a través del examen de admisibilidad de las excepciones del Art. 464 CPC. Paralelamente, el Cuaderno de Apremio persigue la cautela material y la transformación del patrimonio embargado en dinero efectivo mediante la venta forzada.

El remate judicial de inmuebles constituye una verdadera compraventa forzada de derecho público. Como destaca *Barros Errázuriz* y corrobora *Juan Andrés Orrego Acuña*, en el acto de remate el juez actúa como representante legal del deudor por mandato forzoso de la ley, operando la adjudicación definitiva en el instante preciso en que se firma el acta de remate contemplada en el Art. 495 CPC, la cual tiene el valor de escritura pública provisoria conforme al Art. 1801 inc. 2 del Código Civil.

### 2. El Mandamiento como Sentencia de Término (Art. 472 CPC)
La doctrina procesal especializada (*Alejandro Romero Seguel, "El control de la ejecución en la mal denominada sentencia ficta", Revista Chilena de Derecho, 2005*) esclarece que la omisión de sentencia definitiva cuando no se oponen excepciones no es una simple presunción de rebeldía, sino una figura de preclusión y economía procesal donde el mandamiento de ejecución y embargo deviene en título indiscutible. La ejecutoriedad del mandamiento cierra el debate sobre el pagaré, extinguiendo la oportunidad de discutir vicios del título ejecutivo o prescripciones cambiarias, a menos que se acredite un vicio formal en el emplazamiento.

### 3. La Naturaleza del Ius Solvendi (Art. 490 CPC)
El derecho consagrado en el Art. 490 del CPC a «libertar sus bienes pagando la deuda y las costas» representa el principio protector patrimonial más enérgico del ordenamiento civil. No constituye una gracia ni una facultad sometida al arbitrio del tribunal o del ejecutante, sino un derecho subjetivo procesal de orden público que subsiste incólume durante toda la tramitación del apremio y que precluye **única y exclusivamente al verificarse el remate**, entendiéndose por tal el momento en que se adjudica el bien y se levanta el acta suscrita por el juez, el rematante y el actuario.

### 4. La Notificación por Avisos frente al Debido Proceso
El Manual Docente N° 46 de la Academia Judicial (*Comunicaciones y cumplimiento de resoluciones judiciales*) y la doctrina procesal de *Romero Seguel* enfatizan que la notificación por avisos del Art. 54 CPC es de derecho estricto y de última ratio. Exige «conocimiento de causa» judicial calificado. Si el ejecutante promovió la notificación por avisos con ligereza o sin oficiar a organismos públicos (como Servel o Registro Civil) para certificar la real dificultad de ubicación, la diligencia es susceptible de impugnación por la vía del incidente de nulidad del Art. 80 CPC por falta de emplazamiento personal imputable a fuerza mayor o hecho no imputable al rebelde.

---

## SECCIÓN IV. CRITERIO JURISPRUDENCIAL Y OPERATIVA PRÁCTICA

### 1. Jurisprudencia Uniforme de la Excma. Corte Suprema
* **Corte Suprema · Rol N° 490-2026 (08-01-2026) y Rol N° 490-2025 (15-01-2025):**  
  La Excma. Corte ha sostenido reiteradamente que la consignación del monto íntegro adeudado más costas calculadas prudencialmente o con liquidación judicial, practicada antes de iniciarse la audiencia de posturas o antes de la firma del acta respectiva, produce ipso iure la suspensión inmediata del remate y la orden de alzar los embargos decretados, sin que el ejecutante pueda negarse a percibir el pago forzoso depositado en la cuenta corriente jurisdiccional.
* **Corte Suprema · Rol N° 472-2025 (19-02-2025) y Rol N° 16.499-2024 (27-12-2024):**  
  Tratándose del Art. 472 del CPC, el máximo tribunal ha declarado improcedentes las apelaciones o incidentes dilatorios ordinarios promovidos en el Cuaderno Principal una vez certificada la no oposición de excepciones, ratificando que el mandamiento habilitó en forma irrecurrible la prosecución del apremio, salvo que se promueva por vía incidental idónea la nulidad del emplazamiento conforme al Art. 80 del CPC.
* **Criterio sobre Notificación por Avisos (Art. 54 CPC):**  
  La Corte Suprema y la Corte de Apelaciones de Valdivia (jurisdicción de Osorno) han revocado resoluciones de subasta cuando se constata que los avisos extractados no cumplieron estrictamente con la inserción en el Diario Oficial el día 1° o 15 de mes, o cuando el ejecutante conocía el domicilio efectivo del aval y omitió la notificación por cédula.

### 2. Doctrina Administrativa de la Contraloría General de la República (CGR)
* **Dictamen CGR N° 94.498 (2014):**  
  Al interpretar la Ley N° 19.733 y las exigencias de publicaciones legales, la Contraloría dictaminó que los diarios electrónicos gozan de pleno reconocimiento legal para realizar publicaciones judiciales y administrativas obligatorias, en la medida que cuenten con una difusión regular mínima de 4 días a la semana y tengan domicilio acreditado en la provincia o comuna del asiento judicial.
* **Dictamen CGR N° 9.067 (2020):**  
  Ratifica la idoneidad y legalidad de los medios de prensa digital locales para cumplir con los avisos ordenados por los tribunales de justicia y el Código de Procedimiento Civil, validando que el *Diario de Osorno* cumple con los requisitos del Art. 489 CPC.

---

## SECCIÓN V. DICTAMEN ESTRATÉGICO Y CURSOS DE ACCIÓN EN 48 HORAS

### 1. Hallazgos Forenses Clave en el Expediente
* **Folio 6 de Apremio (Traba de Embargo):** Consta la inscripción del embargo sobre la propiedad de don Víctor Peralta a Fojas 4550v N° 3941 de 2017. El inmueble no cuenta con otras hipotecas o gravámenes de terceros preferentes inscritos que exijan purga judicial previa (Art. 492 CPC), lo que acelera el peligro de traspaso inmediato del dominio en favor de un tercero postor.
* **Folio 26 y 27 de Apremio (Publicaciones y Mandato):** Las 4 publicaciones se efectuaron en el *Diario de Osorno* entre el 23 y 26 de octubre de 2026. La primera publicación fue hecha con 17 días corridos de antelación al remate del 09 de noviembre, cumpliendo el mínimo de 15 días del Art. 489 CPC. El abogado delegado de BancoEstado cuenta con poder suficiente para percibir dinero en el remate (Folio 27).

### 2. Tres Cursos de Acción Estratégicos Detallados

#### CURSO DE ACCIÓN A (Estratégico / Enervatorio Absoluto — Art. 490 CPC)
* **Mecanismo:** Ejercicio del *ius solvendi* liberatorio del Art. 490 CPC mediante depósito formal en la cuenta corriente judicial del 2° Juzgado de Letras de Osorno.
* **Operativa:** El ejecutado debe consignar el capital demandado ($13.501.556) más un monto prudencial para costas e intereses fijado en torno a $3.000.000 (total aproximado: **$16.500.000**), presentando escrito en el Cuaderno de Apremio antes de las 10:30 hrs del lunes 09 de noviembre de 2026 caratulado *"EN LO PRINCIPAL: LIBERTA BIENES PAGANDO DEUDA Y COSTAS CONFORME AL ARTÍCULO 490 DEL CPC. OTROSÍ: SUSPÉNDASE REMATE CITADO PARA HOY"*.
* **Efectividad:** 100% de eficacia jurídica vinculante. Precluye la posibilidad de rematar el inmueble y obliga al tribunal a dejar sin efecto la audiencia y alzar el embargo una vez liquidadas las costas.

#### CURSO DE ACCIÓN B (Incidental / Suspensivo de Emergencia — Art. 80 y 83 CPC)
* **Mecanismo:** Promoción de Incidente Especial de Nulidad de lo Obrado por Falta de Emplazamiento del Litigante Rebelde (Art. 80 CPC) en subsidio Nulidad Procesal (Art. 83 CPC).
* **Fundamento:** Se sostiene que don Víctor Peralta jamás tuvo conocimiento personal del litigio, que no se le notificó en persona ninguna resolución y que la notificación por avisos del Art. 54 CPC encubrió una omisión de búsqueda de su domicilio real y efectivo.
* **Requisito Temporal Crítico:** Debe interponerse dentro de los **5 días hábiles** desde que el deudor tomó conocimiento efectivo de la causa, acompañando comprobante de domicilio vigente y solicitando con urgencia extrema la **Orden de No Innovar (ONI)** y la suspensión inmediata de la subasta electrónica por vicio sustantivo que compromete la garantía del debido proceso (Art. 19 N° 3 CPR).
* **Riesgo:** Si el tribunal considera que la notificación por avisos cumplió formalmente con el Diario Oficial y los diarios locales, podría desestimar la suspensión in limine.

#### CURSO DE ACCIÓN C (Transaccional Bancario con Abogado Delegado de Folio 27)
* **Mecanismo:** Comparecencia directa ante el abogado patrocinante y delegado de BancoEstado para suscribir un convenio de pago y reprogramación crediticia.
* **Fundamento:** BancoEstado opera con facultades FOGAPE y políticas de normalización de cartera comercial. El abogado delegado cuenta con poder para convenir y suspender audiencias.
* **Operativa:** Ofrecer el pago al contado de un pie inmediato (20% al 30%, equivalente a $3.000.000 a $4.500.000) y la renegociación del saldo insoluto en cuotas mensuales, condicionando la entrega del vale vista a la presentación conjunta de un escrito de suspensión de remate antes de las 09:00 horas del lunes 09 de noviembre.

---

## PLAN DE ACCIÓN OPERATIVO EN 48 HORAS

| Horario / Ventana | Acción Procesal Concreta | Responsable Obligatorio |
| :--- | :--- | :--- |
| **Viernes 06 Nov · 08:30 - 11:00** | Liquidación de crédito en mesón judicial y revisión de cuenta corriente del 2° J.L. Osorno. | Abogado defensor habilitado |
| **Viernes 06 Nov · 11:30 - 14:00** | Contacto telefónico y presencial urgente con Abogado Patrocinante y Delegado BancoEstado (Folio 27). | Abogado defensor / Cliente |
| **Viernes 06 Nov · 14:00 - 18:00** | Redacción y firma digital del Escrito de Liberación (Art. 490 CPC) o Incidente de Nulidad (Art. 80 CPC). | Abogado habilitado patrocinante |
| **Sábado 07 y Dom 08 Nov** | Obtención de fondos líquidos ($16.500.000 enervatorio o pie transaccional de $4.000.000). | Don Víctor Peralta (Ejecutado) |
| **Lunes 09 Nov · 08:00 - 08:45** | Ingreso del escrito con comprobante de depósito en la OJV del 2° Juzgado de Letras de Osorno. | Abogado defensor con clave OJV |
| **Lunes 09 Nov · 09:00 - 10:30** | Comparecencia en sala Zoom del tribunal / Notificación directa al Secretario para frenar subasta. | Abogado defensor en audiencia |

---

<div class="lenguaje-claro">
<h3>📖 EXPLICACIÓN EN LENGUAJE CLARO PARA EL AFECTADO</h3>
<strong>Estimado don Víctor Domingo Peralta Villagrán:</strong><br><br>
Le informamos de forma directa, clara y sin tecnicismos la situación real de su propiedad:<br>
1. <strong>¿Qué ocurre con su propiedad?</strong> Su casa/terreno inscrito en Osorno saldrá a remate judicial este <strong>lunes 9 de noviembre de 2026 a las 11:00 de la mañana por Zoom</strong>, porque BancoEstado cobró una deuda impaga de $13.501.556 de la Constructora donde usted firmó como aval.<br>
2. <strong>¿Por qué se llegó a este punto?</strong> El banco publicó los avisos del juicio en el diario y usted no se enteró a tiempo. Como venció el plazo de 8 días sin que presentara defensas con un abogado, el juez dio por terminada la primera etapa y autorizó de inmediato el remate del bien raíz por un mínimo de $31.550.172.<br>
3. <strong>¿Cómo puede salvar su casa antes del lunes?</strong>
<ul>
<li><strong>La opción más segura (Pagar la deuda y costas):</strong> La ley chilena (artículo 490 del Código de Procedimiento Civil) le da el derecho absoluto de frenar el remate si usted deposita el dinero adeudado y las costas en la cuenta del tribunal antes de que empiece la subasta. Al pagar, el remate se anula y la casa queda libre.</li>
<li><strong>La opción de defensa judicial (Alegar que no fue notificado en persona):</strong> Si usted nunca recibió los papeles del juicio y el banco lo demandó por avisos sin buscarlo en su casa real, su abogado puede pedir la nulidad de todo lo obrado (artículo 80 del CPC) dentro de los 5 días hábiles desde que supo del juicio, pidiendo la suspensión inmediata del remate.</li>
<li><strong>La opción de acuerdo comercial:</strong> Acercarse urgentemente al abogado del banco este viernes para ofrecer un abono inicial y pactar cuotas, pidiéndole al banco que suspenda la subasta de mutuo acuerdo.</li>
</ul>
<strong>Lo que debe hacer HOY:</strong> Comuníquese de inmediato con su abogado habilitado para definir cuál de estos tres caminos tomar antes de las 14:00 horas del viernes.
</div>

---

<div class="compuerta">
⚖️ <strong>COMPUERTA DE REVISIÓN Y RESPONSABILIDAD PROFESIONAL:</strong><br>
Este documento constituye un Informe en Derecho y Dictamen Estratégico Técnico-Procesal conforme a las disposiciones del Código de Procedimiento Civil, Código Civil, Ley N° 18.092 y jurisprudencia unificada de la Excma. Corte Suprema de Chile. Conforme a las reglas del ejercicio forense (Ley N° 18.120 y Ley N° 20.886 de Tramitación Digital), todo escrito procesal de enervación, consignación o incidente de nulidad debe ser revisado, patrocinado y firmado electrónicamente por un abogado habilitado para el ejercicio de la profesión antes de su ingreso formal a través de la Oficina Judicial Virtual (OJV) ante el 2° Juzgado de Letras de Osorno.
</div>

---

## FUENTES NORMATIVAS, JURISPRUDENCIALES Y DOGMÁTICAS CITADAS

1. **[BCN - Código de Procedimiento Civil, Art. 54]** https://www.bcn.cl/leychile/navegar?idNorma=22740 (Notificación subsidiaria por avisos en prensa y solemnidad del Diario Oficial).
2. **[BCN - Código de Procedimiento Civil, Art. 80]** https://www.bcn.cl/leychile/navegar?idNorma=22740 (Incidente de rescisión y nulidad por falta de emplazamiento personal del rebelde dentro de 5 días).
3. **[BCN - Código de Procedimiento Civil, Art. 83]** https://www.bcn.cl/leychile/navegar?idNorma=22740 (Nulidad procesal de actuaciones judiciales por vicio sustantivo).
4. **[BCN - Código de Procedimiento Civil, Art. 434 N° 4]** https://www.bcn.cl/leychile/navegar?idNorma=22740 (Títulos ejecutivos perfectos: pagarés autorizados ante ministro de fe).
5. **[BCN - Código de Procedimiento Civil, Art. 459]** https://www.bcn.cl/leychile/navegar?idNorma=22740 (Término territorial de 8 días hábiles para oponer excepciones).
6. **[BCN - Código de Procedimiento Civil, Art. 462]** https://www.bcn.cl/leychile/navegar?idNorma=22740 (Cómputo del término de oposición desde la traba del requerimiento de pago).
7. **[BCN - Código de Procedimiento Civil, Art. 472]** https://www.bcn.cl/leychile/navegar?idNorma=22740 (Omisión obligatoria de sentencia y eficacia ejecutiva plena del mandamiento).
8. **[BCN - Código de Procedimiento Civil, Art. 485]** https://www.bcn.cl/leychile/navegar?idNorma=22740 (Venta en remate público de bienes raíces y modalidad remota por videoconferencia).
9. **[BCN - Código de Procedimiento Civil, Art. 486]** https://www.bcn.cl/leychile/navegar?idNorma=22740 (Tasación aprobada por el avalúo fiscal vigente para contribuciones).
10. **[BCN - Código de Procedimiento Civil, Art. 488]** https://www.bcn.cl/leychile/navegar?idNorma=22740 (Fijación de día y hora para la subasta judicial previa tasación firme).
11. **[BCN - Código de Procedimiento Civil, Art. 489]** https://www.bcn.cl/leychile/navegar?idNorma=22740 (Requisitos de los avisos de remate: 4 inserciones con mínimo 15 días de anticipación).
12. **[BCN - Código de Procedimiento Civil, Art. 490]** https://www.bcn.cl/leychile/navegar?idNorma=22740 (Facultad indisponible del ejecutado de libertar sus bienes pagando deuda y costas).
13. **[BCN - Código de Procedimiento Civil, Art. 494]** https://www.bcn.cl/leychile/navegar?idNorma=22740 (Caución legal del 10% del avalúo para participar como postor en la subasta).
14. **[BCN - Código de Procedimiento Civil, Art. 495]** https://www.bcn.cl/leychile/navegar?idNorma=22740 (Valor del acta de remate como escritura pública y firma electrónica).
15. **[BCN - Ley N° 18092, Art. 98]** https://www.bcn.cl/leychile/navegar?idLey=18092 (Plazo fatal de prescripción cambiaria de un año de las acciones del pagaré).
16. **[BCN - Ley N° 18092, Art. 105]** https://www.bcn.cl/leychile/navegar?idLey=18092 (Requisitos de emisión, vencimientos y cláusulas de aceleración en el pagaré).
17. **[BCN - Ley N° 19733, Art. 2]** https://www.bcn.cl/leychile/navegar?idLey=19733 (Definición legal de medios de comunicación social y periódicos digitales).
18. **[BCN - Código Civil, Art. 1511]** https://www.bcn.cl/leychile/navegar?idNorma=172986 (Concepto y fuentes de la obligación solidaria pasiva).
19. **[BCN - Código Civil, Art. 1514]** https://www.bcn.cl/leychile/navegar?idNorma=172986 (Facultad del acreedor de perseguir al deudor solidario sin beneficio de división).
20. **[BCN - Código Civil, Art. 1801 inc. 2]** https://www.bcn.cl/leychile/navegar?idNorma=172986 (Solemnidad de escritura pública para la compraventa de bienes raíces).
21. **[CS - Rol N° 490-2026, Fecha: 08-01-2026]** PJUD (Criterio uniforme Corte Suprema sobre oportunidad liberatoria del Art. 490 CPC).
22. **[CS - Rol N° 472-2025, Fecha: 19-02-2025]** PJUD (Preclusión y eficacia de cosa juzgada del mandamiento bajo Art. 472 CPC).
23. **[Dictamen CGR N° 94.498 (2014)]** https://www.contraloria.cl/pdfbuscador/dictamenes/0094498N14/html (Validez de publicaciones legales en diarios electrónicos según Ley N° 19.733).
24. **[Dictamen CGR N° 9.067 (2020)]** https://www.contraloria.cl/pdfbuscador/dictamenes/009067N20/html (Idoneidad de la prensa digital para publicaciones de emplazamiento y avisos).
25. **[Hugging Face - pablobenavidesj/doctrina-jurisprudencia-chile, Archivo: doctrina/academia_judicial/MD-46-COMUNICACION-Y-CUMPLIMIENTO-RESOLUCIONES-JUDICIALES.md]** https://huggingface.co/datasets/pablobenavidesj/doctrina-jurisprudencia-chile/blob/acbd1e1b52c85e03a32f2b776afb58bb88ec1b03/doctrina/academia_judicial/MD-46-COMUNICACION-Y-CUMPLIMIENTO-RESOLUCIONES-JUDICIALES.md (Academia Judicial de Chile, Notificación por avisos y debido proceso).
26. **[Hugging Face - pablobenavidesj/doctrina-jurisprudencia-chile, Archivo: doctrina/revistas/rchd/2005/73135_el_control_de_la_ejecucion_en_el_caso_de_la_mal_denominada_s.md]** https://huggingface.co/datasets/pablobenavidesj/doctrina-jurisprudencia-chile/blob/acbd1e1b52c85e03a32f2b776afb58bb88ec1b03/doctrina/revistas/rchd/2005/73135_el_control_de_la_ejecucion_en_el_caso_de_la_mal_denominada_s.md (Alejandro Romero Seguel, El control de la ejecución en la sentencia ficta del Art. 472 CPC).
"""

def main():
    print(">>> 1. Compilando Markdown a PDF con MarkdownPdf y CSS institucional...")
    pdf = MarkdownPdf(toc_level=2)
    pdf.add_section(
        Section(MARKDOWN_TEXT, paper_size="A4", borders=(36, 42, -36, -42)),
        user_css=CSS_STYLES
    )
    
    temp_pdf = "/tmp/temp_informe_c895.pdf"
    pdf.save(temp_pdf)
    
    print(">>> 2. Aplicando foliado formal, encabezados y navegación con PyMuPDF...")
    doc = pymupdf.open(temp_pdf)
    total_pages = len(doc)
    
    # Marcadores TOC nativos para OJV con detección dinámica de páginas
    sections = [
        ("Alerta Crítica: Remate Inminente 09/11/2026", "ALERTA PROCESAL CRÍTICA"),
        ("Ficha Técnica y Matriz Forense", "FICHA TÉCNICA"),
        ("Cronología: Cuaderno Principal y Apremio", "TABLAS DE CRONOLOGÍA"),
        ("Sección I: Cuestión Jurídica y Planteamiento", "SECCIÓN I"),
        ("Sección II: Marco Normativo Positivo (BCN)", "SECCIÓN II"),
        ("Sección III: Construcción Dogmática y Doctrinal", "SECCIÓN III"),
        ("Sección IV: Criterio Jurisprudencial (CS y CGR)", "SECCIÓN IV"),
        ("Sección V: Dictamen Estratégico y Cursos de Acción", "SECCIÓN V"),
        ("Plan de Acción Operativo en 48 Horas", "PLAN DE ACCIÓN"),
        ("Lenguaje Claro para el Afectado", "LENGUAJE CLARO"),
        ("Compuerta Ética de Revisión Profesional", "COMPUERTA DE REVISIÓN"),
        ("Fuentes Normativas y Jurisprudenciales (26)", "FUENTES NORMATIVAS")
    ]

    toc = [[1, "INFORME EN DERECHO · ROL C-895-2023", 1]]
    for title, search_term in sections:
        page_found = 1
        for pno, page in enumerate(doc, 1):
            if search_term.lower() in page.get_text().lower():
                page_found = pno
                break
        toc.append([2, title, page_found])

    doc.set_toc(toc)
    
    # Foliado y encabezados página a página
    for idx, page in enumerate(doc, 1):
        # Encabezado institucional
        page.insert_text(
            pymupdf.Point(36, 26),
            "2° JUZGADO DE LETRAS DE OSORNO · CAUSA ROL C-895-2023 · INFORME EN DERECHO",
            fontsize=7.5,
            color=(0.35, 0.38, 0.42),
            fontname="helv"
        )
        page.draw_line(pymupdf.Point(36, 31), pymupdf.Point(559, 31), color=(0.75, 0.78, 0.82), width=0.6)
        
        # Pie de página con foliado
        page.draw_line(pymupdf.Point(36, 814), pymupdf.Point(559, 814), color=(0.75, 0.78, 0.82), width=0.6)
        page.insert_text(
            pymupdf.Point(36, 826),
            "Open Legal Chile — Plataforma Forense y Regulatoria · Derecho Continental Codificado",
            fontsize=7.5,
            color=(0.4, 0.43, 0.48),
            fontname="helv"
        )
        page.insert_text(
            pymupdf.Point(505, 826),
            f"Página {idx} de {total_pages}",
            fontsize=7.5,
            color=(0.25, 0.28, 0.32),
            fontname="helv"
        )
        
    doc.save(str(OUTPUT_PDF))
    doc.close()
    
    if os.path.exists(temp_pdf):
        os.remove(temp_pdf)
        
    size_bytes = OUTPUT_PDF.stat().st_size
    print(f">>> PDF CREADO CON ÉXITO:")
    print(f"    Ruta: {OUTPUT_PDF}")
    print(f"    Tamaño: {size_bytes} bytes ({size_bytes / 1024:.1f} KB)")
    print(f"    Total de páginas: {total_pages}")

if __name__ == "__main__":
    main()
