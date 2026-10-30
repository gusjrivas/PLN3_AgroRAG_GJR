#!/bin/sh

set -eu

fail() {
    printf 'single-host preflight blocked: %s\n' "$1" >&2
    exit 1
}

require_value() {
    variable="$1"
    value="$(printenv "$variable" 2>/dev/null || true)"
    [ -n "$value" ] || fail "$variable no está definido"
}

[ "$(uname -s)" = "Linux" ] || fail "se requiere un host Linux"
command -v docker >/dev/null 2>&1 || fail "Docker Engine no está instalado"
command -v stat >/dev/null 2>&1 || fail "stat no está disponible"
command -v grep >/dev/null 2>&1 || fail "grep no está disponible"
command -v printenv >/dev/null 2>&1 || fail "printenv no está disponible"
command -v date >/dev/null 2>&1 || fail "date no está disponible"
command -v getconf >/dev/null 2>&1 || fail "getconf no está disponible"
command -v awk >/dev/null 2>&1 || fail "awk no está disponible"
started_at_epoch="$(date +%s)"
docker version >/dev/null 2>&1 || fail "Docker Engine no responde"
docker compose version >/dev/null 2>&1 || fail "Docker Compose Plugin no responde"

for variable in \
    AGRO_API_IMAGE \
    AGRO_UI_IMAGE \
    AGRO_GATEWAY_IMAGE \
    AGRO_CATALOGUE_VOLUME \
    AGRO_DOMAIN \
    AGRO_OPENAI_MODEL \
    AGRO_SECRETS_DIR \
    AGRO_RELEASE_VERSION \
    AGRO_COMMIT_SHA \
    AGRO_DEPLOYMENT_ID
do
    require_value "$variable"
done

printf '%s' "$AGRO_COMMIT_SHA" | grep -Eq '^[0-9a-f]{40}$' \
    || fail "AGRO_COMMIT_SHA debe ser un SHA completo"
printf '%s' "$AGRO_RELEASE_VERSION" \
    | grep -Eq '^[0-9]+\.[0-9]+\.[0-9]+([.-][0-9A-Za-z.-]+)?$' \
    || fail "AGRO_RELEASE_VERSION debe ser semver"
printf '%s' "$AGRO_DOMAIN" | grep -Eq '^[A-Za-z0-9.-]+$' \
    || fail "AGRO_DOMAIN no es un hostname válido"
printf '%s' "$AGRO_CATALOGUE_VOLUME" | grep -Eq '^[A-Za-z0-9_.-]+$' \
    || fail "AGRO_CATALOGUE_VOLUME no es un nombre seguro"
printf '%s' "$AGRO_DEPLOYMENT_ID" | grep -Eq '^[A-Za-z0-9_.-]+$' \
    || fail "AGRO_DEPLOYMENT_ID no es un identificador seguro"

case "$AGRO_SECRETS_DIR" in
    /*) ;;
    *) fail "AGRO_SECRETS_DIR debe ser absoluto" ;;
esac
[ -d "$AGRO_SECRETS_DIR" ] || fail "el directorio de secretos no existe"
[ ! -L "$AGRO_SECRETS_DIR" ] || fail "el directorio de secretos no puede ser symlink"
secret_dir_mode="$(stat -c '%a' -- "$AGRO_SECRETS_DIR")"
[ "$secret_dir_mode" = "700" ] || fail "el directorio de secretos debe tener modo 0700"

for secret_name in reader_key openai_api_key gateway_auth
do
    secret_path="$AGRO_SECRETS_DIR/$secret_name"
    [ -f "$secret_path" ] || fail "falta el archivo secreto $secret_name"
    [ ! -L "$secret_path" ] || fail "$secret_name no puede ser symlink"
    [ -s "$secret_path" ] || fail "$secret_name está vacío"
    secret_mode="$(stat -c '%a' -- "$secret_path")"
    case "$secret_mode" in
        400|600) ;;
        *) fail "$secret_name debe tener modo 0400 o 0600" ;;
    esac
done

check_image() {
    variable="$1"
    expected_user="$2"
    image="$(printenv "$variable")"
    printf '%s' "$image" | grep -Eq '^[^[:space:]@]+@sha256:[0-9a-f]{64}$' \
        || fail "$variable debe usar una referencia inmutable por digest"
    docker image inspect "$image" >/dev/null 2>&1 \
        || fail "$variable todavía no fue descargada"
    runtime_user="$(docker image inspect --format '{{.Config.User}}' "$image")"
    [ "$runtime_user" = "$expected_user" ] || fail "$variable tiene un usuario inesperado"
    revision="$(docker image inspect \
        --format '{{index .Config.Labels "org.opencontainers.image.revision"}}' "$image")"
    [ "$revision" = "$AGRO_COMMIT_SHA" ] || fail "$variable no pertenece al commit esperado"
}

check_image AGRO_API_IMAGE '10001:10001'
check_image AGRO_UI_IMAGE '10001:10001'
check_image AGRO_GATEWAY_IMAGE '10002:10002'

docker volume inspect "$AGRO_CATALOGUE_VOLUME" >/dev/null 2>&1 \
    || fail "el volumen externo de catálogo no existe"
[ -r compose.yaml ] || fail "falta compose.yaml"
[ -r compose.production.yaml ] || fail "falta compose.production.yaml"
docker compose -f compose.yaml -f compose.production.yaml config --quiet \
    || fail "la configuración Compose productiva es inválida"

engine_version="$(docker version --format '{{.Server.Version}}')"
compose_version="$(docker compose version --short)"
checked_at_utc="$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
finished_at_epoch="$(date +%s)"
duration_seconds="$((finished_at_epoch - started_at_epoch))"
kernel="$(uname -r)"
architecture="$(uname -m)"
cpu_count="$(getconf _NPROCESSORS_ONLN)"
printf '%s' "$cpu_count" | grep -Eq '^[1-9][0-9]*$' \
    || fail "no se pudo determinar la cantidad de CPU"
memory_kib="$(awk '/^MemTotal:/ {print $2; exit}' /proc/meminfo)"
printf '%s' "$memory_kib" | grep -Eq '^[1-9][0-9]*$' \
    || fail "no se pudo determinar la memoria"
memory_bytes="$((memory_kib * 1024))"
printf 'schema=agrorag.single-host-preflight.v1\n'
printf 'status=approved\n'
printf 'checked_at_utc=%s\n' "$checked_at_utc"
printf 'duration_seconds=%s\n' "$duration_seconds"
printf 'deployment_id=%s\n' "$AGRO_DEPLOYMENT_ID"
printf 'kernel=%s\n' "$kernel"
printf 'architecture=%s\n' "$architecture"
printf 'cpu_count=%s\n' "$cpu_count"
printf 'memory_bytes=%s\n' "$memory_bytes"
printf 'engine_version=%s\n' "$engine_version"
printf 'compose_version=%s\n' "$compose_version"
printf 'release=%s\n' "$AGRO_RELEASE_VERSION"
printf 'commit=%s\n' "$AGRO_COMMIT_SHA"
printf 'catalogue_volume=%s\n' "$AGRO_CATALOGUE_VOLUME"
printf 'api_image=%s\n' "$AGRO_API_IMAGE"
printf 'ui_image=%s\n' "$AGRO_UI_IMAGE"
printf 'gateway_image=%s\n' "$AGRO_GATEWAY_IMAGE"
