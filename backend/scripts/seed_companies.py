"""Seed script to populate initial company list."""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Load .env from backend/ directory
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

COMPANIES = [
    # Pure-play public quantum
    {
        "name": "IonQ",
        "slug": "ionq",
        "ticker": "IONQ",
        "sector": "pure_play",
        "is_etf": False,
        "description": "Trapped-ion quantum computing company.",
    },
    {
        "name": "D-Wave Quantum",
        "slug": "d-wave-quantum",
        "ticker": "QBTS",
        "sector": "pure_play",
        "is_etf": False,
        "description": "Quantum annealing and gate-model quantum computing.",
    },
    {
        "name": "Rigetti Computing",
        "slug": "rigetti-computing",
        "ticker": "RGTI",
        "sector": "pure_play",
        "is_etf": False,
        "description": "Superconducting quantum computing company.",
    },
    {
        "name": "Quantum Computing Inc",
        "slug": "quantum-computing-inc",
        "ticker": "QUBT",
        "sector": "pure_play",
        "is_etf": False,
        "description": "Quantum photonic and nanophotonic computing.",
    },
    {
        "name": "Arqit Quantum",
        "slug": "arqit-quantum",
        "ticker": "ARQQ",
        "sector": "pure_play",
        "is_etf": False,
        "description": "Quantum encryption and cybersecurity.",
    },
    {
        "name": "Infleqtion",
        "slug": "infleqtion",
        "ticker": "INFQ",
        "sector": "pure_play",
        "is_etf": False,
        "description": "Neutral-atom quantum computing and quantum sensors.",
    },
    {
        "name": "SEALSQ",
        "slug": "sealsq",
        "ticker": "LAES",
        "sector": "pure_play",
        "is_etf": False,
        "description": "Post-quantum cryptography semiconductors and secure hardware.",
    },
    {
        "name": "BTQ Technologies",
        "slug": "btq-technologies",
        "ticker": "BTQ",
        "sector": "pure_play",
        "is_etf": False,
        "description": "Post-quantum blockchain security and cryptography.",
    },
    # Big tech with quantum divisions
    {
        "name": "IBM",
        "slug": "ibm",
        "ticker": "IBM",
        "sector": "big_tech",
        "is_etf": False,
        "description": "IBM Quantum — superconducting qubit quantum computing.",
    },
    {
        "name": "Alphabet (Google)",
        "slug": "alphabet-google",
        "ticker": "GOOGL",
        "sector": "big_tech",
        "is_etf": False,
        "description": "Google Quantum AI — superconducting qubit research.",
    },
    {
        "name": "Microsoft",
        "slug": "microsoft",
        "ticker": "MSFT",
        "sector": "big_tech",
        "is_etf": False,
        "description": "Azure Quantum — topological qubit research and quantum cloud.",
    },
    {
        "name": "Amazon (AWS)",
        "slug": "amazon-aws",
        "ticker": "AMZN",
        "sector": "big_tech",
        "is_etf": False,
        "description": "AWS Braket — quantum computing cloud service.",
    },
    {
        "name": "Intel",
        "slug": "intel",
        "ticker": "INTC",
        "sector": "big_tech",
        "is_etf": False,
        "description": "Intel Quantum — silicon spin qubit research.",
    },
    {
        "name": "Honeywell (Quantinuum)",
        "slug": "honeywell-quantinuum",
        "ticker": "HON",
        "sector": "big_tech",
        "is_etf": False,
        "description": (
            "Quantinuum — trapped-ion quantum computing"
            " (Honeywell subsidiary)."
        ),
    },
    {
        "name": "NVIDIA",
        "slug": "nvidia",
        "ticker": "NVDA",
        "sector": "big_tech",
        "is_etf": False,
        "description": (
            "CUDA-Q quantum platform and NVQLink"
            " quantum-classical interconnect."
        ),
    },
    {
        "name": "Fujitsu",
        "slug": "fujitsu",
        "ticker": "6702.T",
        "sector": "big_tech",
        "is_etf": False,
        "description": (
            "Superconducting quantum computing"
            " with RIKEN (256-qubit systems)."
        ),
    },
    # ETFs
    {
        "name": "Defiance Quantum ETF",
        "slug": "defiance-quantum-etf",
        "ticker": "QTUM",
        "sector": "etf",
        "is_etf": True,
        "description": "ETF tracking quantum computing and machine learning companies.",
    },
    {
        "name": "WisdomTree Quantum Computing Fund",
        "slug": "wisdomtree-quantum-etf",
        "ticker": "WQTM",
        "sector": "etf",
        "is_etf": True,
        "description": "ETF focused on pure quantum computing ecosystem companies.",
    },
]


def seed(database_url: str | None = None) -> None:
    """Insert seed companies into the database."""
    url = database_url or os.environ.get(
        "CHARTORA_DATABASE_URL",
        "postgresql://chartora:chartora@localhost:5432/chartora",
    )
    # Strip async driver — this script uses synchronous SQLAlchemy
    url = url.replace("postgresql+asyncpg://", "postgresql://")
    engine = create_engine(url)

    with engine.begin() as conn:
        for company in COMPANIES:
            conn.execute(
                text(
                    """
                    INSERT INTO companies
                        (name, slug, ticker, sector, is_etf, description)
                    VALUES (:name, :slug, :ticker, :sector, :is_etf, :description)
                    ON CONFLICT (slug) DO NOTHING
                    """
                ),
                company,
            )
    print(f"Seeded {len(COMPANIES)} companies.")


if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else None
    seed(url)
