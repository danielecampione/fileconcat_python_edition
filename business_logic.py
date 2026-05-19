# business_logic.py
import os

def merge_files(folder, extensions, output_name="output.txt"):
    output_path = os.path.join(folder, output_name)

    with open(output_path, "w", encoding="utf-8") as out:
        for root, dirs, files in os.walk(folder):
            for f in files:
                if any(f.lower().endswith("." + ext) for ext in extensions):
                    full = os.path.join(root, f)
                    out.write(f"===== FILE: {full} =====\n")
                    try:
                        with open(full, "r", encoding="utf-8", errors="ignore") as src:
                            out.write(src.read())
                    except Exception as e:
                        out.write(f"[ERRORE LETTURA: {e}]\n")
                    out.write("\n\n")

    return output_path
