import setuptools
from version import get_version

VERSION = get_version()

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as f:
    required = [
        line.strip()
        for line in f
        if line.strip() and not line.strip().startswith("#")
    ]

setuptools.setup(
    name="csctracker-ai-core",
    version=VERSION,
    license="MIT",
    author="Carlos Eduardo",
    # author_email="teu.email@exemplo.com", # Se quiser colocar contato
    description="A robust library to integrate Google Gemini AI with API key rotation and ClickHouse telemetry.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/krlsedu/CscTrackerAiCore",
    project_urls={
        "Bug Tracker": "https://github.com/krlsedu/CscTrackerAiCore/issues",
        "Source Code": "https://github.com/krlsedu/CscTrackerAiCore",
    },
    packages=setuptools.find_packages(exclude=["tests", "tests.*"]),
    # Palavras-chave ricas para busca
    keywords=[
        "ai",
        "artificial intelligence",
        "google-gemini",
        "gemini-pro",
        "llm",
        "generative-ai",
        "api-key-rotation",
        "clickhouse",
        "observability",
        "telemetry",
        "finance",
        "llmops",
    ],
    # Classificadores oficiais do PyPI
    classifiers=[
        # Status do projeto
        "Development Status :: 4 - Beta",  # 3 - Alpha, 4 - Beta, 5 - Production/Stable
        # Público alvo
        "Intended Audience :: Developers",
        "Intended Audience :: Financial and Insurance Industry",
        "Intended Audience :: Science/Research",
        # Tecnologias e Tópicos
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: System :: Logging",
        # Licença
        "License :: OSI Approved :: MIT License",
        # Versões do Python suportadas (Python 3.11+ até 3.15)
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
        "Programming Language :: Python :: 3.15",
        # Sistema Operacional
        "Operating System :: OS Independent",
    ],
    install_requires=required,
    python_requires=">=3.11",
    include_package_data=True,
)
