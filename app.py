from flask import Flask, render_template, request, redirect, url_for, session, flash
from datetime import datetime
from functools import wraps
import json

app = Flask(__name__)
app.secret_key = 'chave_super_secreta_sr_papel'

def carregar_banco():
    try:
        with open('database.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {"usuarios": {}, "produtos": {}, "vendas": []}

def salvar_banco(dados):
    with open('database.json', 'w', encoding='utf-8') as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)

# --- DECORATORS DE SEGURANÇA ---
def login_obrigatorio(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario' not in session: return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def gerencia_obrigatoria(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('cargo') != 'gerencia':
            flash("Acesso restrito à gerência.")
            return redirect(url_for('pdv_caixa'))
        return f(*args, **kwargs)
    return decorated_function

# ROTA DE HISTÓRICO CORRIGIDA
@app.route('/historico')
@gerencia_obrigatoria
def historico_vendas():
    banco = carregar_banco()
    # Usamos .get() para evitar erro se a chave não existir
    vendas = banco.get('vendas', [])
    return render_template('historico.html', vendas=vendas)

# ROTA DE FINALIZAR VENDA (ESTRUTURA PADRONIZADA)
@app.route('/finalizar_venda', methods=['POST'])
def finalizar_venda():
    carrinho = session.get('carrinho', {})
    banco = carregar_banco()
    
    total = sum(i['preco'] * i['qtd'] for i in carrinho.values())
    
    venda = {
        'data': datetime.now().strftime("%d/%m/%Y %H:%M"),
        'itens': list(carrinho.values()),
        'forma_pgto': request.form.get('pagamento', 'Dinheiro'),
        'total_pagar': total
    }
    
    banco.setdefault('vendas', []).append(venda)
    salvar_banco(banco)
    session.pop('carrinho', None)
    return redirect(url_for('pdv_caixa'))

if __name__ == '__main__':
    app.run(debug=True)