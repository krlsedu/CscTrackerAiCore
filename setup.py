import setuptools
from version import get_version

VERSION = get_version()

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt") as f:
    required = f.read().splitlines()

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
        # Versões do Python suportadas (Alinhar com o README que diz 3.10+)
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        # Sistema Operacional
        "Operating System :: OS Independent",
    ],
    install_requires=required,
    python_requires=">=3.10",
    include_package_data=True,
)
