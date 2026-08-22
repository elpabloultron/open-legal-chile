from setuptools import setup, find_packages

setup(
    name="openlegal-chile",
    version="1.0.0",
    description="Suite de Inteligencia Jurídica y Conectores de Datos para el Derecho Chileno",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="Open Legal Chile Team",
    author_email="contacto@openlegal.cl",
    url="https://github.com/open-legal-chile/open-legal-chile",
    py_modules=[
        "openlegal",
        "config",
        "server",
        "bcn_connector",
        "cgr_connector",
        "dt_connector",
        "cne_connector",
        "panel_expertos_connector",
        "cmf_connector",
        "sii_connector",
        "ambiental_connector",
        "tdlc_connector"
    ],
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "": ["web/*", "web/**/*", ".env.example"]
    },
    entry_points={
        "console_scripts": [
            "openlegal=openlegal:main",
            "openlegal-web=server:run_server",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "Topic :: Scientific/Engineering :: Information Analysis",
    ],
    python_requires=">=3.8",
)
