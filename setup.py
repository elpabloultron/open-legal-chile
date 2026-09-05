from setuptools import setup, find_packages

setup(
    name="openlegal-chile",
    version="1.0.0",
    description="Suite de Inteligencia Jurídica y Servidor MCP para el Derecho Continental de Chile",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="Pablo Benavides Jorquera / Open Legal Chile Contributors",
    url="https://github.com/elpabloultron/open-legal-chile",
    py_modules=[
        "openlegal",
        "mcp_server",
        "chat_engine",
        "critique",
        "exporters",
        "config",
        "bcn_connector",
        "cgr_connector",
        "dt_connector",
        "pjud_connector",
        "cne_connector",
        "panel_expertos_connector",
        "cmf_connector",
        "sii_connector",
        "ambiental_connector",
        "tdlc_connector",
        "forensic_ocr",
        "pdf_dossier_compiler",
        "notebooklm_connector",
        "infoprobidad_connector",
        "grafo_vinculos",
        "doctrina_connector",
        "examen_grado",
        "docket_watcher",
        "clinica_juridica",
        "cold_start",
        "privacidad_inapi"
    ],
    install_requires=[
        "requests>=2.28.0",
        "beautifulsoup4>=4.11.0",
        "defusedxml>=0.7.1",
        "pymupdf>=1.23.0"
    ],
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "": [".env.example", "mcp_config.json", "smithery.yaml"]
    },
    entry_points={
        "console_scripts": [
            "openlegal=openlegal:main",
            "openlegal-mcp=mcp_server:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Intended Audience :: Legal Industry",
    ],
    python_requires=">=3.10",
)
