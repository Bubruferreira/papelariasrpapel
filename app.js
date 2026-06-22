document.addEventListener("DOMContentLoaded", () => {
    const themeToggle = document.getElementById("theme-toggle");
    const roleSelector = document.getElementById("role-selector");
    const viewRoot = document.getElementById("view-root");
    const heroTitle = document.getElementById("hero-title");
    const heroSubtitle = document.getElementById("hero-subtitle");

    // 1. Alternador Dinâmico de Tema (Tokens)
    themeToggle.addEventListener("click", () => {
        const currentTheme = document.body.getAttribute("data-theme");
        const targetTheme = currentTheme === "dark" ? "light" : "dark";
        document.body.setAttribute("data-theme", targetTheme);
    });

    // 2. Ouvinte de Papéis (RBAC System)
    roleSelector.addEventListener("change", (e) => {
        updateContextHeaders(e.target.value);
        render(e.target.value);
    });

    function updateContextHeaders(role) {
        if (role === "cliente") {
            heroTitle.innerText = "Sr. Papel";
            heroSubtitle.innerText = "Catálogo Oficial • Atualizado em Tempo Real";
        } else if (role === "caixa") {
            heroTitle.innerText = "🏪 PDV Rápido";
            heroSubtitle.innerText = "Terminal de Saída Balcão";
        } else {
            heroTitle.innerText = "📊 Inteligência Corporativa";
            heroSubtitle.innerText = "Análise Tática de Performance Geral";
        }
    }

    async function render(role) {
        viewRoot.innerHTML = "<p>Carregando dados da aplicação...</p>";
        try {
            const products = await ApiService.fetchProducts();
            viewRoot.innerHTML = "";

            if (role === "cliente") {
                const grid = document.createElement("div");
                grid.className = "grid-container";

                products.forEach(p => {
                    const card = document.createElement("div");
                    card.className = "card";
                    
                    let stockStatus = `<span style="color: var(--success); font-weight:bold;">✔ Disponível</span>`;
                    if (p.Quantidade_Atual === 0) {
                        stockStatus = `<span style="color: var(--text-muted); text-decoration: line-through;">❌ Indisponível</span>`;
                    } else if (p.Quantidade_Atual <= p.Ponto_Pedido) {
                        stockStatus = `<span style="color: var(--danger); font-weight:bold;">🔥 Apenas ${p.Quantidade_Atual} un!</span>`;
                    }

                    card.innerHTML = `
                        <h3>${p.Nome}</h3>
                        <p style="color: var(--text-muted); font-size:0.85rem;">EAN: ${p.SKU_EAN}</p>
                        <p><strong>Varejo:</strong> R$ ${p.Preco_Varejo.toFixed(2)}</p>
                        <div style="margin: 15px 0;">${stockStatus}</div>
                        <button class="btn-primary" ${p.Quantidade_Atual === 0 ? 'disabled' : ''}>Comprar</button>
                    `;
                    grid.appendChild(card);
                });
                viewRoot.appendChild(grid);
            } 
            
            else if (role === "caixa") {
                // Interface Otimizada para Entrada de Leitor ou Teclado ("Modo Tio")
                const posContainer = document.createElement("div");
                posContainer.className = "card";
                posContainer.innerHTML = `
                    <h3>Registrar Venda por Código de Barras</h3>
                    <div style="margin: 20px 0;">
                        <input type="text" id="barcode-input" class="select-control" placeholder="Bipe ou digite o código SKU" autofocus>
                    </div>
                    <button id="btn-submit-sale" class="btn-primary">Confirmar Baixa do Item</button>
                    <div id="pos-feedback" style="margin-top: 15px; font-weight: 600;"></div>
                `;
                viewRoot.appendChild(posContainer);

                const input = document.getElementById("barcode-input");
                const feedback = document.getElementById("pos-feedback");

                const executeSale = async () => {
                    const sku = input.value.trim();
                    if(!sku) return;
                    feedback.innerText = "Processando transação...";
                    const res = await ApiService.processSale(sku);
                    
                    if (res.status === "success") {
                        feedback.style.color = "var(--success)";
                        feedback.innerText = res.message;
                        input.value = "";
                        input.focus();
                    } else {
                        feedback.style.color = "var(--danger)";
                        feedback.innerText = res.message;
                    }
                };

                document.getElementById("btn-submit-sale").addEventListener("click", executeSale);
                input.addEventListener("keypress", (e) => { if(e.key === "Enter") executeSale(); });
            }
        } catch (error) {
            viewRoot.innerHTML = "<p style='color: var(--danger);'>Ocorreu um erro crítico ao renderizar a interface.</p>";
        }
    }

    // Inicialização da View padrão
    render("cliente");
});