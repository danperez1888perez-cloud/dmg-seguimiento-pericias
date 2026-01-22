import json
from pathlib import Path
from openpyxl import Workbook
from openpyxl.worksheet.datavalidation import DataValidation

DATA_DIR = Path("data/casos")
INDEX_FILE = Path("data/index.json")
EXPORT_FILE = Path("web/exports/Matriz_Oficial.xlsx")

SECCIONES = [
  "AVA","AVIS +F","DOCUMENTOLOGIA","BALISTICA","PAPILOSCOPIA","IDENTIDAD HUMANA",
  "REVENIDOS QUIMICOS","REMARCACIONES","DILIGENCIAS IOT","ESCENA IOT",
  "MODELO FLAGRANCIA","QUIMICA Y TOXICOLOGIA"
]
ESTADOS = ["No iniciada","En proceso","Realizada"]

def normalize_estado_general(pericias):
    ests = [p.get("estado","") for p in pericias]
    if "No iniciada" in ests: return "No iniciada"
    if "En proceso" in ests: return "En proceso"
    return "Realizada" if ests else "No iniciada"

def max_ultima_actualizacion(pericias):
    dates = [p.get("ultima_actualizacion","") for p in pericias if p.get("ultima_actualizacion")]
    return max(dates) if dates else ""

def load_cases():
    cases = []
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    for fp in sorted(DATA_DIR.glob("*.json")):
        cases.append(json.loads(fp.read_text(encoding="utf-8")))
    return cases

def write_index(cases):
    idx = []
    for c in cases:
        per = c.get("pericias", [])
        idx.append({
            "caso": c.get("caso",""),
            "tipo": c.get("tipo",""),
            "fecha_hecho": c.get("fecha_hecho",""),
            "estado_general": normalize_estado_general(per),
            "total_pericias": len(per),
            "ultima_actualizacion": max_ultima_actualizacion(per)
        })
    INDEX_FILE.parent.mkdir(parents=True, exist_ok=True)
    INDEX_FILE.write_text(json.dumps(idx, ensure_ascii=False, indent=2), encoding="utf-8")

def write_xlsx(cases):
    wb = Workbook()
    ws = wb.active
    ws.title = "MATRIZ_GENERAL"

    headers = [
      "Nº Caso","Tipo de Caso","Fecha del Hecho","Tipo de Pericia",
      "Sección Responsable","Fecha de Disposición","Estado de la Pericia",
      "Fecha Última Actualización","Acción / Avance Realizado","Responsable","Observaciones",
      "Usuario editor","Timestamp"
    ]
    ws.append(headers)

    for c in cases:
        for p in c.get("pericias", []):
            ws.append([
                c.get("caso",""),
                c.get("tipo",""),
                c.get("fecha_hecho",""),
                p.get("tipo_pericia",""),
                p.get("seccion",""),
                p.get("fecha_disposicion",""),
                p.get("estado",""),
                p.get("ultima_actualizacion",""),
                p.get("avance",""),
                p.get("responsable",""),
                p.get("observaciones",""),
                p.get("_last_editor",""),
                p.get("_last_edit_ts","")
            ])

    ws_val = wb.create_sheet("VALIDACIONES")
    ws_val["A1"] = "Estados"
    for i, s in enumerate(ESTADOS, start=2):
        ws_val[f"A{i}"] = s
    ws_val["B1"] = "Secciones"
    for i, s in enumerate(SECCIONES, start=2):
        ws_val[f"B{i}"] = s

    dv_estado = DataValidation(type="list", formula1=f"=VALIDACIONES!$A$2:$A${1+len(ESTADOS)}", allow_blank=True)
    dv_seccion = DataValidation(type="list", formula1=f"=VALIDACIONES!$B$2:$B${1+len(SECCIONES)}", allow_blank=True)
    ws.add_data_validation(dv_estado)
    ws.add_data_validation(dv_seccion)
    dv_estado.add("G2:G5000")
    dv_seccion.add("E2:E5000")

    EXPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    wb.save(EXPORT_FILE)

def main():
    cases = load_cases()
    write_index(cases)
    write_xlsx(cases)

if __name__ == "__main__":
    main()
