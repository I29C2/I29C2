#!/usr/bin/env bash
# scripts/check_health.sh
# BetBot AI – Service Health Checker
#
# Waits for all Docker Compose services to become healthy,
# then verifies the backend API and database connectivity.
#
# Usage:
#   chmod +x scripts/check_health.sh
#   ./scripts/check_health.sh
#   ./scripts/check_health.sh --timeout 120

set -euo pipefail

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
REDIS_HOST="${REDIS_HOST:-localhost}"
REDIS_PORT="${REDIS_PORT:-6379}"
MAX_WAIT="${1:-60}"        # seconds to wait (override with first arg or --timeout)
POLL_INTERVAL=3

# Parse --timeout flag
while [[ $# -gt 0 ]]; do
    case "$1" in
        --timeout)
            MAX_WAIT="$2"
            shift 2
            ;;
        *)
            shift
            ;;
    esac
done

# ---------------------------------------------------------------------------
# Colour helpers
# ---------------------------------------------------------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'   # No colour

info()    { echo -e "${CYAN}[INFO]${NC}  $*"; }
success() { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error()   { echo -e "${RED}[FAIL]${NC}  $*"; }

# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------
check_command() {
    command -v "$1" &>/dev/null
}

wait_for_tcp() {
    local host="$1" port="$2" label="$3"
    local elapsed=0
    info "Waiting for $label ($host:$port)..."
    while ! (echo > /dev/tcp/"$host"/"$port") &>/dev/null; do
        if [[ $elapsed -ge $MAX_WAIT ]]; then
            error "$label did not become reachable within ${MAX_WAIT}s"
            return 1
        fi
        sleep "$POLL_INTERVAL"
        elapsed=$(( elapsed + POLL_INTERVAL ))
        echo -n "."
    done
    echo ""
    success "$label is reachable at $host:$port"
    return 0
}

wait_for_http() {
    local url="$1" label="$2"
    local elapsed=0
    info "Waiting for $label ($url)..."
    while ! curl -sf "$url" -o /dev/null 2>/dev/null; do
        if [[ $elapsed -ge $MAX_WAIT ]]; then
            error "$label did not respond within ${MAX_WAIT}s"
            return 1
        fi
        sleep "$POLL_INTERVAL"
        elapsed=$(( elapsed + POLL_INTERVAL ))
        echo -n "."
    done
    echo ""
    success "$label is responding at $url"
    return 0
}

# ---------------------------------------------------------------------------
# Docker Compose container health
# ---------------------------------------------------------------------------
check_docker_compose_health() {
    if ! check_command docker; then
        warn "Docker not found – skipping container health checks."
        return 0
    fi

    info "Checking Docker Compose service health..."
    local services=("betbot_postgres" "betbot_redis" "betbot_backend")
    local all_healthy=true

    for service in "${services[@]}"; do
        local state
        state=$(docker inspect --format='{{.State.Health.Status}}' "$service" 2>/dev/null || echo "not_found")
        case "$state" in
            healthy)
                success "Container $service is healthy"
                ;;
            not_found)
                warn "Container $service not found (may not be running)"
                all_healthy=false
                ;;
            starting)
                warn "Container $service is still starting..."
                all_healthy=false
                ;;
            unhealthy)
                error "Container $service is UNHEALTHY"
                all_healthy=false
                ;;
            *)
                warn "Container $service status: $state"
                ;;
        esac
    done

    if [[ "$all_healthy" == "false" ]]; then
        return 1
    fi
    return 0
}

# ---------------------------------------------------------------------------
# Backend API health check
# ---------------------------------------------------------------------------
check_backend_health() {
    info "Checking backend /health endpoint..."
    local response
    response=$(curl -sf "${BACKEND_URL}/health" 2>/dev/null) || {
        error "Backend /health endpoint unreachable at ${BACKEND_URL}/health"
        return 1
    }

    # Validate JSON contains status=ok
    if echo "$response" | grep -q '"status"' && echo "$response" | grep -q '"ok"'; then
        success "Backend health check passed: $response"
    else
        warn "Backend responded but status is not 'ok': $response"
    fi
    return 0
}

# ---------------------------------------------------------------------------
# API docs reachability
# ---------------------------------------------------------------------------
check_api_docs() {
    info "Checking Swagger UI (/docs)..."
    if curl -sf "${BACKEND_URL}/docs" -o /dev/null 2>/dev/null; then
        success "Swagger UI is accessible at ${BACKEND_URL}/docs"
    else
        warn "Swagger UI not accessible (may be disabled in production)"
    fi
}

# ---------------------------------------------------------------------------
# Redis connectivity via redis-cli
# ---------------------------------------------------------------------------
check_redis() {
    if check_command redis-cli; then
        info "Checking Redis..."
        local pong
        pong=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" ping 2>/dev/null || echo "FAILED")
        if [[ "$pong" == "PONG" ]]; then
            success "Redis is responding (PONG received)"
        else
            error "Redis ping failed (got: $pong)"
            return 1
        fi
    else
        # Fall back to TCP check
        wait_for_tcp "$REDIS_HOST" "$REDIS_PORT" "Redis"
    fi
    return 0
}

# ---------------------------------------------------------------------------
# PostgreSQL connectivity via psql or TCP
# ---------------------------------------------------------------------------
check_postgres() {
    if check_command psql; then
        info "Checking PostgreSQL..."
        if PGPASSWORD="${POSTGRES_PASSWORD:-betbot_secret}" \
            psql -h "$DB_HOST" -p "$DB_PORT" \
                 -U "${POSTGRES_USER:-betbot}" \
                 -d "${POSTGRES_DB:-betbot}" \
                 -c "SELECT 1;" &>/dev/null; then
            success "PostgreSQL is accepting connections"
        else
            error "PostgreSQL connection failed"
            return 1
        fi
    else
        wait_for_tcp "$DB_HOST" "$DB_PORT" "PostgreSQL"
    fi
    return 0
}

# ---------------------------------------------------------------------------
# Print summary report
# ---------------------------------------------------------------------------
print_report() {
    local exit_code="$1"
    echo ""
    echo "======================================================"
    echo "           BetBot AI – Health Status Report           "
    echo "======================================================"
    echo "  Timestamp  : $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
    echo "  Backend URL: ${BACKEND_URL}"
    echo "  DB Host    : ${DB_HOST}:${DB_PORT}"
    echo "  Redis Host : ${REDIS_HOST}:${REDIS_PORT}"
    echo "------------------------------------------------------"
    if [[ "$exit_code" -eq 0 ]]; then
        echo -e "  Overall    : ${GREEN}ALL SYSTEMS OPERATIONAL${NC}"
    else
        echo -e "  Overall    : ${RED}ONE OR MORE CHECKS FAILED${NC}"
    fi
    echo "======================================================"
    echo ""
    echo "  API Docs : ${BACKEND_URL}/docs"
    echo "  Frontend : http://localhost:3000"
    echo ""
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
main() {
    echo ""
    echo "======================================================"
    echo "   BetBot AI – Service Health Checker"
    echo "   Max wait time: ${MAX_WAIT}s per service"
    echo "======================================================"
    echo ""

    local overall_exit=0

    # 1. TCP connectivity
    wait_for_tcp "$DB_HOST" "$DB_PORT" "PostgreSQL" || overall_exit=1
    wait_for_tcp "$REDIS_HOST" "$REDIS_PORT" "Redis"     || overall_exit=1
    wait_for_http "${BACKEND_URL}/health" "Backend API"  || overall_exit=1

    # 2. Docker container health (optional – only runs if docker is present)
    check_docker_compose_health || overall_exit=1

    # 3. Deep service checks
    check_backend_health  || overall_exit=1
    check_redis           || overall_exit=1
    check_postgres        || overall_exit=1

    # 4. API docs
    check_api_docs

    print_report "$overall_exit"
    exit "$overall_exit"
}

main "$@"
