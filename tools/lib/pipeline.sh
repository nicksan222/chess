# Shared project listing for the hardware generators.
#
# Not a user-facing command. Both runners source this so generate walks
# projects/*/generate.py in the same generation-order.

list_projects() {
    local generator order order_file lines
    lines="$(
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
    )"
    if [[ -z "${lines}" ]]; then
        printf 'No project generators found in %s/projects.\n' "${domain_dir}" >&2
        return 1
    fi
    printf '%s\n' "${lines}" | LC_ALL=C sort | cut -f2-
}
