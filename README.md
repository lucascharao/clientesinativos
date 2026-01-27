# Sistema de Análise de Clientes - Mutumilk

Sistema web para análise de clientes sem movimentação, com interface minimalista e intuitiva.

## Funcionalidades

- Upload de planilha Excel (.xlsx, .xls)
- Análise da coluna "ÚLTIMA VENDA"
- Filtros disponíveis:
  - **Por dias**: 30, 60 ou 90 dias sem compra
  - **Por meses**: Selecione meses específicos do ano
- Listagem de clientes inativos com:
  - Código do cliente
  - Nome fantasia
  - Data da última venda
  - Total de vendas
- Exportação de resultados em CSV
- Interface responsiva e moderna

## Requisitos

- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)

## Instalação

1. **Instalar dependências:**
```bash
pip install -r requirements.txt
```

## Como Usar

1. **Iniciar o servidor:**
```bash
python app.py
```

2. **Acessar a aplicação:**
Abra seu navegador e acesse: `http://localhost:5000`

3. **Usar o sistema:**
   - Clique para selecionar a planilha de clientes
   - Escolha o tipo de filtro (Por dias ou Por meses)
   - Se escolheu "Por dias": selecione 30, 60 ou 90 dias
   - Se escolheu "Por meses": marque os meses desejados
   - Clique em "Analisar Planilha"
   - Visualize os resultados na tabela
   - Exporte para CSV se necessário

## Estrutura do Projeto

```
clientesmutu/
├── app.py                          # Backend Flask
├── requirements.txt                # Dependências Python
├── README.md                       # Documentação
├── templates/
│   └── index.html                  # Interface HTML
├── static/
│   ├── css/
│   │   └── style.css              # Estilos
│   └── js/
│       └── script.js              # Lógica frontend
└── uploads/                        # Pasta temporária (criada automaticamente)
```

## Formato da Planilha

A planilha deve ter as seguintes colunas (a partir da linha 18):
- **CÓDIGO**: Código do cliente
- **NOME FANTASIA**: Nome do cliente
- **ÚLTIMA VENDA**: Data da última venda (formato DD/MM/YYYY)
- **TOTAL**: Valor total de vendas

## Tecnologias Utilizadas

- **Backend**: Python + Flask
- **Processamento**: Pandas (rápido e preciso)
- **Frontend**: HTML5 + CSS3 + JavaScript
- **Design**: Interface minimalista e responsiva

## Observações

- Arquivos são processados e removidos automaticamente após análise
- Limite de upload: 16MB
- A aplicação analisa apenas clientes sem compra no período selecionado
- Clientes que nunca compraram também são listados
