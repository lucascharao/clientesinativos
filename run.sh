#!/bin/bash

# Script para iniciar o servidor

echo "🚀 Iniciando Sistema de Análise de Clientes - Mutumilk"
echo ""

# Ativar ambiente virtual
source venv/bin/activate

# Iniciar servidor Flask
echo "📊 Servidor rodando em: http://localhost:5001"
echo "Pressione Ctrl+C para parar"
echo ""

python app.py
