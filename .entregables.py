"""Verificaciones objetivas de los entregables (documentos, Git, estructura del código).

Funciones puras sobre el repositorio del equipo: no usan Docker, red ni librerías externas.
Las usa el calificador oficial y también `./validator entregables` de cada kit, que trae una
copia idéntica de este archivo (`kits/<nivel>/.entregables.py`, ver tools/sync_kits.py).

Cada verificación devuelve (fracción entre 0 y 1, detalle legible para el jurado).
"""

import ast
import os
import re
import subprocess
import unicodedata
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

Result = Tuple[float, str]

BOGOTA = timezone(timedelta(hours=-5))
SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", "target", "build", "dist", "vendor", ".gradle", ".idea", ".mvn", "test-results"}
CODE_SUFFIXES = {".py", ".js", ".mjs", ".cjs", ".ts", ".java", ".kt", ".go", ".cs", ".php", ".rb", ".rs", ".sql", ".yaml", ".yml", ".json", ".properties", ".toml", ".ini", ".env", ".xml", ".sh"}
GENERIC_MESSAGES = {"update", "updates", "fix", "fixes", "wip", "cambios", "cambio", "commit", "changes", "test", "prueba", "ok", "listo", "avance", "avances", "save", "guardar", "initial commit", "first commit"}
MAX_TEXT_BYTES = 1024 * 1024
MAX_REPORT_BYTES = 5 * 1024 * 1024
OTHER_DOC_SUFFIXES = (".docx", ".doc", ".pdf", ".odt", ".rtf", ".pages", ".txt", ".html")
EVIDENCE_SUFFIXES = {".txt", ".log", ".md", ".csv", ".json", ".pdf", ".png", ".jpg", ".jpeg"}
EMPTY_ANSWERS = {"", "-", "n/a", "na", "no aplica", "nada", "ninguno", "ninguna", "pendiente", "por definir", "tbd", "todo"}


# --------------------------------------------------------------------------- utilidades


def norm(text: str) -> str:
    """Minúsculas sin tildes ni espacios repetidos: 'Síntoma ' -> 'sintoma'."""
    value = unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", value).strip().lower()


def find_file(repo: Path, relative: str) -> Optional[Path]:
    """Busca el archivo con el nombre exacto y, si no está, sin distinguir mayúsculas."""
    target = Path(repo) / relative
    if target.is_file():
        return target
    parent = target.parent
    if parent.is_dir():
        for item in parent.iterdir():
            if item.is_file() and item.name.lower() == target.name.lower():
                return item
    return None


def small_text(path: Path, limit: int = MAX_TEXT_BYTES) -> Optional[str]:
    """Texto de un archivo; None si pesa más del límite (no se procesan archivos enormes)."""
    if path.stat().st_size > limit:
        return None
    return path.read_text(encoding="utf-8", errors="replace")


def read_text(repo: Path, relative: str) -> Optional[str]:
    """Contenido del archivo sin comentarios HTML (las instrucciones de las plantillas no cuentan)."""
    path = find_file(repo, relative)
    text = small_text(path) if path else None
    return strip_comments(text) if text is not None else None


def not_found(repo: Path, relative: str) -> str:
    """Por qué no se pudo revisar un documento: no existe, está en otro formato o es demasiado grande."""
    path = find_file(repo, relative)
    if path is not None:
        return "{0} pesa más de {1} MB: no se revisa".format(relative, MAX_TEXT_BYTES // (1024 * 1024))
    stem = relative.rsplit(".", 1)[0]
    others = [stem + suffix for suffix in OTHER_DOC_SUFFIXES if find_file(repo, stem + suffix) and stem + suffix != relative]
    message = "No existe " + relative
    if others:
        message += " (se encontró {0}: solo se acepta el formato indicado, {1})".format(", ".join(others), relative)
    return message


def strip_comments(text: str) -> str:
    return re.sub(r"<!--.*?-->", " ", text, flags=re.S)


def words(text: str) -> int:
    return len(re.findall(r"[\w./`-]+", text or ""))


def sections(text: str, depth: int = 2) -> List[Tuple[str, str]]:
    """Divide un Markdown por encabezados de nivel `depth` (## por defecto)."""
    pattern = re.compile(r"^#{%d}(?!#)\s*(.+?)\s*#*\s*$" % depth, re.M)
    matches = list(pattern.finditer(text or ""))
    result = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        result.append((match.group(1), text[match.end():end]))
    return result


def headings(text: str) -> List[str]:
    return [norm(m.group(1)) for m in re.finditer(r"^#{1,6}\s*(.+?)\s*#*\s*$", text or "", re.M)]


def section_body(text: str, title_key: str) -> Optional[str]:
    """Texto bajo el primer encabezado (de cualquier nivel) que contenga `title_key`."""
    matches = list(re.finditer(r"^(#{1,6})\s*(.+?)\s*#*\s*$", text or "", re.M))
    for index, match in enumerate(matches):
        if title_key in norm(match.group(2)):
            level = len(match.group(1))
            end = len(text)
            for following in matches[index + 1:]:
                if len(following.group(1)) <= level:
                    end = following.start()
                    break
            return text[match.end():end]
    return None


def list_items(text: str) -> int:
    return len(re.findall(r"^\s*(?:[-*+]|\d+[.)])\s+\S", text or "", re.M))


def _label_of(raw: str, keys: Sequence[str]) -> Optional[str]:
    """La etiqueta de una línea 'Etiqueta: valor' (admite viñeta, negrita y aclaraciones cortas)."""
    position = raw.find(":")
    if position == -1:
        return None
    prefix = re.sub(r"[*_]{1,2}", "", raw[:position]).strip()
    prefix = norm(re.sub(r"^[-+>]\s*", "", prefix))
    for key in keys:
        if prefix.startswith(key) and len(prefix) <= len(key) + 15:
            return key
    return None


def labeled_fields(body: str, labels: Sequence[str]) -> Dict[str, str]:
    """Valores de campos 'Etiqueta: valor' (con o sin viñeta o negrita), incluidas líneas siguientes."""
    keys = [norm(label) for label in labels]
    values = {}  # type: Dict[str, List[str]]
    current = None
    in_fence = False
    for raw in (body or "").splitlines():
        if raw.strip().startswith("```"):
            in_fence = not in_fence
            if current:
                values[current].append(raw)
            continue
        if not in_fence:
            hit = _label_of(raw, keys)
            if hit:
                current = hit
                values.setdefault(current, []).append(raw.split(":", 1)[1].lstrip("*_ "))
                continue
            if re.match(r"^#{1,6}\s", raw):
                current = None
                continue
        if current:
            values[current].append(raw)
    return {key: "\n".join(lines).strip() for key, lines in values.items()}


def markdown_tables(text: str) -> List[Tuple[List[str], List[List[str]]]]:
    """Tablas Markdown como (encabezado normalizado, filas con celdas sin formato)."""
    tables = []
    lines = (text or "").splitlines()
    index = 0
    while index < len(lines) - 1:
        if lines[index].strip().startswith("|") and re.match(r"^\s*\|?\s*:?-{2,}", lines[index + 1]):
            header = [norm(c) for c in _cells(lines[index])]
            rows = []
            index += 2
            while index < len(lines) and lines[index].strip().startswith("|"):
                rows.append([c.strip().strip("`").strip() for c in _cells(lines[index])])
                index += 1
            tables.append((header, rows))
        else:
            index += 1
    return tables


def _cells(line: str) -> List[str]:
    stripped = line.strip()
    if stripped.startswith("|"):
        stripped = stripped[1:]
    if stripped.endswith("|"):
        stripped = stripped[:-1]
    return [c.strip() for c in stripped.split("|")]


def find_table(text: str, required: Sequence[str]) -> Optional[Tuple[Dict[str, int], List[List[str]]]]:
    """Primera tabla cuyo encabezado contiene todas las columnas pedidas (por palabra clave)."""
    for header, rows in markdown_tables(text):
        columns = {}
        for key in required:
            for position, name in enumerate(header):
                if key in name:
                    columns[key] = position
                    break
        if len(columns) == len(required):
            return columns, rows
    return None


def cell(row: List[str], columns: Dict[str, int], key: str) -> str:
    position = columns[key]
    return row[position] if position < len(row) else ""


def meaningful(value: str, minimum_words: int = 3) -> bool:
    return norm(value).strip(" .") not in EMPTY_ANSWERS and words(value) >= minimum_words


def iter_files(base: Path, suffixes: Optional[Set[str]] = None) -> Iterable[Path]:
    if not base.is_dir():
        return
    for root, dirs, files in os.walk(str(base)):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in files:
            path = Path(root) / name
            if (suffixes is None or path.suffix.lower() in suffixes) and path.stat().st_size <= MAX_TEXT_BYTES:
                yield path


def is_test_path(relative: Path) -> bool:
    parts = [p.lower() for p in relative.parts]
    if any(p in ("test", "tests", "__tests__", "spec", "specs") for p in parts[:-1]):
        return True
    name = parts[-1]
    return name.startswith("test_") or bool(re.search(r"([._-]test|[._-]spec|tests?)\.[a-z]+$", name))


def ratio(found: float, needed: float) -> float:
    return max(0.0, min(1.0, found / float(needed))) if needed else 1.0


# --------------------------------------------------------------------------- comunes


AI_LABELS = ["Herramienta", "Para qué se usó", "Prompt principal", "Qué produjo", "Qué modificó o corrigió el equipo"]


def ai_usage(repo: Path, minimum: int = 3) -> Result:
    """AI_USAGE.md: al menos `minimum` usos con los cinco campos llenos y la corrección del equipo explicada."""
    text = read_text(repo, "AI_USAGE.md")
    if text is None:
        return 0.0, not_found(repo, "AI_USAGE.md")
    entries = [(title, body) for title, body in sections(text) if norm(title).startswith("uso")]
    complete, problems = 0, []
    for title, body in entries:
        fields = labeled_fields(body, AI_LABELS)
        missing = [label for label in AI_LABELS if not meaningful(fields.get(norm(label), ""), 1 if label == "Herramienta" else 2)]
        correction = fields.get(norm(AI_LABELS[-1]), "")
        if not missing and words(correction) < 8:
            missing.append("corrección del equipo con al menos 8 palabras")
        if missing:
            problems.append("{0}: falta {1}".format(title.strip(), ", ".join(missing)))
        else:
            complete += 1
    detail = "{0} usos completos de {1} exigidos ({2} secciones '## Uso N')".format(complete, minimum, len(entries))
    if problems:
        detail += ". " + "; ".join(problems[:4])
    return ratio(complete, minimum), detail


def parse_time(value) -> Optional[datetime]:
    if value in (None, ""):
        return None
    parsed = value if isinstance(value, datetime) else datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=BOGOTA)


def git_commits(repo: Path) -> Optional[List[Dict[str, str]]]:
    if not (Path(repo) / ".git").exists():
        return None
    proc = subprocess.run(
        ["git", "log", "--no-merges", "--format=%H%x1f%an%x1f%ae%x1f%cI%x1f%s"],
        cwd=str(repo), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True,
    )
    if proc.returncode != 0:
        return None
    commits = []
    for line in proc.stdout.splitlines():
        parts = line.split("\x1f")
        if len(parts) == 5:
            commits.append({"sha": parts[0], "author": parts[1], "email": parts[2].lower(), "date": parts[3], "message": parts[4]})
    return commits


def git_history(repo: Path, start=None, deadline=None, minimum_commits: int = 10, per_author: int = 3) -> Result:
    """Commits del evento: cantidad, aporte de los dos integrantes y mensajes descriptivos."""
    commits = git_commits(repo)
    if commits is None:
        return 0.0, "El repositorio no tiene historial Git"
    begin, end = parse_time(start), parse_time(deadline)
    window = [c for c in commits if (begin is None or parse_time(c["date"]) >= begin) and (end is None or parse_time(c["date"]) <= end)]
    by_author = {}  # type: Dict[str, int]
    for commit in window:
        by_author[commit["email"]] = by_author.get(commit["email"], 0) + 1
    contributors = sum(1 for count in by_author.values() if count >= per_author)
    descriptive = sum(1 for c in window if words(c["message"]) >= 3 and norm(c["message"]).strip(" .") not in GENERIC_MESSAGES)
    share = descriptive / float(len(window)) if window else 0.0
    parts = [ratio(len(window), minimum_commits), ratio(contributors, 2), ratio(share, 0.8)]
    detail = "{0} commits en la ventana del evento (mínimo {1}); {2} integrantes con ≥ {3} commits (se esperan 2); {4:.0%} de mensajes descriptivos (mínimo 80 %)".format(
        len(window), minimum_commits, contributors, per_author, share)
    return sum(parts) / 3.0, detail


SECTION_MIN_WORDS = 20
ADR_MIN_WORDS = 10


def filled_section(text: str, key: str, minimum_words: int) -> bool:
    """Hay un encabezado de nivel 2 o más que empieza por `key` con al menos `minimum_words` palabras debajo."""
    matches = list(re.finditer(r"^(#{1,6})\s*(.+?)\s*#*\s*$", text or "", re.M))
    for index, match in enumerate(matches):
        title = re.sub(r"^[\d.)\s-]+", "", norm(match.group(2)))
        if len(match.group(1)) < 2 or not title.startswith(key):
            continue
        end = len(text)
        for following in matches[index + 1:]:
            if len(following.group(1)) <= len(match.group(1)):
                end = following.start()
                break
        if words(strip_comments(text[match.end():end])) >= minimum_words:
            return True
    return False


def architecture_doc(repo: Path, required: Sequence[str]) -> Result:
    """docs/architecture.md con las secciones exigidas (≥ 20 palabras cada una) y al menos dos alternativas descartadas."""
    text = read_text(repo, "docs/architecture.md")
    if text is None:
        return 0.0, not_found(repo, "docs/architecture.md")
    found = [key for key in required if filled_section(text, key, SECTION_MIN_WORDS)]
    alternatives = section_body(text, "alternativas descartadas")
    alt_count = list_items(alternatives or "")
    fraction = 0.8 * ratio(len(found), len(required)) + 0.2 * float(alt_count >= 2)
    missing = [key for key in required if key not in found]
    detail = "{0}/{1} secciones con al menos {2} palabras; {3} alternativas descartadas listadas (mínimo 2)".format(
        len(found), len(required), SECTION_MIN_WORDS, alt_count)
    if missing:
        detail += "; faltan o están cortas: " + ", ".join(missing)
    return fraction, detail


def openapi_paths(repo: Path, required: Sequence[str]) -> Result:
    """openapi.yaml (o .yml/.json) versión 3 con todas las rutas del contrato."""
    text = None
    for name in ("openapi.yaml", "openapi.yml", "openapi.json"):
        text = read_text(repo, name)
        if text is not None:
            break
    if text is None:
        return 0.0, not_found(repo, "openapi.yaml")
    version_ok = bool(re.search(r"""["']?openapi["']?\s*:\s*["']?3\.""", text))
    missing = []
    for path in required:
        pattern = re.escape(path).replace(r"\{x\}", r"\{[^}/]+\}")
        if not re.search(r"""(^|[\s"'])""" + pattern + r"""["']?\s*:""", text, re.M):
            missing.append(path)
    fraction = 0.1 * version_ok + 0.9 * ratio(len(required) - len(missing), len(required))
    detail = "OpenAPI 3: {0}; {1}/{2} rutas del contrato".format("sí" if version_ok else "no", len(required) - len(missing), len(required))
    if missing:
        detail += "; faltan: " + ", ".join(missing)
    return fraction, detail


# --------------------------------------------------------------------------- pruebas del equipo (JUnit)


def junit_summary(repo: Path) -> Optional[Dict[str, object]]:
    """Resultados de las pruebas del equipo en test-results/**/*.xml (formato JUnit)."""
    folder = Path(repo) / "test-results"
    files = sorted(folder.rglob("*.xml")) if folder.is_dir() else []
    if not files:
        return None
    total = passed = failed = skipped = 0
    names = set()  # type: Set[str]
    for path in files:
        try:
            if path.stat().st_size > MAX_REPORT_BYTES:
                continue
            root = ET.parse(str(path)).getroot()
        except ET.ParseError:
            continue
        for case in root.iter("testcase"):
            total += 1
            tags = {child.tag for child in case}
            if tags & {"failure", "error"}:
                failed += 1
            elif "skipped" in tags:
                skipped += 1
            else:
                passed += 1
                name = case.get("name", "")
                classname = case.get("classname", "")
                names.update({norm(name), norm(classname + "." + name), norm(classname + "::" + name)})
    return {"total": total, "passed": passed, "failed": failed, "skipped": skipped, "passed_names": names, "files": len(files)}


def suite_score(summary: Optional[Dict[str, object]], exit_code: Optional[int], minimum: int) -> Result:
    if summary is None:
        return 0.0, "No se encontraron resultados JUnit en test-results/ (código de salida {0})".format(exit_code)
    passed, failed = int(summary["passed"]), int(summary["failed"])
    fraction = ratio(passed, minimum) * (1.0 if failed == 0 and exit_code in (0, None) else 0.5)
    detail = "{0} pruebas aprobadas, {1} fallidas, {2} omitidas (mínimo {3} aprobadas y 0 fallidas); código de salida {4}".format(
        passed, failed, summary["skipped"], minimum, exit_code)
    return fraction, detail


def passed_test(summary: Optional[Dict[str, object]], reference: str) -> bool:
    if not summary or not reference.strip():
        return False
    wanted = norm(reference.strip().strip("`"))
    names = summary["passed_names"]
    return wanted in names or any(name.endswith("." + wanted) or name.endswith("::" + wanted) for name in names)


# --------------------------------------------------------------------------- Técnico


INCIDENT_LABELS = ["Síntoma", "Diagnóstico", "Comandos", "Solución", "Evidencia"]
TERMINAL_TOOLS = ["docker", "psql", "grep", "awk", "sed", "sort", "uniq", "wc", "find", "chmod"]


def incidents(text: str) -> Dict[int, Dict[str, str]]:
    found = {}
    for title, body in sections(text):
        match = re.search(r"incidente\s*(\d+)", norm(title))
        if match:
            found[int(match.group(1))] = labeled_fields(body, INCIDENT_LABELS)
    return found


def incident_report(repo: Path, total: int = 10) -> Result:
    """incident-report.md: una sección '## Incidente N' por incidente con los cinco campos llenos."""
    text = read_text(repo, "incident-report.md")
    if text is None:
        return 0.0, not_found(repo, "incident-report.md")
    found = incidents(text)
    score, problems = 0.0, []
    for number in range(1, total + 1):
        fields = found.get(number)
        if fields is None:
            problems.append("{0}: sin sección".format(number))
            continue
        ok = []
        for label in INCIDENT_LABELS:
            value = fields.get(norm(label), "")
            if label == "Comandos":
                ok.append("`" in value and meaningful(value, 1))
            elif label == "Evidencia":
                ok.append("evidence/" in value)
            else:
                ok.append(meaningful(value))
        score += sum(ok) / float(len(INCIDENT_LABELS))
        missing = [label for label, good in zip(INCIDENT_LABELS, ok) if not good]
        if missing:
            problems.append("{0}: {1}".format(number, ", ".join(missing)))
    complete = total - len(problems)
    detail = "{0}/{1} incidentes con los 5 campos completos".format(complete, total)
    if problems:
        detail += ". Incompletos: " + "; ".join(problems[:6])
    return score / total, detail


def incident_evidence(repo: Path, total: int = 10) -> Result:
    """Cada incidente cita en 'Evidencia' un archivo de evidence/ que existe y no está vacío."""
    text = read_text(repo, "incident-report.md")
    if text is None:
        return 0.0, not_found(repo, "incident-report.md")
    found = incidents(text)
    good, invalid = 0, []
    for number in range(1, total + 1):
        value = (found.get(number) or {}).get("evidencia", "")
        paths = re.findall(r"evidence/[\w./-]+", value)
        files = [Path(repo) / p.rstrip(".,)") for p in paths]
        if any(f.is_file() and f.stat().st_size > 0 and f.suffix.lower() in EVIDENCE_SUFFIXES for f in files):
            good += 1
        else:
            invalid.append(str(number))
    detail = "{0}/{1} incidentes con archivo de evidencia existente".format(good, total)
    if invalid:
        detail += "; sin evidencia válida: {0} (formatos aceptados: {1})".format(", ".join(invalid), " ".join(sorted(EVIDENCE_SUFFIXES)))
    return good / float(total), detail


def terminal_tools(repo: Path, minimum: int = 6) -> Result:
    """Herramientas de terminal distintas citadas en los campos Comandos y Diagnóstico."""
    text = read_text(repo, "incident-report.md")
    if text is None:
        return 0.0, not_found(repo, "incident-report.md")
    corpus = " ".join(f.get("comandos", "") + " " + f.get("diagnostico", "") for f in incidents(text).values())
    used = [tool for tool in TERMINAL_TOOLS if re.search(r"(?<![\w-])" + tool + r"(?![\w-])", corpus)]
    return ratio(len(used), minimum), "{0} herramientas distintas (mínimo {1}): {2}".format(len(used), minimum, ", ".join(used) or "ninguna")


def scripts_syntax(repo: Path) -> Result:
    """run.sh y scripts/: ejecutables, con shebang y sin errores de sintaxis (bash -n / Python)."""
    repo = Path(repo)
    targets = [repo / "run.sh"] if (repo / "run.sh").is_file() else []
    if not targets:
        return 0.0, "No existe run.sh en la raíz"
    targets += sorted(p for p in iter_files(repo / "scripts", {".sh", ".py"}))
    good, problems = 0, []
    for path in targets:
        relative = path.relative_to(repo)
        if path.suffix == ".py":
            try:
                ast.parse(path.read_text(encoding="utf-8", errors="replace"))
                good += 1
            except SyntaxError as exc:
                problems.append("{0}: sintaxis ({1})".format(relative, exc.msg))
            continue
        first = path.read_text(encoding="utf-8", errors="replace").splitlines()[:1]
        issues = []
        if not os.access(str(path), os.X_OK):
            issues.append("sin permiso de ejecución")
        if not first or not first[0].startswith("#!"):
            issues.append("sin shebang")
        check = subprocess.run(["bash", "-n", str(path)], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
        if check.returncode != 0:
            issues.append("bash -n: " + check.stdout.strip().splitlines()[-1][:80] if check.stdout.strip() else "bash -n falló")
        if issues:
            problems.append("{0}: {1}".format(relative, ", ".join(issues)))
        else:
            good += 1
    detail = "{0}/{1} scripts correctos".format(good, len(targets))
    if problems:
        detail += ". " + "; ".join(problems[:5])
    return good / float(len(targets)), detail


# --------------------------------------------------------------------------- Tecnólogo


LEGACY_IDENTIFIERS = [
    "nro_doc_ben", "nro_doc", "afi_mae", "afi_ben", "logmov", "est_afi", "cod_emp", "nom_emp", "cod_par",
    "person_master", "sp_registrar_retiro", "per_apo", "vlr_apo", "tip_mov", "fec_ret", "fec_afi",
    "nom1", "nom2", "ape1", "ape2",
]
LEGACY_PATTERN = re.compile(r"(?<![A-Za-z0-9_])(" + "|".join(LEGACY_IDENTIFIERS) + r")(?![A-Za-z0-9_])", re.I)


def _is_adapter(relative: Path) -> bool:
    return any("adapter" in part.lower() for part in relative.parts)


def adapter_encapsulation(repo: Path) -> Result:
    """Fuera del adapter, ningún archivo de src/ nombra tablas, columnas o procedimientos legacy."""
    src = Path(repo) / "src"
    if not src.is_dir():
        return 0.0, "No existe src/"
    inside, outside = [], []
    for path in iter_files(src, CODE_SUFFIXES):
        relative = path.relative_to(src)
        if is_test_path(relative):
            continue
        if LEGACY_PATTERN.search(path.read_text(encoding="utf-8", errors="replace")):
            (inside if _is_adapter(relative) else outside).append("src/" + relative.as_posix())
    if not inside:
        return 0.0, "Ningún archivo bajo una carpeta o archivo 'adapter' de src/ accede al esquema legacy{0}".format(
            " (sí lo hacen: " + ", ".join(outside[:4]) + ")" if outside else "")
    fraction = len(inside) / float(len(inside) + len(outside))
    detail = "{0} archivos del adapter conocen el esquema legacy; {1} archivos fuera del adapter también".format(len(inside), len(outside))
    if outside:
        detail += ": " + ", ".join(outside[:5])
    return fraction, detail


DEPENDENCIES_EXPECTED = {
    ("educacion", "AFI_MAE", "LECTURA"),
    ("educacion", "EMPRESA", "LECTURA"),
    ("subsidios", "AFI_MAE", "ESCRITURA"),
    ("subsidios", "LOGMOV", "ESCRITURA"),
    ("reportes", "AFI_MAE", "LECTURA"),
    ("reportes", "LOGMOV", "LECTURA"),
}
APP_ALIASES = {"educacion": "educacion", "subsidio": "subsidios", "reporte": "reportes", "portal": "portal", "movil": "movil", "mobile": "movil"}
IGNORED_APPS = ("gateway", "adapter", "api nueva", "servicio nuevo")
TABLE_ALIASES = {"afi_mae": "AFI_MAE", "person_master": "AFI_MAE", "afi_ben": "AFI_BEN", "empresa": "EMPRESA", "aportes": "APORTES", "logmov": "LOGMOV"}


def dependency_rows(text: str) -> Tuple[Set[Tuple[str, str, str]], int, int]:
    table = find_table(text, ["aplicacion", "tabla", "operacion", "criticidad"])
    if table is None:
        return set(), 0, 0
    columns, rows = table
    found = set()
    valid_criticality = considered = 0
    for row in rows:
        app_text = norm(cell(row, columns, "aplicacion"))
        if not app_text or any(ignored in app_text for ignored in IGNORED_APPS):
            continue
        considered += 1
        app = next((value for key, value in APP_ALIASES.items() if key in app_text), app_text)
        tables = {alias for key, alias in TABLE_ALIASES.items() if re.search(r"\b" + key + r"\b", norm(cell(row, columns, "tabla")))}
        operation = norm(cell(row, columns, "operacion"))
        operations = {op for op in ("LECTURA", "ESCRITURA") if op.lower() in operation}
        if norm(cell(row, columns, "criticidad")) in ("alta", "media", "baja"):
            valid_criticality += 1
        for table_name in tables:
            for op in operations:
                found.add((app, table_name, op))
    return found, valid_criticality, considered


def dependency_map(repo: Path) -> Result:
    """docs/dependency-map.md: tabla Aplicación | Tabla | Operación | Criticidad comparada con las dependencias reales."""
    text = read_text(repo, "docs/dependency-map.md")
    if text is None:
        return 0.0, not_found(repo, "docs/dependency-map.md")
    found, valid_criticality, total_rows = dependency_rows(text)
    if not total_rows:
        return 0.0, "No hay una tabla con columnas Aplicación | Tabla | Operación | Criticidad"
    hits = found & DEPENDENCIES_EXPECTED
    wrong = found - DEPENDENCIES_EXPECTED
    accuracy = max(0.0, (len(hits) - len(wrong)) / float(len(DEPENDENCIES_EXPECTED)))
    fraction = 0.8 * accuracy + 0.2 * ratio(valid_criticality, total_rows)
    detail = "{0}/{1} dependencias reales identificadas; {2} incorrectas; criticidad válida en {3}/{4} filas".format(
        len(hits), len(DEPENDENCIES_EXPECTED), len(wrong), valid_criticality, total_rows)
    if wrong:
        detail += "; incorrectas: " + ", ".join("{0} {1} {2}".format(*item) for item in sorted(wrong)[:4])
    return fraction, detail


MIGRATION_STATES = ("LEGACY", "DUAL", "MODERN")


def migration_plan(repo: Path) -> Result:
    """docs/migration-plan.md: tabla Dominio | Estado | Criterio para avanzar | Rollback y 'Siguiente dominio:'."""
    text = read_text(repo, "docs/migration-plan.md")
    if text is None:
        return 0.0, not_found(repo, "docs/migration-plan.md")
    table = find_table(text, ["dominio", "estado", "criterio", "rollback"])
    if table is None:
        return 0.0, "No hay una tabla con columnas Dominio | Estado | Criterio para avanzar | Rollback"
    columns, rows = table
    rows = [r for r in rows if cell(r, columns, "dominio").strip()]
    if not rows:
        return 0.0, "La tabla Dominio | Estado | Criterio para avanzar | Rollback no tiene filas"
    valid = [r for r in rows if cell(r, columns, "estado").strip().upper() in MIGRATION_STATES]
    affiliations = any("afiliacion" in norm(cell(r, columns, "dominio")) or "affiliation" in norm(cell(r, columns, "dominio")) for r in valid)
    measurable = sum(1 for r in rows if re.search(r"\d", cell(r, columns, "criterio")))
    rollback = sum(1 for r in rows if meaningful(cell(r, columns, "rollback"), 2))
    next_domain = any(
        re.search(r"siguiente dominio[*_]*\s*:[*_\s]*\w", norm(line)) for line in text.splitlines())
    parts = {
        "≥ 3 dominios con estado válido": (0.3, ratio(len(valid), 3)),
        "fila de Afiliaciones": (0.1, float(affiliations)),
        "criterios con número": (0.25, ratio(measurable, len(rows))),
        "rollback por dominio": (0.2, ratio(rollback, len(rows))),
        "Siguiente dominio": (0.15, float(bool(next_domain))),
    }
    fraction = sum(weight * value for weight, value in parts.values())
    detail = "; ".join("{0}: {1:.0%}".format(name, value) for name, (_, value) in parts.items())
    return fraction, "{0} dominios en la tabla. {1}".format(len(rows), detail)


# --------------------------------------------------------------------------- Profesional


def adrs(repo: Path, minimum: int = 3) -> Result:
    """docs/adr/: al menos tres ADR con Contexto, Decisión y Consecuencias (≥ 10 palabras) y Alternativas (≥ 2)."""
    folder = Path(repo) / "docs" / "adr"
    files = sorted(p for p in folder.glob("*.md") if not re.search(r"plantilla|template", p.name, re.I)) if folder.is_dir() else []
    if not files:
        return 0.0, "No hay ADR en docs/adr/ (la plantilla no cuenta)"
    complete, problems = 0, []
    for path in files:
        text = strip_comments(small_text(path) or "")
        missing = [key for key in ("contexto", "decision", "consecuencias") if not filled_section(text, key, ADR_MIN_WORDS)]
        if list_items(section_body(text, "alternativas") or "") < 2:
            missing.append("2 alternativas")
        if missing:
            problems.append("{0}: falta {1}".format(path.name, ", ".join(missing)))
        else:
            complete += 1
    detail = "{0} ADR completos de {1} archivos (mínimo {2})".format(complete, len(files), minimum)
    if problems:
        detail += ". " + "; ".join(problems[:4])
    return ratio(complete, minimum), detail


THREAT_CATEGORIES = [("autenticacion", "Autenticación"), ("finalidad", "Finalidad"), ("dato minimo", "Dato mínimo"), ("secretos", "Secretos"), ("auditoria", "Auditoría")]


def threat_model(repo: Path, summary: Optional[Dict[str, object]]) -> Result:
    """docs/threat-model.md: una fila por categoría obligatoria, con la prueba automatizada que la demuestra."""
    text = read_text(repo, "docs/threat-model.md")
    if text is None:
        return 0.0, not_found(repo, "docs/threat-model.md")
    table = find_table(text, ["categoria", "amenaza", "mitigacion", "prueba"])
    if table is None:
        return 0.0, "No hay una tabla con columnas Categoría | Amenaza | Mitigación | Prueba"
    columns, rows = table
    score, notes = 0.0, []
    for key, label in THREAT_CATEGORIES:
        matching = [r for r in rows if key in norm(cell(r, columns, "categoria"))]
        described = [r for r in matching if meaningful(cell(r, columns, "amenaza")) and meaningful(cell(r, columns, "mitigacion"))]
        proven = [r for r in described if passed_test(summary, cell(r, columns, "prueba"))]
        score += 0.5 * bool(described) + 0.5 * bool(proven)
        if not described:
            notes.append("{0}: sin fila completa".format(label))
        elif not proven:
            notes.append("{0}: la prueba citada no aparece aprobada".format(label))
    detail = "{0:.1f}/5 categorías cubiertas".format(score)
    if summary is None:
        detail += " (sin resultados JUnit: las pruebas citadas no se pudieron comprobar)"
    if notes:
        detail += ". " + "; ".join(notes)
    return score / len(THREAT_CATEGORIES), detail


LOAD_FIELDS = ["herramienta", "documentos", "duracion_segundos", "errores"]


def load_test_doc(repo: Path) -> Result:
    """docs/load-test.md con herramienta, documentos (≥ 10 000), duracion_segundos (≤ 300) y errores."""
    text = read_text(repo, "docs/load-test.md")
    if text is None:
        return 0.0, not_found(repo, "docs/load-test.md")
    values = {}
    lines = [norm(line) for line in text.splitlines()]
    for key in LOAD_FIELDS:
        pattern = re.compile(r"^[\s>*_|-]*" + key + r"[*_]*\s*:\s*[*_]*\s*(.+)$")
        for line in lines:
            match = pattern.match(line)
            if match and match.group(1).strip(" *_|"):
                values[key] = match.group(1).strip(" *_|")
                break

    def number(value: str) -> Optional[float]:
        match = re.search(r"\d[\d.,]*", value or "")
        if not match:
            return None
        raw = match.group(0)
        if re.fullmatch(r"\d{1,3}([.,]\d{3})+", raw):
            raw = re.sub(r"[.,]", "", raw)
        return float(raw.replace(",", "."))

    documents, duration = number(values.get("documentos", "")), number(values.get("duracion_segundos", ""))
    fraction = 0.15 * len(values) + 0.2 * float(documents is not None and documents >= 10000) + 0.2 * float(duration is not None and duration <= 300)
    detail = "campos: {0}/4; documentos={1}; duracion_segundos={2}".format(len(values), values.get("documentos", "-"), values.get("duracion_segundos", "-"))
    return fraction, detail


CAJAS = ["norte", "oriente", "centro", "sur"]
HARDCODED_ENDPOINT = re.compile(r"(?<![\w-])caja-(norte|oriente|sur)(?![\w-])|:900[124](?!\d)", re.I)


def cajas_config(repo: Path) -> Result:
    """config/cajas.(yaml|yml|json) declara las 4 cajas y src/ no tiene direcciones de cajas escritas en el código."""
    repo = Path(repo)
    config = None
    for name in ("cajas.yaml", "cajas.yml", "cajas.json"):
        config = find_file(repo, "config/" + name)
        if config:
            break
    declared = []
    if config:
        text = norm(small_text(config) or "")
        declared = [c for c in CAJAS if c in text]
    hardcoded = []
    for path in iter_files(repo / "src", CODE_SUFFIXES):
        relative = path.relative_to(repo / "src")
        if is_test_path(relative):
            continue
        if HARDCODED_ENDPOINT.search(path.read_text(encoding="utf-8", errors="replace")):
            hardcoded.append("src/" + relative.as_posix())
    fraction = 0.5 * ratio(len(declared), len(CAJAS)) + 0.5 * float(not hardcoded and (repo / "src").is_dir())
    detail = "{0}: {1}/4 cajas declaradas; {2} archivos de src/ con direcciones de cajas escritas en el código".format(
        config.relative_to(repo).as_posix() if config else "sin config/cajas.yaml", len(declared), len(hardcoded))
    if hardcoded:
        detail += ": " + ", ".join(hardcoded[:4])
    return fraction, detail


# --------------------------------------------------------------------------- catálogo para el validador de los equipos

OPENAPI_TECNOLOGO = ["/health", "/api/v1/members/{x}", "/api/v1/members/{x}/beneficiaries", "/api/v1/companies/{x}", "/api/v1/members/{x}/retirements", "/api/v1/migration/status"]
OPENAPI_PROFESIONAL = ["/api/v1/affiliations/{x}", "/api/v2/affiliations/{x}", "/api/v1/batch-checks", "/api/v1/batch-checks/{x}", "/api/v1/audit"]
ARCH_TECNOLOGO = ["contexto", "componentes", "modelo canonico", "cambio de esquema", "alternativas descartadas"]
ARCH_PROFESIONAL = ["contexto", "componentes", "flujo de consulta", "manejo de fallas", "alternativas descartadas"]
MIN_TESTS = {"tecnologo": 10, "profesional": 15}


# --------------------------------------------------------------------------- README: documentación del software


README_RUN = {"tecnico": ["docker compose", "up", "run.sh"], "tecnologo": ["docker compose", "up", "rollback.sh"], "profesional": ["docker compose", "up"]}
README_USAGE = {
    "tecnico": ["/afiliados/{x}", "afiliados_activos.csv", "excepciones.csv", "totales.txt", "top_error.txt"],
    "tecnologo": OPENAPI_TECNOLOGO,
    "profesional": OPENAPI_PROFESIONAL,
}
README_DOCS = {
    "tecnico": ["incident-report.md", "evidence", "AI_USAGE.md"],
    "tecnologo": ["docs/architecture.md", "docs/dependency-map.md", "docs/migration-plan.md", "openapi.yaml", "AI_USAGE.md"],
    "profesional": ["docs/architecture.md", "docs/adr", "docs/threat-model.md", "docs/load-test.md", "openapi.yaml", "config/cajas.yaml", "AI_USAGE.md"],
}


def heading_body(text: str, key: str) -> Optional[str]:
    """Texto bajo los encabezados de nivel 2 o más que empiezan por `key` (con sus subsecciones); None si no hay."""
    matches = list(re.finditer(r"^(#{1,6})\s*(.+?)\s*#*\s*$", text or "", re.M))
    bodies = []
    for index, match in enumerate(matches):
        title = re.sub(r"^[\d.)\s-]+", "", norm(match.group(2)))
        if len(match.group(1)) < 2 or not title.startswith(key):
            continue
        end = len(text)
        for following in matches[index + 1:]:
            if len(following.group(1)) <= len(match.group(1)):
                end = following.start()
                break
        bodies.append(text[match.end():end])
    return "\n".join(bodies) if bodies else None


def env_variables(repo: Path) -> Optional[List[str]]:
    text = read_text(repo, ".env.example")
    if text is None:
        return None
    return sorted(set(re.findall(r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=", text, re.M)))


def compose_services(repo: Path) -> Optional[List[str]]:
    """Nombres de los servicios de docker-compose.yml (sin librerías: por indentación bajo `services:`)."""
    text = None
    for name in ("docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml"):
        path = find_file(repo, name)
        text = small_text(path) if path else None
        if text is not None:
            break
    if text is None:
        return None
    services, inside, indent = [], False, None
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if re.match(r"^services\s*:\s*$", line):
            inside = True
            continue
        if not inside:
            continue
        if not line[0].isspace():
            break
        depth = len(line) - len(line.lstrip())
        indent = depth if indent is None else indent
        match = re.match(r"^\s+([A-Za-z0-9_.-]+)\s*:\s*$", line)
        if match and depth == indent:
            services.append(match.group(1))
    return services


def mentions(body: str, name: str, case: bool = False) -> bool:
    flags = 0 if case else re.I
    return bool(re.search(r"(?<![\w-])" + re.escape(name) + r"(?![\w-])", body or "", flags))


def mentions_route(body: str, route: str) -> bool:
    """La ruta aparece en el texto; `{documento}`, `{id}`… cuentan como el parámetro `{x}`."""
    normalized = re.sub(r"\{[^}/\s]+\}", "{x}", body or "")
    return bool(re.search(re.escape(route) + r"(?![\w/{-])", normalized))


def readme_doc(repo: Path, level: str) -> Result:
    """README.md con la documentación del software: once secciones; cuatro se contrastan con el repositorio."""
    text = read_text(repo, "README.md")
    if text is None:
        return 0.0, not_found(repo, "README.md")
    scores, problems = [], []

    def add(label: str, fraction: float, problem: str = "") -> None:
        scores.append(fraction)
        if fraction < 1:
            problems.append("{0}: {1}".format(label, problem or "falta o está corta"))

    def body(key: str) -> str:
        return strip_comments(heading_body(text, key) or "")

    add("Descripción", float(words(body("descripcion")) >= 30), "al menos 30 palabras")
    add("Integrantes", float(list_items(body("integrantes")) >= 2), "una viñeta por integrante")
    add("Requisitos", float(words(body("requisitos")) >= 5), "al menos 5 palabras")

    run = body("instalacion")
    run_missing = [item for item in README_RUN[level] if item not in run.lower()]
    run_ok = [words(run) >= 15] + [item not in run_missing for item in README_RUN[level]]
    add("Instalación y ejecución", ratio(sum(run_ok), len(run_ok)),
        "al menos 15 palabras y los comandos " + ", ".join(README_RUN[level]) + (" (faltan: " + ", ".join(run_missing) + ")" if run_missing else ""))

    variables = env_variables(repo)
    if variables is None:
        add("Configuración", 0.0, "no existe .env.example para contrastar")
    else:
        missing = [name for name in variables if not mentions(body("configuracion"), name, case=True)]
        add("Configuración", ratio(len(variables) - len(missing), len(variables)), "faltan variables de .env.example: " + ", ".join(missing[:8]))

    services = compose_services(repo)
    if services is None:
        add("Arquitectura", 0.0, "no existe docker-compose.yml para contrastar")
    else:
        architecture = body("arquitectura")
        missing = [name for name in services if not mentions(architecture, name)]
        fraction = 0.5 * float(words(architecture) >= 30) + 0.5 * ratio(len(services) - len(missing), len(services))
        add("Arquitectura", fraction, "al menos 30 palabras y cada servicio de docker-compose.yml" + (" (faltan: " + ", ".join(missing[:8]) + ")" if missing else ""))

    usage = body("uso")
    missing = [item for item in README_USAGE[level] if not (mentions_route(usage, item) if item.startswith("/") else mentions(usage, item))]
    add("Uso", ratio(len(README_USAGE[level]) - len(missing), len(README_USAGE[level])), "faltan: " + ", ".join(missing))

    tests = body("pruebas")
    tests_ok = [words(tests) >= 15] + ([("--profile test" in tests)] if level != "tecnico" else [])
    add("Pruebas", ratio(sum(tests_ok), len(tests_ok)), "al menos 15 palabras" + (" y el comando docker compose --profile test run --rm tests" if level != "tecnico" else ""))

    documents = body("documentacion")
    missing = [item for item in README_DOCS[level] if item.lower() not in documents.lower()]
    add("Documentación", ratio(len(README_DOCS[level]) - len(missing), len(README_DOCS[level])), "faltan referencias a: " + ", ".join(missing))

    add("Qué resolvimos", float(words(body("que resolvimos")) >= 30), "al menos 30 palabras")
    add("Limitaciones y pendientes", float(words(body("limitaciones")) >= 10), "al menos 10 palabras")

    complete = sum(1 for score in scores if score >= 1)
    detail = "README.md: {0}/{1} secciones completas".format(complete, len(scores))
    if problems:
        detail += ". " + "; ".join(problems)
    return sum(scores) / len(scores), detail


def static_checks(level: str, repo: Path, start=None, deadline=None) -> List[Tuple[str, str, Result]]:
    """Lo que `./validator entregables` puede revisar sin Docker (las pruebas y el rollback se ejecutan aparte)."""
    repo = Path(repo)
    if level == "tecnico":
        return [
            ("TE01", "Informe de incidentes", incident_report(repo)),
            ("TE02", "Evidencia por incidente", incident_evidence(repo)),
            ("TE03", "Diagnóstico desde terminal", terminal_tools(repo)),
            ("TE04", "Scripts verificables", scripts_syntax(repo)),
            ("TE05", "Historial Git", git_history(repo, start, deadline)),
            ("TE06", "AI_USAGE.md", ai_usage(repo)),
            ("TE08", "README: documentación del software", readme_doc(repo, "tecnico")),
        ]
    if level == "tecnologo":
        summary = junit_summary(repo)
        return [
            ("GE01", "Adapter encapsula el esquema", adapter_encapsulation(repo)),
            ("GE02", "Mapa de dependencias", dependency_map(repo)),
            ("GE03", "Plan de migración", migration_plan(repo)),
            ("GE05", "Pruebas automatizadas (último resultado en test-results/)", suite_score(summary, None, MIN_TESTS["tecnologo"])),
            ("GE06", "Contrato OpenAPI", openapi_paths(repo, OPENAPI_TECNOLOGO)),
            ("GE07", "Documento de arquitectura", architecture_doc(repo, ARCH_TECNOLOGO)),
            ("GE08", "Historial Git", git_history(repo, start, deadline)),
            ("GE09", "AI_USAGE.md", ai_usage(repo)),
            ("GE11", "README: documentación del software", readme_doc(repo, "tecnologo")),
        ]
    if level == "profesional":
        summary = junit_summary(repo)
        return [
            ("PE01", "ADR", adrs(repo)),
            ("PE02", "Modelo de amenazas con pruebas", threat_model(repo, summary)),
            ("PE03", "Pruebas automatizadas (último resultado en test-results/)", suite_score(summary, None, MIN_TESTS["profesional"])),
            ("PE04", "Prueba de carga documentada", load_test_doc(repo)),
            ("PE05", "Cajas por configuración", cajas_config(repo)),
            ("PE06", "Contrato OpenAPI v1 y v2", openapi_paths(repo, OPENAPI_PROFESIONAL)),
            ("PE07", "Documento de arquitectura", architecture_doc(repo, ARCH_PROFESIONAL)),
            ("PE08", "Historial Git", git_history(repo, start, deadline)),
            ("PE09", "AI_USAGE.md", ai_usage(repo)),
            ("PE11", "README: documentación del software", readme_doc(repo, "profesional")),
        ]
    raise ValueError("Nivel desconocido: " + level)


PITCH_NOTE = "{0} Pitch de 1 minuto (se registra en Mi equipo: video público de Drive de 60 s o menos; el comité revisa el contenido)"
OFFICIAL_ONLY = {
    "tecnico": [PITCH_NOTE.format("TE07")],
    "tecnologo": ["GE04 Rollback ejecutable (ejecuta ./rollback.sh y un retiro desde Subsidios)", PITCH_NOTE.format("GE10")],
    "profesional": [PITCH_NOTE.format("PE10")],
}


def print_report(level: str, repo: Path, points: Dict[str, float], start=None) -> int:
    """Tabla de `./validator entregables`: mismas reglas y puntos que el calificador oficial."""
    rows = static_checks(level, Path(repo), start)
    width = 72
    print("=" * width)
    print("ENTREGABLES — revisión con las reglas del calificador oficial".center(width).rstrip())
    print("=" * width)
    earned_total = max_total = 0.0
    for check_id, name, (fraction, detail) in rows:
        maximum = points.get(check_id, 0)
        earned = maximum * fraction
        earned_total += earned
        max_total += maximum
        status = "PASS" if fraction >= 0.999 else ("PARCIAL" if fraction > 0 else "FAIL")
        print("{0} {1} {2:<7} {3:>5.2f} / {4:g}".format(check_id, (name + " ").ljust(44, ".")[:44], status, earned, maximum))
        if status != "PASS":
            print("     " + detail[:300])
    print("-" * width)
    print("PUNTOS: {0:.2f} / {1:g}".format(earned_total, max_total))
    for item in OFFICIAL_ONLY.get(level, []):
        print("No se revisa aquí: " + item)
    if level in ("tecnologo", "profesional"):
        print("Las pruebas se leen del último test-results/; el oficial las ejecuta con: docker compose --profile test run --rm tests")
    if start is None:
        print("Historial Git: se cuentan todos los commits. Use --desde AAAA-MM-DDTHH:MM para contar solo los del evento.")
    return 0


# --------------------------------------------------------------------------- generado por tools/sync_kits.py (no editar)
LEVEL = "tecnico"
POINTS = {"TE01": 5, "TE02": 2, "TE03": 1, "TE04": 1, "TE05": 2, "TE06": 2, "TE08": 2}

if __name__ == "__main__":
    import sys as _sys

    _args = _sys.argv[1:]
    _start = _args[_args.index("--desde") + 1] if "--desde" in _args and len(_args) > _args.index("--desde") + 1 else None
    _sys.exit(print_report(LEVEL, Path(__file__).resolve().parent, POINTS, _start))
