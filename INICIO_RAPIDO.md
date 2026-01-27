# Início Rápido

## Como usar o sistema em 3 passos:

### 1. Iniciar o servidor
```bash
./run.sh
```

Ou manualmente:
```bash
source venv/bin/activate
python app.py
```

### 2. Abrir no navegador
Acesse: **http://localhost:5000**

### 3. Usar a aplicação

1. **Selecione a planilha**
   - Clique na área de upload
   - Escolha o arquivo `.xlsx` com os dados dos clientes

2. **Escolha o filtro**
   - **Por Dias**: Clientes sem compra nos últimos 30, 60 ou 90 dias
   - **Por Meses**: Clientes que não compraram em meses específicos do ano

3. **Clique em "Analisar Planilha"**
   - O sistema processará os dados
   - Resultados aparecerão em poucos segundos

4. **Exporte se necessário**
   - Clique em "Exportar CSV" para baixar os resultados

---

## Exemplos de uso:

### Exemplo 1: Clientes inativos nos últimos 60 dias
- Tipo de filtro: **Por Dias**
- Período: **60 dias**
- Resultado: Lista de clientes que não compraram nos últimos 2 meses

### Exemplo 2: Clientes que não compraram no último trimestre
- Tipo de filtro: **Por Meses**
- Meses: ✅ **Outubro, Novembro, Dezembro**
- Resultado: Lista de clientes sem compras no Q4

---

## Solução de problemas:

**Erro ao iniciar servidor:**
```bash
# Reinstalar dependências
./venv/bin/pip install -r requirements.txt
```

**Erro ao processar planilha:**
- Verifique se a planilha tem as colunas: CÓDIGO, NOME FANTASIA, ÚLTIMA VENDA
- Certifique-se que o formato de data está correto (DD/MM/YYYY)

**Página não carrega:**
- Verifique se o servidor está rodando
- Tente acessar: http://127.0.0.1:5000

---

## Estrutura da planilha esperada:

A planilha deve ter (a partir da linha 18):
- **CÓDIGO**: Código do cliente (ex: 9632)
- **NOME FANTASIA**: Nome do estabelecimento
- **ÚLTIMA VENDA**: Data no formato DD/MM/YYYY (ex: 27/09/2025)
- **TOTAL**: Valor total de vendas

---

Para mais informações, consulte o arquivo `README.md`
