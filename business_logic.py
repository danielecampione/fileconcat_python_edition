# business_logic.py
import os


def merge_files(folder, extensions, output_name="output.txt"):
    """
    Walks `folder` recursively and merges all files matching `extensions`
    into a single output file saved in `folder`.
    Returns the path to the output file.
    """
    output_path = os.path.join(folder, output_name)

    with open(output_path, "w", encoding="utf-8") as out:
        for root, dirs, files in os.walk(folder):
            # Skip hidden directories
            dirs[:] = [d for d in dirs if not d.startswith(".")]
            for f in sorted(files):
                if any(f.lower().endswith("." + ext.lower()) for ext in extensions):
                    full = os.path.join(root, f)
                    # Avoid including the output file itself
                    if os.path.abspath(full) == os.path.abspath(output_path):
                        continue
                    out.write(f"===== FILE: {full} =====\n")
                    try:
                        with open(full, "r", encoding="utf-8", errors="ignore") as src:
                            out.write(src.read())
                    except Exception as e:
                        out.write(f"[ERRORE LETTURA: {e}]\n")
                    out.write("\n\n")

    return output_path


def merge_file_list(file_paths, output_path):
    """
    Merges a specific list of file paths (accumulated via GUI) into `output_path`.
    Returns the output_path.
    """
    with open(output_path, "w", encoding="utf-8") as out:
        for full in file_paths:
            out.write(f"===== FILE: {full} =====\n")
            try:
                with open(full, "r", encoding="utf-8", errors="ignore") as src:
                    out.write(src.read())
            except Exception as e:
                out.write(f"[ERRORE LETTURA: {e}]\n")
            out.write("\n\n")

    return output_path
