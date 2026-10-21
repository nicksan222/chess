# Development container

This directory owns the reproducible VS Code / Cursor development environment.
The Dockerfile installs every toolchain the jobs need: Blender, KiCad 9, Ruff,
and the Rust components. Open the repository and run **Dev Containers:
Reopen in Container**, or drive it from the
[`devcontainer` CLI](https://github.com/devcontainers/cli):

```sh
devcontainer up --workspace-folder .
devcontainer exec --workspace-folder . just pcb
devcontainer exec --workspace-folder . just cad
devcontainer exec --workspace-folder . just quality
devcontainer exec --workspace-folder . just test
devcontainer exec --workspace-folder . just check
```

The image provides:

- Node.js 22 and the agent harnesses: pinned Claude Code in the image and pinned
  Codex installed during container creation (creation fails if either is
  missing). Both read the shared [agent tooling](../.agents/README.md);
- stable Rust with `rustfmt`, Clippy, Just, and the AArch64 GNU target/linker;
- Ruff for CAD, PCB, and shared Python;
- KiCad 9 with `kicad-cli` and `pcbnew`;
- a checksum-verified Blender at `/opt/blender`;
- X11/GL/EGL, Mesa, Xvfb, and `xauth` so headless Blender can render;
- an in-container Docker daemon for Yocto metadata validation, plus native build,
  USB, and udev development libraries;
- rust-src, Pylance, YAML, ShellCheck, Docker, Cargo.toml, TOML, LLDB,
  Markdown, and GitHub Actions editor integration.

CI prebuilds this image, pushes it to GHCR, then runs Python, CAD, PCB, and Rust as
parallel `devcontainer exec` jobs against that digest. Subsequent
prebuilds reuse the image layers when the Dockerfile is unchanged.

Container creation configures the repository pre-commit hook and installs Codex
without starting a model. Separate `chess-claude` and `chess-codex` volumes keep provider
credentials and runtime configuration across rebuilds. Run `claude auth login`
(or forward `CLAUDE_CODE_OAUTH_TOKEN`) and `codex login` inside the container.
Accept workspace trust manually. Host API credentials may select API billing;
unset `ANTHROPIC_API_KEY` before opening the container for subscription-only use.
No host credential directories are mounted and no secrets are copied into the image.

Host-only fallback downloads (`.cache/blender`, `.cache/pcb`) exist for people
who run the tools outside the container.

After create, the first VS Code terminal greets you with a 👋 welcome: toolchain
versions, which agents are signed in, and the commands below. Bring it back with
`just welcome`.

```sh
just welcome                # toolchain/login status and starter commands
claude auth login           # persistent Claude login; no automatic sign-in
codex login                 # persistent Codex login
just pcb                    # test, then generate PCB review output
just cad                    # test, then generate CAD output
just quality                # lint and format-check every package
just firmware-binary        # link the firmware for AArch64
just test                   # test every package
just check                  # all domains, sequentially
```

Host-specific device access and hardware flashing policy do not belong in the
portable baseline container configuration.
