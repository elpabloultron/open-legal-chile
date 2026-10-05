import re
from pathlib import Path

p = Path("investigacion_academica/articulo_cientifico_open_legal_chile.md")
content = p.read_text(encoding="utf-8")

# Realizamos pequeños reemplazos para reducir 150-200 palabras
subs = [
    ("como el sistema operativo Linux, la base de datos PostgreSQL o los servidores web Apache y Nginx", "como Linux o PostgreSQL"),
    ("las universidades públicas regionales y sus comunidades académicas poseen una insustituible vocación social para idear soluciones tecnológicas diseñadas no para engrosar el margen de utilidad comercial de consultoras cerradas, sino para resolver los problemas reales de los ciudadanos en los territorios más vulnerables y desprovistos de asistencia letrada.", "las universidades públicas regionales poseen una vocación social clave para idear soluciones orientadas a los ciudadanos y sectores vulnerables."),
    ("Toda minuta, escrito o dashboard producido por la plataforma incorpora obligatoriamente en su cuerpo la compuerta de validación deontológica:", "Todo producto de la plataforma incorpora obligatoriamente la compuerta de validación deontológica:"),
    ("En el aula universitaria y el estudio dogmático: La exigencia cotidiana de desentrañar textos legales extensos, concordar artículos dispersos en los códigos sustantivos y procesales, y comprender instituciones abstractas de la dogmática jurídica (teoría del negocio jurídico, estatuto de las obligaciones, regímenes posesorios, derechos reales y garantías constitucionales) revela la absoluta insuficiencia de las herramientas digitales convencionales, las cuales se limitaban a motores de búsqueda por texto plano desprovistos de comprensión deóntica.", "En el aula universitaria: La exigencia de concordar normas dispersas y comprender instituciones abstractas evidencia la insuficiencia de motores de búsqueda por texto plano desprovistos de lógica deóntica."),
    ("Durante la práctica obligatoria en los consultorios jurídicos de asistencia judicial gratuita que defienden a personas de escasos recursos y sectores socialmente vulnerables, la saturación laboral del postulante es abrumadora: tramitación simultánea de decenas de causas de familia (alimentos, cuidado personal, relación directa y regular), causas laborales (despidos, cobro de prestaciones) y causas civiles de precario o cobranza. En dicho contexto, el postulante carece de asistentes letrados y debe redactar demandas, computar plazos fatales a contrarreloj y traducir complejos proveídos judiciales a un Lenguaje Claro que un ciudadano en situación de vulnerabilidad pueda comprender sin angustia.", "En la práctica judicial (CAJ): La sobrecarga en la tramitación de causas de familia, laborales y civiles obliga a redactar demandas y computar plazos fatales a contrarreloj, traduciendo proveídos a Lenguaje Claro para usuarios vulnerables."),
    ("En la transición hacia el ejercicio profesional autónomo en tribunales, el abogado novel se enfrenta a la asimetría impuesta por los grandes estudios de la capital, careciendo de infraestructura tecnológica propia y quedando expuesto al riesgo de preclusión procesal por errores en el cómputo de términos legales.", "En el ejercicio profesional: El abogado litigante novel enfrenta asimetrías tecnológicas frente a grandes estudios corporativos, arriesgando preclusiones por yerros en plazos fatales.")
]

for s, r in subs:
    if s in content:
        content = content.replace(s, r)
        print(f"Reemplazado: {s[:40]}...")
    else:
        print(f"NO encontrado: {s[:40]}...")

p.write_text(content, encoding="utf-8")
words = len(re.findall(r'\b\w+\b', content))
chars = len(content)
print(f"Total palabras: {words}")
print(f"Total caracteres: {chars}")
