"""Both hardware runners share one pipeline and install their own toolchain."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
RUNNERS = ("cad", "electronics")
VERBS = ("list", "setup", "build", "generate", "check", "help")


class SharedPipelineTest(unittest.TestCase):
    def test_both_runners_use_the_same_pipeline(self) -> None:
        library = (REPO / "tools" / "lib" / "pipeline.sh").read_text()
        for verb in VERBS:
            self.assertIn(verb, library, verb)
        for name in RUNNERS:
            with self.subTest(runner=name):
                tool = (REPO / "tools" / name).read_text()
                self.assertIn("source tools/lib/pipeline.sh", tool)
                self.assertIn("pipeline_main", tool)
                # The pipeline owns discovery and dispatch; a runner only
                # supplies the parts that genuinely differ.
                for hook in ("setup_toolchain", "run_generator", "run_checks"):
                    self.assertIn(f"{hook}()", tool, hook)
                self.assertNotIn("generation-order", tool)

    def test_runners_expose_an_identical_verb_set(self) -> None:
        library = (REPO / "tools" / "lib" / "pipeline.sh").read_text()
        dispatch = library.split("pipeline_main()", 1)[1]
        for verb in VERBS:
            self.assertIn(verb, dispatch, verb)

    def test_each_domain_keeps_generated_output_in_one_folder(self) -> None:
        for name in RUNNERS:
            with self.subTest(runner=name):
                tool = (REPO / "tools" / name).read_text()
                self.assertIn('"${domain_dir}/generated"', tool)
                generated = REPO / "hardware" / name / "generated"
                self.assertTrue(generated.is_dir(), str(generated))
                self.assertIn(
                    "do not edit", (generated / "README.md").read_text().lower()
                )


class ElectronicsToolingTest(unittest.TestCase):
    def test_runner_bootstraps_a_local_venv(self) -> None:
        tool = (REPO / "tools" / "electronics").read_text()
        self.assertIn(".cache/electronics", tool)
        self.assertIn("requirements.txt", tool)
        requirements = REPO / "hardware" / "electronics" / "requirements.txt"
        self.assertIn("schemdraw", requirements.read_text())
        self.assertNotIn("kicad", tool.lower())
        self.assertNotIn("docker", tool.lower())

    def test_cad_runner_caches_blender_instead_of_installing_it(self) -> None:
        tool = (REPO / "tools" / "cad").read_text()
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
        # Schemdraw needs a virtual environment; Blender is a downloaded
        # tarball that links against X11 and GL even in background mode.
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
    def test_ci_runs_the_same_check_verbs_as_a_developer(self) -> None:
        workflow = (REPO / ".github" / "workflows" / "ci.yml").read_text()
        for name in RUNNERS:
            self.assertIn(f"./tools/{name} setup", workflow, name)
            self.assertIn(f"./tools/{name} check", workflow, name)
            self.assertIn(f"hardware/{name}/generated", workflow, name)
        # CAD generation is the expensive half, so prove it still runs.
        self.assertIn("./tools/cad build", workflow)
        self.assertIn("devcontainers/ci", workflow)


if __name__ == "__main__":
    unittest.main()
