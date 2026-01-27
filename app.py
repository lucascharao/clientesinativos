from flask import Flask, render_template, request, jsonify
import pandas as pd
from datetime import datetime, timedelta
import os
import sys
from werkzeug.utils import secure_filename

# Adicionar diretório atual ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__)

# Usar /tmp na Vercel (serverless) ou uploads localmente
if os.environ.get('VERCEL'):
    app.config['UPLOAD_FOLDER'] = '/tmp'
else:
    app.config['UPLOAD_FOLDER'] = 'uploads'
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

def parse_date(date_str):
    """Converte string de data para datetime"""
    if pd.isna(date_str) or date_str == '' or date_str is None:
        return None

    try:
        # Tentar formato DD/MM/YYYY
        return pd.to_datetime(date_str, format='%d/%m/%Y', errors='coerce')
    except:
        try:
            # Tentar parsing automático
            return pd.to_datetime(date_str, errors='coerce')
        except:
            return None

def analyze_spreadsheet(file_path, filter_type, filter_value, include_no_date=False):
    """Analisa a planilha e retorna clientes sem compras no período"""

    # Ler planilha (header na linha 17, dados começam na linha 18)
    df = pd.read_excel(file_path, header=17)

    # Pegar a primeira linha como cabeçalhos reais
    headers = df.iloc[0].values
    df = df.iloc[1:].copy()
    df.columns = headers

    # Filtrar apenas colunas necessárias
    df = df[['CÓDIGO', 'NOME FANTASIA', 'ÚLTIMA VENDA', 'TOTAL']].copy()

    # Converter coluna ÚLTIMA VENDA para datetime
    df['ÚLTIMA VENDA'] = df['ÚLTIMA VENDA'].apply(parse_date)

    # Data de referência (hoje)
    today = datetime.now()

    # Aplicar filtro baseado no tipo
    if filter_type == 'days':
        range_value = filter_value

        # Processar faixa de dias
        if range_value == 'never':
            # Clientes que nunca compraram
            filtered_df = df[df['ÚLTIMA VENDA'].isna()].copy()
            filter_description = "nunca compraram"
        elif range_value.endswith('+'):
            # Faixa aberta (ex: 181+)
            min_days = int(range_value.replace('+', ''))
            date_max = today - timedelta(days=min_days)

            if include_no_date:
                filtered_df = df[
                    (df['ÚLTIMA VENDA'].isna()) |
                    ((df['ÚLTIMA VENDA'].notna()) & (df['ÚLTIMA VENDA'] <= date_max))
                ].copy()
                filter_description = f"inativos há {min_days}+ dias (incluindo sem data)"
            else:
                filtered_df = df[
                    (df['ÚLTIMA VENDA'].notna()) &
                    (df['ÚLTIMA VENDA'] <= date_max)
                ].copy()
                filter_description = f"inativos há {min_days}+ dias"
        else:
            # Faixa específica (ex: 0-30, 31-60)
            min_days, max_days = map(int, range_value.split('-'))
            date_min = today - timedelta(days=max_days)
            date_max = today - timedelta(days=min_days)

            if include_no_date:
                filtered_df = df[
                    (df['ÚLTIMA VENDA'].isna()) |
                    ((df['ÚLTIMA VENDA'].notna()) &
                     (df['ÚLTIMA VENDA'] >= date_min) &
                     (df['ÚLTIMA VENDA'] <= date_max))
                ].copy()
                filter_description = f"inativos há {min_days}-{max_days} dias (incluindo sem data)"
            else:
                filtered_df = df[
                    (df['ÚLTIMA VENDA'].notna()) &
                    (df['ÚLTIMA VENDA'] >= date_min) &
                    (df['ÚLTIMA VENDA'] <= date_max)
                ].copy()
                filter_description = f"inativos há {min_days}-{max_days} dias"

    elif filter_type == 'months':
        # Filtro por meses específicos do ano
        selected_months = [int(m) for m in filter_value.split(',')]

        # Clientes que não compraram nos meses selecionados
        # Primeiro, filtrar apenas clientes que têm data de última venda
        df_with_date = df[df['ÚLTIMA VENDA'].notna()].copy()

        # Extrair mês da última venda
        df_with_date['MÊS_VENDA'] = df_with_date['ÚLTIMA VENDA'].dt.month

        # Clientes que não compraram nos meses selecionados (ou nunca compraram)
        filtered_df = df[
            (df['ÚLTIMA VENDA'].isna()) |
            (~df['CÓDIGO'].isin(df_with_date[df_with_date['MÊS_VENDA'].isin(selected_months)]['CÓDIGO']))
        ].copy()

        month_names = {
            1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
            5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
            9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
        }
        selected_month_names = [month_names[m] for m in selected_months]
        filter_description = f"meses: {', '.join(selected_month_names)}"

    # Formatar resultado
    results = []
    for _, row in filtered_df.iterrows():
        ultima_venda = row['ÚLTIMA VENDA']
        if pd.isna(ultima_venda):
            ultima_venda_str = "Nunca comprou"
            dias_inativo = "-"
        else:
            ultima_venda_str = ultima_venda.strftime('%d/%m/%Y')
            dias_inativo = (today - ultima_venda).days

        results.append({
            'codigo': str(row['CÓDIGO']),
            'nome': str(row['NOME FANTASIA']),
            'ultima_venda': ultima_venda_str,
            'dias_inativo': dias_inativo,
            'total': f"R$ {float(row['TOTAL']) if pd.notna(row['TOTAL']) else 0:.2f}"
        })

    return {
        'total': len(results),
        'filter_description': filter_description,
        'clientes': results
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/favicon.ico')
def favicon():
    from flask import send_from_directory
    return send_from_directory(
        os.path.join(app.root_path, 'static', 'images'),
        'favicon.svg',
        mimetype='image/svg+xml'
    )

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        # Verificar se arquivo foi enviado
        if 'file' not in request.files:
            return jsonify({'error': 'Nenhum arquivo enviado'}), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({'error': 'Nenhum arquivo selecionado'}), 400

        # Verificar extensão
        if not file.filename.endswith(('.xlsx', '.xls')):
            return jsonify({'error': 'Apenas arquivos Excel (.xlsx, .xls) são permitidos'}), 400

        # Salvar arquivo
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Pegar parâmetros do filtro
        filter_type = request.form.get('filter_type')
        filter_value = request.form.get('filter_value')
        include_no_date = request.form.get('include_no_date', 'false') == 'true'

        # Analisar planilha
        result = analyze_spreadsheet(filepath, filter_type, filter_value, include_no_date)

        # Remover arquivo após análise
        os.remove(filepath)

        return jsonify(result)

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Erro detalhado: {error_details}")  # Log para debug
        return jsonify({
            'error': f'Erro ao processar arquivo: {str(e)}',
            'details': error_details if app.debug else None
        }), 500

if __name__ == '__main__':
    # Desenvolvimento local
    app.run(debug=True, port=5001)
else:
    # Produção (Vercel)
    app.config['DEBUG'] = False
