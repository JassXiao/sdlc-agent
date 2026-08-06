from pathlib import Path
from typing import Dict, Any, List

def save_sdlc_project_to_disk(final_state: Dict[str, Any], output_dir: str = "./generated_project") -> Path:
    base_path = Path(output_dir).resolve()
    print(f"\n📂 导出工程生成物至绝对路径: {base_path}")

    total_files = 0

    def _write_modules(code_modules: List[Dict[str, Any]], default_folder: str) -> None:
        nonlocal total_files
        for module in code_modules:
            relative_path_str = module.get("file_path", "").strip()
            content = module.get("content", "")
            if not relative_path_str:
                continue

            clean_path_str = relative_path_str.lstrip("/\\")
            if clean_path_str.startswith("backend/") or clean_path_str.startswith("frontend/"):
                target_file_path = base_path / clean_path_str
            else:
                target_file_path = base_path / default_folder / clean_path_str

            target_file_path.parent.mkdir(parents=True, exist_ok=True)
            target_file_path.write_text(content, encoding="utf-8")
            total_files += 1
            print(f"  └─ 📄 [已导出] {target_file_path.relative_to(base_path)}")

    _write_modules(final_state.get("backend_code", []), "backend")
    _write_modules(final_state.get("frontend_code", []), "frontend")

    docs_dir = base_path / "docs"
    if final_state.get("openapi_yaml"):
        docs_dir.mkdir(parents=True, exist_ok=True)
        (docs_dir / "openapi.yaml").write_text(final_state["openapi_yaml"], encoding="utf-8")
        total_files += 1
        print(f"  └─ 📄 [已导出] docs/openapi.yaml")

    if final_state.get("ddl_sql"):
        docs_dir.mkdir(parents=True, exist_ok=True)
        (docs_dir / "schema.sql").write_text(final_state["ddl_sql"], encoding="utf-8")
        total_files += 1
        print(f"  └─ 📄 [已导出] docs/schema.sql")

    print(f"\n🎉 导出完成，共计 {total_files} 个文件落盘。")
    return base_path
