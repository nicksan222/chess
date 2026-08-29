"""Both hardware tools do the same sequential job and install their own toolchain."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
RUNNERS = ("cad", "electronics")
OPTIONAL_COMMANDS = ("list", "setup", "check", "build", "help")


def runner_source(name: str) -> str:
    return (REPO / "tools" / name).read_text()


def default_path(source: str) -> str:
    return source.split("if [[ $# -eq 0 ]]; then", 1)[1].split("fi", 1)[0]


class SharedPipelineTest(unittest.TestCase):
    def test_default_path_is_setup_then_tests_then_generate(self) -> None:
        for name in RUNNERS:
            with self.subTest(runner=name):
                source = runner_source(name)
                self.assertIn("if [[ $# -eq 0 ]]; then", source)
                body = default_path(source)
                self.assertLess(body.index("setup"), body.index("run_tests"))
                self.assertLess(body.index("run_tests"), body.index("generate"))
                self.assertLess(
                    source.index("if [[ $# -eq 0 ]]; then"),
                    source.index("case "),
                )

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

    def test_optional_commands_stay_available(self) -> None:
        for name in RUNNERS:
            source = runner_source(name)
            for command in OPTIONAL_COMMANDS:
                self.assertIn(command, source, command)

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

    def test_devcontainer_prepares_both_toolchains(self) -> None:
        post = (REPO / ".devcontainer" / "post-create.sh").read_text()
        for name in RUNNERS:
            self.assertIn(f"./tools/{name} setup", post, name)
        self.assertNotIn("kicad", post.lower())
        spec = json.loads((REPO / ".devcontainer" / "devcontainer.json").read_text())
        self.assertIn("post-create.sh", spec["postCreateCommand"])
        self.assertNotIn("KICAD_IMAGE", spec.get("containerEnv", {}))
        self.assertNotIn("initializeCommand", spec)

    def test_devcontainer_image_can_run_both_toolchains(self) -> None:
        """Neither setup verb may need a package the image does not ship."""
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
        for name in RUNNERS:
            self.assertIn(f"hardware/{name}/generated", workflow, name)
        self.assertIn("devcontainers/ci", workflow)


if __name__ == "__main__":
    unittest.main()
