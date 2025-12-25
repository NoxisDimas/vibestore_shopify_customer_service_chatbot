#!/bin/bash
# ============================================
# Docker Swarm Secrets Setup Script
# ============================================
# This script helps you create Docker Swarm secrets
# Run this BEFORE deploying the stack
#
# Usage: ./setup-secrets.sh
# ============================================

set -e

echo "🔐 Docker Swarm Secrets Setup"
echo "=============================="
echo ""

# Check if Docker Swarm is initialized
if ! docker info 2>/dev/null | grep -q "Swarm: active"; then
    echo "⚠️  Docker Swarm is not initialized."
    read -p "Initialize Docker Swarm now? (y/n): " init_swarm
    if [ "$init_swarm" = "y" ]; then
        docker swarm init
        echo "✅ Docker Swarm initialized"
    else
        echo "❌ Please initialize Docker Swarm first: docker swarm init"
        exit 1
    fi
fi

echo ""
echo "📝 Please enter your secrets (input will be hidden):"
echo ""

# Function to create secret
create_secret() {
    local name=$1
    local description=$2
    local required=$3
    
    # Check if secret already exists
    if docker secret ls | grep -q "$name"; then
        echo "  ⚠️  Secret '$name' already exists. Skipping."
        return
    fi
    
    read -sp "  $description: " value
    echo ""
    
    if [ -z "$value" ] && [ "$required" = "true" ]; then
        echo "  ❌ $name is required!"
        exit 1
    fi
    
    if [ -n "$value" ]; then
        echo "$value" | docker secret create "$name" -
        echo "  ✅ Created secret: $name"
    else
        echo "  ⏭️  Skipped: $name (optional)"
    fi
}

echo "=== Required Secrets ==="
create_secret "api_key" "API Key (for authentication)" "true"
create_secret "postgres_password" "PostgreSQL Password" "true"
create_secret "neo4j_password" "Neo4j Password" "true"

echo ""
echo "=== LLM Provider Secrets (at least one required) ==="
create_secret "openai_api_key" "OpenAI API Key" "false"
create_secret "groq_api_key" "Groq API Key" "false"

echo ""
echo "=== Optional Secrets ==="
create_secret "langsmith_api_key" "LangSmith API Key (for tracing)" "false"
create_secret "qdrant_api_key" "Qdrant API Key (if using cloud)" "false"
create_secret "mem0_api_key" "Mem0 API Key" "false"
create_secret "whatsapp_access_token" "WhatsApp Access Token" "false"
create_secret "telegram_bot_token" "Telegram Bot Token" "false"

# Create postgres_uri from password
echo ""
read -sp "Enter PostgreSQL password again to create postgres_uri: " pg_pass
echo ""
if [ -n "$pg_pass" ]; then
    echo "postgresql://postgres:${pg_pass}@postgres:5432/agent_db" | docker secret create postgres_uri -
    echo "  ✅ Created secret: postgres_uri"
fi

echo ""
echo "=============================="
echo "✅ All secrets created!"
echo ""
echo "📋 List of secrets:"
docker secret ls
echo ""
echo "🚀 To deploy the stack, run:"
echo "   cd infra"
echo "   docker stack deploy -c docker-compose.swarm.yml cs-agent"
echo ""
