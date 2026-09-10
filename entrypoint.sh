#!/bin/bash
set -e

# Cria os diretórios necessários no volume montado caso ainda não existam
mkdir -p /app/storage/uploads /app/storage/converted /app/storage/temp 2>/dev/null || true

# Ajusta propriedade e permissões completas para o appuser
chown -R appuser:appuser /app/storage 2>/dev/null || true
chmod -R 777 /app/storage 2>/dev/null || true

# Executa o comando principal utilizando gosu para segurança como usuário não-root
if command -v gosu >/dev/null 2>&1; then
    exec gosu appuser "$@"
else
    exec "$@"
fi
