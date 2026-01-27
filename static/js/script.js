// Elementos do DOM
const fileInput = document.getElementById('fileInput');
const fileName = document.getElementById('fileName');
const uploadForm = document.getElementById('uploadForm');
const filterTypeDays = document.querySelector('input[value="days"]');
const filterTypeMonths = document.querySelector('input[value="months"]');
const daysFilter = document.getElementById('daysFilter');
const monthsFilter = document.getElementById('monthsFilter');
const filterBtns = document.querySelectorAll('.filter-btn');
const selectedRangeInput = document.getElementById('selectedRange');
const includeNoDateCheckbox = document.getElementById('includeNoDate');
const analyzeBtn = document.getElementById('analyzeBtn');
const btnText = document.getElementById('btnText');
const btnLoader = document.getElementById('btnLoader');
const results = document.getElementById('results');
const errorMessage = document.getElementById('errorMessage');
const resultsBody = document.getElementById('resultsBody');
const totalClientes = document.getElementById('totalClientes');
const filterApplied = document.getElementById('filterApplied');
const exportBtn = document.getElementById('exportBtn');

let currentResults = [];

// Atualizar nome do arquivo selecionado
fileInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
        fileName.textContent = file.name;
    } else {
        fileName.textContent = 'Insira sua planilha aqui';
    }
});

// Alternar entre filtros de dias e meses
document.querySelectorAll('input[name="filterType"]').forEach(radio => {
    radio.addEventListener('change', (e) => {
        if (e.target.value === 'days') {
            daysFilter.classList.remove('hidden');
            monthsFilter.classList.add('hidden');
        } else {
            daysFilter.classList.add('hidden');
            monthsFilter.classList.remove('hidden');
        }
    });
});

// Selecionar faixa de dias
filterBtns.forEach(btn => {
    btn.addEventListener('click', (e) => {
        e.preventDefault();
        filterBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        if (btn.dataset.range) {
            selectedRangeInput.value = btn.dataset.range;
        }
    });
});

// Submeter formulário
uploadForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    // Esconder mensagens anteriores
    results.classList.add('hidden');
    errorMessage.classList.add('hidden');

    // Validar arquivo
    const file = fileInput.files[0];
    if (!file) {
        showError('Por favor, selecione um arquivo.');
        return;
    }

    // Preparar dados do formulário
    const formData = new FormData();
    formData.append('file', file);

    // Determinar tipo de filtro
    const filterType = document.querySelector('input[name="filterType"]:checked').value;
    formData.append('filter_type', filterType);

    if (filterType === 'days') {
        formData.append('filter_value', selectedRangeInput.value);
        formData.append('include_no_date', includeNoDateCheckbox.checked ? 'true' : 'false');
    } else {
        // Pegar meses selecionados
        const selectedMonths = Array.from(
            document.querySelectorAll('#monthsFilter input[type="checkbox"]:checked')
        ).map(cb => cb.value);

        if (selectedMonths.length === 0) {
            showError('Por favor, selecione pelo menos um mês.');
            return;
        }

        formData.append('filter_value', selectedMonths.join(','));
    }

    // Mostrar loading
    setLoading(true);

    try {
        const response = await fetch('/analyze', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Erro ao processar arquivo');
        }

        // Mostrar resultados
        displayResults(data);

    } catch (error) {
        showError(error.message);
    } finally {
        setLoading(false);
    }
});

// Exibir resultados
function displayResults(data) {
    currentResults = data.clientes;

    // Atualizar informações
    totalClientes.textContent = data.total;
    filterApplied.textContent = data.filter_description;

    // Limpar tabela
    resultsBody.innerHTML = '';

    // Preencher tabela
    if (data.clientes.length === 0) {
        resultsBody.innerHTML = `
            <tr>
                <td colspan="5" style="text-align: center; padding: 40px;">
                    Nenhum cliente encontrado com os critérios selecionados.
                </td>
            </tr>
        `;
    } else {
        data.clientes.forEach(cliente => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${cliente.codigo}</td>
                <td>${cliente.nome}</td>
                <td>${cliente.ultima_venda}</td>
                <td>${cliente.dias_inativo}</td>
                <td>${cliente.total}</td>
            `;
            resultsBody.appendChild(row);
        });
    }

    // Mostrar seção de resultados
    results.classList.remove('hidden');

    // Scroll suave para resultados
    results.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// Exportar para CSV
exportBtn.addEventListener('click', () => {
    if (currentResults.length === 0) {
        showError('Não há dados para exportar.');
        return;
    }

    // Criar conteúdo CSV
    const headers = ['Código', 'Nome Fantasia', 'Última Venda', 'Dias Inativo', 'Total'];
    const rows = currentResults.map(cliente => [
        cliente.codigo,
        `"${cliente.nome}"`, // Aspas para nomes com vírgula
        cliente.ultima_venda,
        cliente.dias_inativo,
        cliente.total
    ]);

    const csvContent = [
        headers.join(','),
        ...rows.map(row => row.join(','))
    ].join('\n');

    // Criar e baixar arquivo
    const blob = new Blob(['\uFEFF' + csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);

    link.setAttribute('href', url);
    link.setAttribute('download', `clientes_sem_movimentacao_${Date.now()}.csv`);
    link.style.visibility = 'hidden';

    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
});

// Mostrar erro
function showError(message) {
    errorMessage.textContent = message;
    errorMessage.classList.remove('hidden');

    // Scroll para erro
    errorMessage.scrollIntoView({ behavior: 'smooth', block: 'center' });

    // Auto-esconder após 5 segundos
    setTimeout(() => {
        errorMessage.classList.add('hidden');
    }, 5000);
}

// Controlar estado de loading
function setLoading(loading) {
    if (loading) {
        btnText.classList.add('hidden');
        btnLoader.classList.remove('hidden');
        analyzeBtn.disabled = true;
    } else {
        btnText.classList.remove('hidden');
        btnLoader.classList.add('hidden');
        analyzeBtn.disabled = false;
    }
}
