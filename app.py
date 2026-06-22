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

# --- DECORATORS ---
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

# --- ROTAS ---
@app.route('/')
def catalogo():
    banco = carregar_banco()
    produtos = banco.get('produtos', {})
    busca = request.args.get('busca', '').lower()
    if busca:
        produtos = {sku: p for sku, p in produtos.items() if busca in p['nome'].lower()}
    return render_template('catalogo.html', produtos=produtos)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u, s = request.form.get('usuario'), request.form.get('senha')
        banco = carregar_banco()
        user = banco.get('usuarios', {}).get(u)
        if user and user['senha'] == s:
            session['usuario'], session['cargo'] = u, user['cargo']
            return redirect(url_for('painel_gerencia' if user['cargo'] == 'gerencia' else 'pdv_caixa'))
        flash("Credenciais inválidas")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/pdv')
@login_obrigatorio
def pdv_caixa():
    carrinho = session.get('carrinho', {})
    total = sum(i['preco'] * i['qtd'] for i in carrinho.values())
    return render_template('caixa.html', carrinho=carrinho, total=total)

@app.route('/adicionar_carrinho', methods=['POST'])
@login_obrigatorio
def adicionar_carrinho():
    sku = request.form.get('sku')
    banco = carregar_banco()
    prod = banco.get('produtos', {}).get(sku)
    if prod and prod['quantidade'] > 0:
        carrinho = session.setdefault('carrinho', {})
        if sku in carrinho:
            if carrinho[sku]['qtd'] < prod['quantidade']: carrinho[sku]['qtd'] += 1
            else: flash("Estoque insuficiente!")
        else: carrinho[sku] = {'nome': prod['nome'], 'preco': prod['preco_varejo'], 'qtd': 1}
        session.modified = True
    else: flash("Produto indisponível!")
    return redirect(url_for('pdv_caixa'))

@app.route('/finalizar_venda', methods=['POST'])
@login_obrigatorio
def finalizar_venda():
    carrinho = session.get('carrinho', {})
    if not carrinho: return redirect(url_for('pdv_caixa'))
        
    banco = carregar_banco()
    
    # Cálculos para o recibo
    total_bruto = sum(item['preco'] * item['qtd'] for item in carrinho.values())
    desconto = float(request.form.get('desconto') or 0)
    valor_recebido = float(request.form.get('recebido') or 0)
    total_pagar = total_bruto - desconto
    troco = valor_recebido - total_pagar if valor_recebido > total_pagar else 0
    
    # Estrutura completa exigida pelo seu recibo.html
    recibo_dados = {
        'data': datetime.now().strftime("%d/%m/%Y %H:%M"),
        'operador': session.get('usuario', 'Caixa'),
        'itens': list(carrinho.values()),
        'total_bruto': total_bruto,
        'desconto': desconto,
        'total_pagar': total_pagar,
        'forma_pgto': request.form.get('pagamento'),
        'valor_recebido': valor_recebido,
        'troco': troco
    }
    
    # Salva no histórico e desconta estoque
    banco.setdefault('vendas', []).append(recibo_dados)
    for sku, item in carrinho.items():
        if sku in banco['produtos']:
            banco['produtos'][sku]['quantidade'] -= item['qtd']
            
    salvar_banco(banco)
    
    # Envia os dados para a página de recibo
    session['ultimo_recibo'] = recibo_dados
    session.pop('carrinho', None)
    return redirect(url_for('exibir_recibo'))

@app.route('/admin')
@gerencia_obrigatoria
def painel_gerencia():
    return render_template('gerencia.html', produtos=carregar_banco().get('produtos', {}))

@app.route('/historico')
@gerencia_obrigatoria
def historico_vendas():
    return render_template('historico.html', vendas=carregar_banco().get('vendas', []))

@app.route('/adicionar_produto', methods=['POST'])
@gerencia_obrigatoria
def adicionar_produto():
    banco = carregar_banco()
    sku = request.form.get('sku')
    banco['produtos'][sku] = {
        "nome": request.form.get('nome'),
        "preco_varejo": float(request.form.get('varejo')),
        "preco_atacado": float(request.form.get('atacado')),
        "quantidade": int(request.form.get('qtd'))
    }
    salvar_banco(banco)
    return redirect(url_for('painel_gerencia'))

@app.route('/entrada_estoque', methods=['POST'])
@gerencia_obrigatoria
def entrada_estoque():
    banco = carregar_banco()
    sku, qtd = request.form.get('sku'), int(request.form.get('qtd'))
    if sku in banco['produtos']:
        banco['produtos'][sku]['quantidade'] += qtd
        salvar_banco(banco)
    return redirect(url_for('painel_gerencia'))

@app.route('/excluir_produto/<sku>')
@gerencia_obrigatoria
def excluir_produto(sku):
    banco = carregar_banco()
    if sku in banco.get('produtos', {}):
        del banco['produtos'][sku]
        salvar_banco(banco)
    return redirect(url_for('painel_gerencia'))

@app.route('/editar_produto/<sku>', methods=['GET', 'POST'])
@gerencia_obrigatoria
def editar_produto(sku):
    banco = carregar_banco()
    if request.method == 'POST':
        p = banco['produtos'][sku]
        p['nome'], p['preco_varejo'] = request.form['nome'], float(request.form['varejo'])
        p['preco_atacado'], p['quantidade'] = float(request.form['atacado']), int(request.form['qtd'])
        salvar_banco(banco)
        return redirect(url_for('painel_gerencia'))
    return render_template('editar.html', sku=sku, produto=banco['produtos'][sku])

@app.route('/recibo')
@login_obrigatorio
def exibir_recibo():
    return render_template('recibo.html', recibo=session.get('ultimo_recibo'))

@app.route('/alterar_qtd/<sku>', methods=['POST'])
@login_obrigatorio
def alterar_qtd(sku):
    carrinho = session.get('carrinho', {})
    acao = request.form.get('acao')
    if sku in carrinho:
        if acao == 'aumentar': carrinho[sku]['qtd'] += 1
        else: carrinho[sku]['qtd'] -= 1
        if carrinho[sku]['qtd'] <= 0: del carrinho[sku]
    session.modified = True
    return redirect(url_for('pdv_caixa'))

@app.route('/adicionar_carrinho_cliente/<sku>', methods=['POST'])
def adicionar_carrinho_cliente(sku):
    banco = carregar_banco()
    prod = banco.get('produtos', {}).get(sku)
    
    # Pega a quantidade enviada pelo formulário, padrão é 1
    qtd_desejada = int(request.form.get('qtd', 1))
    
    if prod and prod['quantidade'] >= qtd_desejada:
        carrinho_cliente = session.setdefault('carrinho_cliente', {})
        
        if sku in carrinho_cliente:
            carrinho_cliente[sku]['qtd'] += qtd_desejada
        else:
            carrinho_cliente[sku] = {
                'nome': prod['nome'], 
                'preco': prod['preco_varejo'], 
                'qtd': qtd_desejada
            }
        
        session.modified = True
        flash(f"{qtd_desejada}x {prod['nome']} adicionado ao carrinho!")
    else:
        flash("Quantidade indisponível em estoque!")
        
    return redirect(url_for('catalogo'))

if __name__ == '__main__':
    app.run(debug=True)
