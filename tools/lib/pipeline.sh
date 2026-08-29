# Shared generation pipeline for the hardware domains.
#
# hardware/cad and hardware/electronics are the same shape: a directory of
# projects, each owning one generate.py, run in an order the projects declare
# themselves. This library owns that shape so both runners stay identical and
# only the parts that genuinely differ -- the toolchain and how a generator is
# executed -- live in the runner itself.
#
# A runner sets `domain` and `domain_dir`, then defines:
#   setup_toolchain   prepare interpreters and dependencies (idempotent)
#   run_generator     execute one generate.py
#   run_checks        the domain's own test suite
# and optionally:
#   clean_artefacts   remove generated files before a build
#   post_build        run after every generator has succeeded

pipeline_usage() {
    cat <<EOF
Usage: ./tools/${domain} <command>

Commands:
  list      Show project generate.py files in dependency order.
  setup     Install the toolchain only, without generating.
  build     Run every project generator.
  generate  Same as build.
  check     Run the ${domain} checks.
  help      Show this message.

Projects live in ${domain_dir}/projects. Adding one is adding a directory with
a generate.py; the runner discovers it. A project may declare a numeric
generation-order file when it depends on another project's output.
EOF
}

pipeline_discover() {
    local generator order order_file
    while IFS= read -r -d '' generator; do
        order_file="$(dirname -- "${generator}")/generation-order"
        order=100
        if [[ -f "${order_file}" ]]; then
            IFS= read -r order < "${order_file}" || true
        fi
        if [[ ! "${order}" =~ ^[0-9]+$ ]]; then
            printf 'Invalid generation order in %s: %s\n' \
                "${order_file}" "${order}" >&2
            return 1
        fi
        printf '%09d\t%s\n' "${order}" "${generator}"
    done < <(find "${domain_dir}/projects" -type f -name generate.py -print0)
}

# Generators in run order, one "<order><tab><path>" line each.
pipeline_manifest() {
    local manifest
    manifest="$(mktemp)"
    pipeline_discover | LC_ALL=C sort > "${manifest}"
    if [[ ! -s "${manifest}" ]]; then
        rm -f "${manifest}"
        printf 'No %s project generators found.\n' "${domain}" >&2
        return 1
    fi
    cat "${manifest}"
    rm -f "${manifest}"
}

pipeline_list() {
    local manifest
    manifest="$(pipeline_manifest)"
    printf '%s\n' "${manifest}" | cut -f2-
}

pipeline_build() {
    local manifest order generator
    manifest="$(pipeline_manifest)"
    setup_toolchain
    if declare -F clean_artefacts > /dev/null; then
        clean_artefacts
    fi
    while IFS=$'\t' read -r order generator; do
        printf '\n==> Generate %s\n' "$(dirname -- "${generator}")"
        run_generator "${generator}"
    done <<< "${manifest}"
    if declare -F post_build > /dev/null; then
        post_build
    fi
}

pipeline_main() {
    local command_name="${1:-}"
    shift || true
    case "${command_name}" in
        list) pipeline_list ;;
        setup) setup_toolchain ;;
        build | generate) pipeline_build ;;
        check) run_checks "$@" ;;
        help | -h | --help | "") pipeline_usage ;;
        *)
            printf 'error: unknown %s command: %s\n' "${domain}" "${command_name}" >&2
            pipeline_usage >&2
            exit 2
            ;;
    esac
}
