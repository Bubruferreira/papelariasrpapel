const ApiService = {
    async fetchProducts() {
        try {
            const response = await fetch('/api/products');
            if (!response.ok) throw new Error('Erro na requisição HTTP.');
            return await response.json();
        } catch (error) {
            console.error('ApiService Erro:', error);
            throw error;
        }
    },

    async processSale(sku) {
        try {
            const response = await fetch('/api/products/sell', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ sku: sku })
            });
            return await response.json();
        } catch (error) {
            console.error('ApiService Erro:', error);
            throw error;
        }
    }
};
