"""Full docs pipeline. Run from repo root:

    python scripts/docs/all.py [--shots ...] [--skip-shots]

Steps: content -> viewmap -> validate -> screenshots -> validate screenshots
-> build reports. Stops at the first failure.
"""
import subprocess
import sys

STEPS = [
    ("content", [sys.executable, "scripts/docs/gen_content.py"], {}),
    ("viewmap", [sys.executable, "scripts/docs/gen_viewmap.py"], {}),
    ("validate", [sys.executable, "scripts/docs/validate.py"], {}),
]


def run(name, cmd, extra):
    print(f"=== {name}: {' '.join(cmd + extra)}")
    r = subprocess.run(cmd + extra)
    if r.returncode != 0:
        print(f"FAILED at {name}")
        sys.exit(r.returncode)


def main():
    args = sys.argv[1:]
    skip_shots = "--skip-shots" in args
    shot_args = []
    for a in args:
        if a.startswith("--shots"):
            shot_args = [a]
    for name, cmd, _e in STEPS:
        run(name, cmd, [])
    if not skip_shots:
        run("screenshots",
            [sys.executable, "scripts/docs/generate_screenshots.py", "--update"], shot_args)
        run("validate-screenshots",
            [sys.executable, "scripts/docs/validate_screenshots.py"], [])
    run("build", [sys.executable, "scripts/docs/build.py"], [])
    print("docs pipeline complete")


if __name__ == "__main__":
    main()
