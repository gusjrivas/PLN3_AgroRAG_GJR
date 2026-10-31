#!/bin/sh

set -eu

preflight_script="${1:?indique el preflight}"
fixture_dir="$(CDPATH= cd -- "$(dirname -- "$0")/fixtures/preflight" && pwd)"
test_dir="$(mktemp -d)"
trap 'rm -rf "$test_dir"' EXIT HUP INT TERM

secrets_dir="$test_dir/secrets"
mkdir "$secrets_dir"
chmod 700 "$secrets_dir"
for secret_name in reader_key openai_api_key gateway_auth
do
    printf 'sentinel-%s\n' "$secret_name" > "$secrets_dir/$secret_name"
    chmod 600 "$secrets_dir/$secret_name"
done
chown 10001:10001 "$secrets_dir/reader_key" "$secrets_dir/openai_api_key"
chown 10002:10002 "$secrets_dir/gateway_auth"

: > "$test_dir/compose.yaml"
: > "$test_dir/compose.production.yaml"
evidence_file="$test_dir/preflight.env"
rejected_evidence_file="$test_dir/rejected-preflight.env"
rejected_error_file="$test_dir/rejected-preflight.stderr"
digest='aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
commit='bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb'

run_preflight() {
    output_file="$1"
    (
        cd "$test_dir"
        PATH="$fixture_dir:$PATH" \
        AGRO_API_IMAGE="ghcr.io/example/agrorag/api@sha256:$digest" \
        AGRO_UI_IMAGE="ghcr.io/example/agrorag/ui@sha256:$digest" \
        AGRO_GATEWAY_IMAGE="ghcr.io/example/agrorag/gateway@sha256:$digest" \
        AGRO_CATALOGUE_VOLUME='agrorag_catalogue_staging' \
        AGRO_DOMAIN='sentinel.example.org' \
        AGRO_OPENAI_MODEL='sentinel-model' \
        AGRO_SECRETS_DIR="$secrets_dir" \
        AGRO_RELEASE_VERSION='2.0.0-rc.1' \
        AGRO_COMMIT_SHA="$commit" \
        AGRO_DEPLOYMENT_ID='staging-a' \
        sh "$preflight_script" > "$output_file"
    )
}

assert_rejected_owner() {
    secret_name="$1"
    wrong_owner="$2"
    expected_owner="$3"
    chown "$wrong_owner" "$secrets_dir/$secret_name"
    if run_preflight "$rejected_evidence_file" 2> "$rejected_error_file"
    then
        printf 'preflight accepted %s with the wrong runtime owner\n' "$secret_name" >&2
        exit 1
    fi
    grep -Fx "single-host preflight blocked: $secret_name debe pertenecer a $expected_owner" \
        "$rejected_error_file"
    if grep -Eq 'sentinel-(reader|openai|gateway)' "$rejected_error_file"
    then
        printf 'preflight rejection leaked a forbidden value\n' >&2
        exit 1
    fi
    chown "$expected_owner" "$secrets_dir/$secret_name"
}

assert_rejected_owner reader_key 10002:10002 10001:10001
assert_rejected_owner openai_api_key 10002:10002 10001:10001
assert_rejected_owner gateway_auth 10001:10001 10002:10002
run_preflight "$evidence_file"

grep -Fx 'schema=agrorag.single-host-preflight.v1' "$evidence_file"
grep -Fx 'status=approved' "$evidence_file"
grep -Fx 'deployment_id=staging-a' "$evidence_file"
grep -Fx 'release=2.0.0-rc.1' "$evidence_file"
grep -Fx "commit=$commit" "$evidence_file"
grep -Eq '^checked_at_utc=[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$' "$evidence_file"
grep -Eq '^duration_seconds=[0-9]+$' "$evidence_file"
grep -Eq '^cpu_count=[1-9][0-9]*$' "$evidence_file"
grep -Eq '^memory_bytes=[1-9][0-9]*$' "$evidence_file"
grep -Fx "api_image=ghcr.io/example/agrorag/api@sha256:$digest" "$evidence_file"
grep -Fx "ui_image=ghcr.io/example/agrorag/ui@sha256:$digest" "$evidence_file"
grep -Fx "gateway_image=ghcr.io/example/agrorag/gateway@sha256:$digest" "$evidence_file"

if grep -Eq 'sentinel\.(example\.org|model)|sentinel-(reader|openai|gateway)|secrets_dir=' "$evidence_file"
then
    printf 'preflight contract leaked a forbidden value\n' >&2
    exit 1
fi
