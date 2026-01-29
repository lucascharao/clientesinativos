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

def read_and_parse_spreadsheet(file_path):
    """Lê a planilha, detecta cabeçalho dinamicamente e faz parse das datas"""
    # Buscar dinamicamente a linha de cabeçalho
    df_temp = pd.read_excel(file_path, header=None, nrows=50)
    
    header_row_index = 0
    header_found = False
    
    for index, row in df_temp.iterrows():
        # Converter valores para string e uppercase para verificar
        row_values = [str(val).upper().strip() for val in row.values]
        row_set = set(row_values)
        
        # Verificar se encontra colunas chave
        if 'CÓDIGO' in row_set and 'NOME FANTASIA' in row_set:
            header_row_index = index
            header_found = True
            break
            
    # Ler planilha com o cabeçalho correto
    df = pd.read_excel(file_path, header=header_row_index)
    
    # Normalizar nomes das colunas para uppercase e strip
    df.columns = [str(col).upper().strip() for col in df.columns]

    # Verificar existência das colunas necessárias
    required = ['CÓDIGO', 'NOME FANTASIA', 'ÚLTIMA VENDA', 'TOTAL']
    available = df.columns.tolist()
    
    # Se não encontrar todas, tentar fallback ou apenas avisar
    # Para simplificar, vamos assumir que se achou o header, as colunas estão lá ou parciais.
    # Mas vamos filtrar apenas o que existe para não dar erro
    cols_to_use = [c for c in required if c in available]
    df = df[cols_to_use].copy()
    
    # Garantir que TOTAIS seja numérico
    if 'TOTAL' in df.columns:
         df['TOTAL'] = pd.to_numeric(df['TOTAL'], errors='coerce').fillna(0)

    # Converter coluna ÚLTIMA VENDA para datetime
    if 'ÚLTIMA VENDA' in df.columns:
        df['ÚLTIMA VENDA'] = df['ÚLTIMA VENDA'].apply(parse_date)
        
    return df

def preview_spreadsheet(file_path):
    """Gera metadados e estatísticas da planilha para o dashboard"""
    df = read_and_parse_spreadsheet(file_path)
    
    total_clientes = len(df)
    total_valor = df['TOTAL'].sum() if 'TOTAL' in df.columns else 0
    
    # Estatísticas de data
    first_sale = None
    last_sale = None
    never_bought_count = 0
    
    if 'ÚLTIMA VENDA' in df.columns:
        valid_dates = df[df['ÚLTIMA VENDA'].notna()]['ÚLTIMA VENDA']
        never_bought_count = df['ÚLTIMA VENDA'].isna().sum()
        
        if not valid_dates.empty:
            first_sale = valid_dates.min().strftime('%d/%m/%Y')
            last_sale = valid_dates.max().strftime('%d/%m/%Y')
            
    return {
        'total_clientes': int(total_clientes),
        'total_valor': f"R$ {total_valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
        'primeira_venda': first_sale or '-',
        'ultima_venda': last_sale or '-',
        'nunca_compraram': int(never_bought_count)
    }

def analyze_spreadsheet(file_path, filter_type, filter_value, include_no_date=False):
    """Analisa a planilha e retorna clientes sem compras no período"""
    
    df = read_and_parse_spreadsheet(file_path) # Usar a helper function

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
    
    elif filter_type == 'custom':
        # Filtro por período personalizado
        start_date_str, end_date_str = filter_value.split('|')
        
        # Converter para datetime (início do dia e fim do dia)
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        # Ajustar data final para incluir o dia todo (23:59:59)
        end_date = end_date.replace(hour=23, minute=59, second=59)

        # Filtrar clientes cuja última venda está dentro do range e ANTES da data final
        # A lógica é: mostrar quem comprou neste período
        # Mas o usuário pediu "clientes inativos". 
        # Porém, a descrição na tela diz "Listar clientes cuja última compra foi DENTRO deste período ou ANTES dele"
        # Não, na tela coloquei: "Serão listados clientes cuja última compra foi DENTRO deste período"
        # Vamos assumir que o usuário quer ver quem comprou entre X e Y.
        
        # Re-lendo o pedido: "coloque uma opção de o usuário selecionar o calendario, o ano e a data de inicio e fim"
        # Contexto: "Puxar" dados antigos. Então ele quer ver quem comprou em 2021, por exemplo.
        
        filtered_df = df[
            (df['ÚLTIMA VENDA'].notna()) &
            (df['ÚLTIMA VENDA'] >= start_date) &
            (df['ÚLTIMA VENDA'] <= end_date)
        ].copy()
        
        s_display = start_date.strftime('%d/%m/%Y')
        e_display = end_date.strftime('%d/%m/%Y')
        filter_description = f"vendas entre {s_display} e {e_display}"

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

@app.route('/preview', methods=['POST'])
def preview():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'Nenhum arquivo enviado'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'Nenhum arquivo selecionado'}), 400

        if not file.filename.endswith(('.xlsx', '.xls')):
            return jsonify({'error': 'Apenas arquivos Excel (.xlsx, .xls) são permitidos'}), 400

        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        result = preview_spreadsheet(filepath)
        os.remove(filepath)

        return jsonify(result)
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
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
