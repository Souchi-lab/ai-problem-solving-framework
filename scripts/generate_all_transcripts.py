import os
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path.cwd() / "src"))

from apsf.storage.run_repository import RunRepository
from apsf.orchestration.transcript_generator import TranscriptGenerator

def find_project_root():
    current = Path(__file__).resolve().parent
    for _ in range(5):
        if (current / "runs").exists() and (current / "src").exists():
            return current
        current = current.parent
    return Path(os.getcwd())

def main():
    root = find_project_root()
    repo = RunRepository(
        runs_dir=root / "runs",
        template_dir=root / "runs" / "_template"
    )
    gen = TranscriptGenerator()
    
    runs = repo.list_all_runs(taxonomy=None)
    print(f"Found {len(runs)} runs.")
    
    for full_name in runs:
        if "/" in full_name:
            taxonomy, run_name = full_name.split("/", 1)
            run_dir = repo.get_child_run_dir(taxonomy, run_name)
        else:
            taxonomy = "legacy" # Fallback if no taxonomy
            run_name = full_name
            run_dir = repo.get_run_dir(run_name)
        
        if run_dir.exists():
            print(f"Generating transcript for: {full_name}...")
            gen.write(run_dir)
        else:
            print(f"Warning: Directory not found for {full_name}")

if __name__ == "__main__":
    main()
