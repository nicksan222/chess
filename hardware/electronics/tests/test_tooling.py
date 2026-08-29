"""Both hardware tools do the same sequential job and install their own toolchain."""

from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
RUNNERS = ("cad", "electronics")
LISTED_PROJECTS = {
    "cad": [
        "hardware/cad/projects/single-tile-top/generate.py",
        "hardware/cad/projects/single-tile-bottom/generate.py",
        "hardware/cad/projects/single-tile-merged/generate.py",
        "hardware/cad/projects/board-skeleton/generate.py",
        "hardware/cad/projects/board-assembly/generate.py",
    ],
    "electronics": [
        "hardware/electronics/projects/square/generate.py",
        "hardware/electronics/projects/chessboard/generate.py",
    ],
}


def runner_source(name: str) -> str:
    return (REPO / "tools" / name).read_text()


class SharedPipelineTest(unittest.TestCase):
    def test_runners_always_setup_then_test_then_generate(self) -> None:
        for name in RUNNERS:
            with self.subTest(runner=name):
                source = runner_source(name)
                self.assertNotIn("case ", source)
                self.assertLess(source.index("setup"), source.index("run_tests"))
                self.assertLess(source.index("run_tests"), source.index("generate"))
                self.assertIn("if [[ $# -ne 0 ]]; then", source)
                self.assertIn(f"Usage: ./tools/{name}", source)

    def test_extra_arguments_are_an_error(self) -> None:
        for name in RUNNERS:
            with self.subTest(runner=name):
                result = subprocess.run(
                    [f"./tools/{name}", "check"],
                    cwd=REPO,
                    text=True,
                    capture_output=True,
                )
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stderr, f"Usage: ./tools/{name}\n")

    def test_both_runners_share_only_project_listing(self) -> None:
        library = (REPO / "tools" / "lib" / "pipeline.sh").read_text()
        self.assertIn("list_projects()", library)
        self.assertIn("${domain_dir}/projects", library)
        self.assertNotIn("pipeline_main", library)
        for name in RUNNERS:
            with self.subTest(runner=name):
                source = runner_source(name)
                self.assertIn("source tools/lib/pipeline.sh", source)
                self.assertIn("list_projects", source)
                self.assertNotIn("pipeline_main", source)
                self.assertNotIn("generation-order", source)

    def test_list_projects_orders_each_domain(self) -> None:
        for domain, paths in LISTED_PROJECTS.items():
            with self.subTest(domain=domain):
                result = subprocess.run(
                    [
                        "bash",
                        "-c",
                        "source tools/lib/pipeline.sh\n"
                        f"domain_dir=hardware/{domain}\n"
                        "list_projects\n",
                    ],
                    cwd=REPO,
                    check=True,
                    text=True,
                    capture_output=True,
                )
                self.assertEqual(result.stdout.splitlines(), paths)

    def test_each_domain_keeps_generated_output_in_one_folder(self) -> None:
        for name in RUNNERS:
            with self.subTest(runner=name):
                source = runner_source(name)
                self.assertIn('"${domain_dir}/generated"', source)
                generated = REPO / "hardware" / name / "generated"
                self.assertTrue(generated.is_dir(), str(generated))
                self.assertIn(
                    "do not edit", (generated / "README.md").read_text().lower()
                )


class ElectronicsToolingTest(unittest.TestCase):
    def test_runner_bootstraps_a_local_venv(self) -> None:
        tool = runner_source("electronics")
        self.assertIn(".cache/electronics", tool)
        self.assertIn("requirements.txt", tool)
        requirements = REPO / "hardware" / "electronics" / "requirements.txt"
        self.assertIn("schemdraw", requirements.read_text())
        self.assertNotIn("kicad", tool.lower())
        self.assertNotIn("docker", tool.lower())

    def test_cad_runner_caches_blender_instead_of_installing_it(self) -> None:
        tool = runner_source("cad")
        self.assertIn(".cache/blender", tool)
        self.assertIn("BLENDER_BIN", tool)
        self.assertIn("sha256sum", tool)

    def test_devcontainer_does_not_dispatch_hardware_verbs(self) -> None:
        post = (REPO / ".devcontainer" / "post-create.sh").read_text()
        for name in RUNNERS:
            self.assertNotIn(f"./tools/{name} setup", post, name)
            self.assertNotIn(f"./tools/{name} check", post, name)
        self.assertIn("./tools/electronics", post)
        self.assertIn("./tools/cad", post)
        self.assertNotIn("kicad", post.lower())
        spec = json.loads((REPO / ".devcontainer" / "devcontainer.json").read_text())
        self.assertIn("post-create.sh", spec["postCreateCommand"])
        self.assertNotIn("KICAD_IMAGE", spec.get("containerEnv", {}))
        self.assertNotIn("initializeCommand", spec)

    def test_devcontainer_image_can_run_both_toolchains(self) -> None:
        """The image must ship every package the hardware jobs need."""
        dockerfile = (REPO / ".devcontainer" / "Dockerfile").read_text()
        for package in (
            "curl",
            "libgl1",
            "libice6",
            "libsm6",
            "libx11-6",
            "libxext6",
            "libxfixes3",
            "libxi6",
            "libxkbcommon0",
            "libxrender1",
            "python3-venv",
            "xz-utils",
        ):
            self.assertIn(package, dockerfile, package)


class ContinuousIntegrationTest(unittest.TestCase):
    def test_ci_runs_the_same_full_job_as_a_developer(self) -> None:
        workflow = (REPO / ".github" / "workflows" / "ci.yml").read_text()
        self.assertIn("run: ./tools/cad\n", workflow)
        self.assertIn("run: ./tools/electronics\n", workflow)
        self.assertIn("runCmd: ./tools/electronics && ./tools/cad\n", workflow)
        self.assertNotIn("./tools/cad check", workflow)
        self.assertNotIn("./tools/electronics check", workflow)
        for name in RUNNERS:
            self.assertIn(f"hardware/{name}/generated", workflow, name)
        self.assertIn("devcontainers/ci", workflow)

        check = (REPO / "tools" / "check").read_text()
        self.assertIn("./tools/cad\n", check)
        self.assertIn("./tools/electronics\n", check)
        self.assertNotIn("./tools/cad check", check)
        self.assertNotIn("./tools/electronics check", check)

        makefile = (REPO / "Makefile").read_text()
        self.assertNotIn("cad-check", makefile)
        self.assertNotIn("electronics-check", makefile)
        self.assertNotIn("./tools/cad setup", makefile)
        self.assertNotIn("./tools/electronics setup", makefile)


if __name__ == "__main__":
    unittest.main()
