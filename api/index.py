import sys
import os

# Adicionar diretório pai ao path para importar app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app

# Vercel precisa da variável 'app' exportada
# Desabilitar modo debug em produção
app.config['DEBUG'] = False
