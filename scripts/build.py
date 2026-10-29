#!/usr/bin/env python3
"""Build the standalone host, optionally selecting explicit source checkouts."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]


def metadata(cargo, manifest, env, dependencies=True):
    command = [*cargo, "metadata", "--format-version", "1", "--all-features",
               "--manifest-path", str(manifest)]
    if not dependencies:
        command.append("--no-deps")
    return json.loads(subprocess.check_output(command, cwd=ROOT, env=env, text=True))


def revision(directory):
    return subprocess.check_output(
        ["git", "-C", str(directory), "rev-parse", "HEAD"], text=True
    ).strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native", action="store_true",
                        help="Build for the current CPU")
    parser.add_argument("--claviron-source", type=Path)
    parser.add_argument("--deno-source", type=Path)
    args = parser.parse_args()
    if bool(args.claviron_source) != bool(args.deno_source):
        parser.error("supply both source paths or neither")

    env = os.environ.copy()
    if args.native:
        env["RUSTFLAGS"] = (env.get("RUSTFLAGS", "") + " -C target-cpu=native").strip()
    cache = ROOT / ".cache"
    cache.mkdir(exist_ok=True)
    cargo = ["cargo"]
    sources = {}
    if args.claviron_source:
        sources = {
            "claviron": args.claviron_source.resolve(),
            "claviron-deno": args.deno_source.resolve(),
        }
        for name, directory in sources.items():
            packages = metadata(["cargo"], directory / "Cargo.toml", env, False)["packages"]
            if not any(p["name"] == name for p in packages):
                parser.error(f"{directory} does not contain {name}")
        config = cache / "sources.toml"
        config.write_text("[patch.crates-io]\n" + "".join(
            f"{json.dumps(name)} = {{ path = {json.dumps(str(directory))} }}\n"
            for name, directory in sources.items()
        ))
        cargo += ["--config", str(config)]

    resolved = metadata(cargo, ROOT / "Cargo.toml", env)
    for name, directory in sources.items():
        package = next(p for p in resolved["packages"] if p["name"] == name)
        if package["source"] is not None or Path(package["manifest_path"]).resolve() != directory / "Cargo.toml":
            raise SystemExit(f"{name} did not resolve to the selected source; refresh this workspace's lockfile")

    subprocess.run([*cargo, "build", "--release", "--workspace", "--all-features",
                    "--all-targets"], cwd=ROOT, env=env, check=True)
    dependencies = subprocess.check_output(
        [*cargo, "tree", "--workspace", "--all-features", "--edges", "normal"],
        cwd=ROOT, env=env, text=True,
    )
    (cache / "dependencies.txt").write_text(dependencies)
    (cache / "metadata.json").write_text(json.dumps(resolved, indent=2) + "\n")
    record = {
        "native": args.native,
        "rustflags": env.get("RUSTFLAGS", ""),
        "rustc": subprocess.check_output(["rustc", "--version"], text=True).strip(),
        "target_directory": resolved["target_directory"],
        "lockfile_sha256": hashlib.sha256((ROOT / "Cargo.lock").read_bytes()).hexdigest(),
        "sources": {
            name: {"path": str(directory), "revision": revision(directory)}
            for name, directory in sources.items()
        },
        "dependency_tree": str(cache / "dependencies.txt"),
        "cargo_metadata": str(cache / "metadata.json"),
    }
    (cache / "build.json").write_text(json.dumps(record, indent=2) + "\n")
    print(f"Build record: {cache / 'build.json'}")


if __name__ == "__main__":
    main()
