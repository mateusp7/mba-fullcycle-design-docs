#!/usr/bin/env python3
"""Validate ADRs produced for the webhook architecture challenge.

The validator is intentionally dependency-free and checks observable invariants:
file names, required sections, alternatives, consequences, decision coverage,
traceability, and references to existing repository files.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


ADR_NAME = re.compile(r"^ADR-(\d{3})-([a-z0-9]+(?:-[a-z0-9]+)*)\.md$")
TIMESTAMP = re.compile(r"\[\d{2}:\d{2}\]\s+[^\]\n:]+")
CODE_PATH = re.compile(
    r"(?<![\w.-])((?:src|prisma|tests)/[A-Za-z0-9_./-]+\.[A-Za-z0-9]+)"
    r"(?::\d+(?:-\d+)?)?"
)

REQUIRED_SECTIONS = [
    "Status",
    "Contexto",
    "Decisão",
    "Alternativas consideradas",
    "Consequências positivas",
    "Consequências negativas e trade-offs",
    "Rastreabilidade",
]

DECISIONS = {
    "outbox transacional no MySQL": ["outbox", "mysql"],
    "retry com backoff e DLQ": ["retry", "backoff", ("dlq", "dead-letter")],
    "HMAC-SHA256 com secret por endpoint": ["hmac-sha256", "secret", "endpoint"],
    "at-least-once com X-Event-Id": ["at-least-once", "x-event-id"],
    "worker separado em polling": ["worker", "polling", ("processo separado", "separado da api")],
    "reuso dos padrões existentes": ["apperror", "pino", ("schemas zod", "zod"), "src/modules"],
}


def section_body(text: str, heading: str) -> str:
    pattern = re.compile(
        rf"^##\s+{re.escape(heading)}\s*$([\s\S]*?)(?=^##\s+|\Z)",
        re.IGNORECASE | re.MULTILINE,
    )
    match = pattern.search(text)
    return match.group(1).strip() if match else ""


def contains_terms(text: str, terms: list[str | tuple[str, ...]]) -> bool:
    lowered = text.lower()
    for term in terms:
        if isinstance(term, tuple):
            if not any(option in lowered for option in term):
                return False
        elif term.lower() not in lowered:
            return False
    return True


def likely_proposed(line: str) -> bool:
    lowered = line.lower()
    return any(
        marker in lowered
        for marker in (
            "proposto",
            "proposta",
            "inexistente",
            "não existe",
            "nao existe",
            "ainda não",
            "ainda nao",
            "artefato novo",
        )
    )


def validate_file(path: Path, repo_root: Path) -> list[str]:
    errors: list[str] = []
    text = path.read_text(encoding="utf-8")

    for section in REQUIRED_SECTIONS:
        if not section_body(text, section):
            errors.append(f"seção obrigatória ausente ou vazia: {section}")

    alternatives = section_body(text, "Alternativas consideradas")
    if alternatives and not re.search(r"^\s*[-*]\s+|^\s*\d+[.)]\s+|\|", alternatives, re.MULTILINE):
        errors.append("Alternativas consideradas não contém pelo menos uma alternativa listada")
    if alternatives and not re.search(r"plausível|discutida na reunião|discutida", alternatives, re.IGNORECASE):
        errors.append("alternativas não estão classificadas como discutidas ou plausíveis")
    if alternatives and not re.search(r"trade[- ]?off|descarte|custo|limitação|menos adequada", alternatives, re.IGNORECASE):
        errors.append("Alternativas consideradas não explicita o trade-off ou motivo do descarte")

    traceability = section_body(text, "Rastreabilidade")
    if traceability and not TIMESTAMP.search(traceability):
        errors.append("Rastreabilidade não contém fonte de transcrição no formato [hh:mm] Nome")
    if traceability and not any(
        (match := CODE_PATH.search(line))
        and (repo_root / Path(match.group(1))).is_file()
        for line in traceability.splitlines()
    ):
        errors.append("Rastreabilidade não referencia arquivo de código existente")

    # Validate source paths cited as code. A missing path is acceptable only when
    # the same line explicitly says that the artifact is proposed/nonexistent.
    for line_number, line in enumerate(text.splitlines(), start=1):
        for match in CODE_PATH.finditer(line):
            relative = Path(match.group(1))
            if not (repo_root / relative).is_file() and not likely_proposed(line):
                errors.append(
                    f"caminho de código inexistente na linha {line_number}: {relative.as_posix()}"
                )

    if not any(CODE_PATH.search(line) and (repo_root / Path(CODE_PATH.search(line).group(1))).is_file()
               for line in text.splitlines()):
        errors.append("ADR não referencia arquivo de código existente")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("package", "single"), default="package")
    parser.add_argument("--file", type=Path, help="ADR a validar no modo single")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="raiz do repositório")
    args = parser.parse_args()

    repo_root = args.root.resolve()
    adr_dir = repo_root / "docs" / "adrs"
    errors: list[str] = []

    if args.mode == "single":
        if not args.file:
            errors.append("--file é obrigatório no modo single")
            files: list[Path] = []
        else:
            candidate = args.file if args.file.is_absolute() else repo_root / args.file
            files = [candidate.resolve()]
            if not files[0].is_file():
                errors.append(f"arquivo não encontrado: {files[0]}")
    else:
        if not adr_dir.is_dir():
            errors.append(f"diretório não encontrado: {adr_dir}")
            files = []
        else:
            all_markdown = sorted(adr_dir.glob("*.md"))
            files = []
            for path in all_markdown:
                if path.name == "README.md":
                    continue
                if not ADR_NAME.match(path.name):
                    errors.append(f"nome de ADR inválido: {path.name}")
                else:
                    files.append(path)
            if not 5 <= len(files) <= 8:
                errors.append(f"quantidade de ADRs fora do intervalo 5-8: {len(files)}")

    for path in files:
        match = ADR_NAME.match(path.name)
        if not match:
            errors.append(f"nome de ADR inválido: {path.name}")
            continue
        errors.extend(f"{path.name}: {error}" for error in validate_file(path, repo_root))

    if args.mode == "package" and files:
        covered = [
            name
            for name, terms in DECISIONS.items()
            if any(
                contains_terms(path.read_text(encoding="utf-8"), terms)
                for path in files
            )
        ]
        if len(covered) < 5:
            errors.append(
                "cobertura insuficiente das decisões-base: "
                f"{len(covered)}/6 ({', '.join(covered) or 'nenhuma'})"
            )

    if errors:
        print("FALHOU")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"OK: {len(files)} ADR(s) validado(s)")
    if args.mode == "package":
        print("OK: pacote entre 5 e 8, seções, alternativas, trade-offs, cobertura e caminhos verificados")
    return 0


if __name__ == "__main__":
    sys.exit(main())
