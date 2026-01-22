import os, re, json
from pathlib import Path
from datetime import datetime

DATA_DIR = Path("data/casos")

def parse_form(body: str) -> dict:
    fields = {}
    parts = re.split(r"\n###\s+", "\n" + body.strip())
    for p in parts:
        p = p.strip()
        if not p:
            continue
        lines = p.splitlines()
        key = lines[0].strip()
        val = "\n".join(lines[1:]).strip()
        val = re.sub(r"^_No response_\s*$", "", val, flags=re.M).strip()
        fields[key] = val
    return fields

def load_case(caso_id: str) -> dict:
    fp = DATA_DIR / f"{caso_id}.json"
    if not fp.exists():
        return {
            "caso": caso_id,
            "tipo": "Connotación",
            "fecha_hecho": "",
            "estado_general": "No iniciada",
            "pericias": []
        }
    return json.loads(fp.read_text(encoding="utf-8"))

def save_case(caso: dict):
    fp = DATA_DIR / f"{caso['caso']}.json"
    fp.parent.mkdir(parents=True, exist_ok=True)
    fp.write_text(json.dumps(caso, ensure_ascii=False, indent=2), encoding="utf-8")

def next_pericia_id(pericias: list) -> str:
    nums = []
    for p in pericias:
        m = re.match(r"PER-(\d+)", (p.get("id") or "").strip())
        if m:
            nums.append(int(m.group(1)))
    n = (max(nums) + 1) if nums else 1
    return f"PER-{n:03d}"

def main():
    title = os.environ.get("ISSUE_TITLE", "")
    body = os.environ.get("ISSUE_BODY", "")
    user = os.environ.get("ISSUE_USER", "unknown")

    fields = parse_form(body)

    is_add = "AGREGAR" in title.upper()
    is_update = "ACTUALIZAR" in title.upper()

    caso_id = fields.get("Nº Caso") or fields.get("N\u00ba Caso") or fields.get("N° Caso") or ""
    caso_id = caso_id.strip()
    if not caso_id:
        raise SystemExit("No se encontró Nº Caso en el issue form.")

    caso = load_case(caso_id)

    if is_add:
        per = {
            "id": next_pericia_id(caso.get("pericias", [])),
            "tipo_pericia": (fields.get("Tipo de Pericia") or "").strip(),
            "seccion": (fields.get("Sección Responsable") or "").strip(),
            "estado": (fields.get("Estado") or "").strip(),
            "fecha_disposicion": (fields.get("Fecha de Disposición (YYYY-MM-DD)") or "").strip(),
            "ultima_actualizacion": (fields.get("Última Actualización (YYYY-MM-DD)") or "").strip(),
            "avance": (fields.get("Avance / Acción realizada") or "").strip(),
            "responsable": (fields.get("Responsable") or "").strip(),
            "observaciones": (fields.get("Observaciones") or "").strip(),
            "_last_editor": user,
            "_last_edit_ts": datetime.utcnow().isoformat() + "Z"
        }
        caso.setdefault("pericias", []).append(per)

    elif is_update:
        per_id = (fields.get("ID de Pericia") or "").strip()
        if not per_id:
            raise SystemExit("Falta ID de Pericia para actualizar.")

        updated = False
        for p in caso.get("pericias", []):
            if (p.get("id") or "").strip() == per_id:
                p["estado"] = (fields.get("Estado") or "").strip()
                p["ultima_actualizacion"] = (fields.get("Última Actualización (YYYY-MM-DD)") or "").strip()
                p["avance"] = (fields.get("Avance / Acción realizada") or "").strip()
                p["responsable"] = (fields.get("Responsable") or "").strip()
                obs = (fields.get("Observaciones") or "").strip()
                if obs:
                    p["observaciones"] = obs
                p["_last_editor"] = user
                p["_last_edit_ts"] = datetime.utcnow().isoformat() + "Z"
                updated = True
                break

        if not updated:
            raise SystemExit(f"No se encontró la pericia {per_id} en el caso {caso_id}.")

    else:
        raise SystemExit("El título del issue debe incluir [AGREGAR PERICIA] o [ACTUALIZAR PERICIA].")

    save_case(caso)

if __name__ == "__main__":
    main()
