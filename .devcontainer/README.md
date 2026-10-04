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

- Node.js 22, Bun 1.4, and the [Pi coding agent](https://pi.dev/), installed
  during container creation;
- pinned Claude Code and Herdr, plus Codex, provider status hooks and the Reviewr
  panel; the optional [agent team](../.agents/team/README.md) defaults to Claude
  Code for all roles;
- a Bun-managed `.pi` TypeScript project with pinned Pi API types, workspace
  IntelliSense, and `bun run --cwd .pi check` validation for project extensions;
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

Container creation configures the repository pre-commit hook, installs Pi/Codex,
and configures Herdr integrations without starting models. Claude Code is installed
in the image. Separate `chess-claude`, `chess-codex` and `chess-herdr` volumes keep
provider credentials and runtime configuration across rebuilds. Run
`claude auth login` inside the container (or forward `CLAUDE_CODE_OAUTH_TOKEN`).
Accept workspace trust manually. Host API credentials may select API billing;
unset `ANTHROPIC_API_KEY` before opening the container for subscription-only use.
No host credential directories are mounted and no secrets are copied into the image.
Credentials for every built-in Pi API-key provider are forwarded from matching
host environment variables without writing secrets to the repository. Pi's
`~/.pi/agent` directory uses the persistent `chess-pi-agent` Docker volume, so
credentials created with `pi` and `/login` survive container rebuilds. The
`pi-worktrees` package stores managed worktrees in the persistent
`chess-pi-worktrees` volume, preserving uncommitted agent work across container
recreation. Export provider variables on the host before opening the container; see Pi's
[provider documentation](https://github.com/earendil-works/pi-mono/blob/main/packages/coding-agent/docs/providers.md)
for the supported names and cloud-provider settings.

Host-only fallback downloads (`.cache/blender`, `.cache/pcb`) exist for people
who run the tools outside the container.

After create:

```sh
bun run --cwd .pi check    # type-check project Pi extensions
pi                         # start the coding agent; use /login for OAuth
claude auth login          # persistent Claude login; no automatic sign-in
just agents-doctor         # tools/login check, no model request
just agents lead developer # portable Rust team (eight engineering roles with just agents)
just agents lead hardware-engineer mechanical-engineer # circuit/enclosure team
just agents-test           # offline launcher/configuration tests
just pcb                    # test, then generate PCB review output
just cad                    # test, then generate CAD output
just quality                # lint and format-check every package
just firmware-binary        # link the firmware for AArch64
just test                   # test every package
just check                  # all domains, sequentially
```

Host-specific device access and hardware flashing policy do not belong in the
portable baseline container configuration.
