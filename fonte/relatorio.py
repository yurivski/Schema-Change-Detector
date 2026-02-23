import os
from datetime import datetime

# Relatório HTML para mudanças de esquema
def carregar_template(nome):
    caminho = os.path.join('templates', f'{nome}.html')
    with open(caminho, 'r', encoding='utf-8') as f:
        return f.read()
    
# Gera HTML para uma mudança específica
def gerar_linha_mudanca(mudanca, tipo):
    """Gera uma linha HTML para uma mudança."""
    coluna = mudanca['coluna']
    
    if tipo == 'breaking':
        if mudanca.get('tipo') == 'column_removed':
            return f"""
                <tr>
                    <td><code>{coluna}</code></td>
                    <td><span class="badge-breaking">Coluna Removida</span></td>
                    <td>Existente</td>
                    <td>—</td>
                </tr>
            """
        elif mudanca['campo'] == 'tipo':
            return f"""
                <tr>
                    <td><code>{coluna}</code></td>
                    <td><span class="badge-breaking">Tipo Alterado</span></td>
                    <td><code>{mudanca['valor_antigo']}</code></td>
                    <td><code>{mudanca['valor_novo']}</code></td>
                </tr>
            """
        elif mudanca['campo'] == 'not_null':
            return f"""
                <tr>
                    <td><code>{coluna}</code></td>
                    <td><span class="badge-breaking">NOT NULL Adicionado</span></td>
                    <td>NULL permitido</td>
                    <td>NOT NULL</td>
                </tr>
            """
        elif mudanca['campo'] == 'primary_key':
            return f"""
                <tr>
                    <td><code>{coluna}</code></td>
                    <td><span class="badge-breaking">Primary Key Mudou</span></td>
                    <td>{mudanca['valor_antigo']}</td>
                    <td>{mudanca['valor_novo']}</td>
                </tr>
            """
    
    elif tipo == 'warning':
        if mudanca['campo'] == 'not_null':
            return f"""
                <tr>
                    <td><code>{coluna}</code></td>
                    <td><span class="badge-warning">NOT NULL Removido</span></td>
                    <td>NOT NULL</td>
                    <td>NULL permitido</td>
                </tr>
            """
        elif mudanca['campo'] == 'unique':
            return f"""
                <tr>
                    <td><code>{coluna}</code></td>
                    <td><span class="badge-warning">UNIQUE Mudou</span></td>
                    <td>{mudanca['valor_antigo']}</td>
                    <td>{mudanca['valor_novo']}</td>
                </tr>
            """
    
    elif tipo == 'safe':
        return f"""
            <tr>
                <td><code>{coluna}</code></td>
                <td><span class="badge-safe">Coluna Adicionada</span></td>
                <td>Nova coluna adicionada</td>
            </tr>
        """
    
    return ""

# Classifica mudanças em breaking/warning/safe
def classificar_mudancas(mudancas):
    """Classifica mudanças em breaking/warning/safe."""
    breaking = []
    warning = []
    safe = []
    
    for m in mudancas:
        if m['tipo'] == 'column_removed':
            breaking.append(m)
        elif m['tipo'] == 'column_added':
            safe.append(m)
        elif m['tipo'] in ['type_changed', 'property_changed']:
            if m['campo'] == 'tipo':
                breaking.append(m)
            elif m['campo'] == 'not_null':
                if m['valor_novo'] == True:
                    breaking.append(m)
                else:
                    warning.append(m)
            elif m['campo'] == 'primary_key':
                breaking.append(m)
            elif m['campo'] == 'default':
                breaking.append(m)
            elif m['campo'] == 'foreign_key':
                if not m['valor_antigo'] and m['valor_novo']:
                    warning.append(m)
                else:
                    breaking.append(m)
            elif m['campo'] == 'unique':
                warning.append(m)
    
    return breaking, warning, safe

# Gera HTML para uma seção de mudanças (breaking/warning/safe)
def gerar_secao(mudancas, tipo):
    """Gera HTML de uma seção (breaking/warning/safe)."""
    if not mudancas:
        return ""
    
    template = carregar_template(f'secao_{tipo}')
    
    linhas = ""
    for m in mudancas:
        linhas += gerar_linha_mudanca(m, tipo)
    
    html = template.replace('{{count}}', str(len(mudancas)))
    html = html.replace('{{linhas}}', linhas)
    
    return html

# Gera HTML para uma tabela específica
def gerar_html_tabela(nome_tabela, mudancas):
    """Gera HTML para uma tabela específica."""
    if not mudancas:
        return "", 0, 0, 0
    
    breaking, warning, safe = classificar_mudancas(mudancas)
    
    # Gerar seções
    html_breaking = gerar_secao(breaking, 'breaking')
    html_warning = gerar_secao(warning, 'warning')
    html_safe = gerar_secao(safe, 'safe')
    
    secoes_html = html_breaking + html_warning + html_safe
    
    # Carregar template da tabela
    template = carregar_template('tabela')
    
    html = template.replace('{{nome_tabela}}', nome_tabela.upper())
    html = html.replace('{{breaking}}', str(len(breaking)))
    html = html.replace('{{warning}}', str(len(warning)))
    html = html.replace('{{safe}}', str(len(safe)))
    html = html.replace('{{secoes_html}}', secoes_html)
    
    return html, len(breaking), len(warning), len(safe)

# Gera relatório HTML consolidado de todas as tabelas
def gerar_relatorio_consolidado(todas_mudancas):
    """Gera relatório HTML consolidado de todas as tabelas."""
    template = carregar_template('base')
    
    total_breaking = 0
    total_warning = 0
    total_safe = 0
    tabelas_html = ""
    
    for nome_tabela, mudancas in todas_mudancas.items():
        tabela_html, brk, wrn, saf = gerar_html_tabela(nome_tabela, mudancas)
        
        if tabela_html:
            tabelas_html += tabela_html
            total_breaking += brk
            total_warning += wrn
            total_safe += saf
    
    if not tabelas_html:
        tabelas_html = '<div class="table-section"><div class="no-changes">Nenhuma mudança detectada</div></div>'
    
    timestamp = datetime.now().strftime('%d/%m/%Y às %H:%M:%S')
    
    html = template.replace('{{timestamp}}', timestamp)
    html = html.replace('{{total_breaking}}', str(total_breaking))
    html = html.replace('{{total_warning}}', str(total_warning))
    html = html.replace('{{total_safe}}', str(total_safe))
    html = html.replace('{{tabelas_html}}', tabelas_html)
    
    return html

# Salva relatório HTML em arquivo
def salvar_relatorio(html, nome_arquivo='relatorio_consolidado'):
    """Salva relatório HTML em arquivo."""
    os.makedirs('relatorios', exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    nome_arquivo_final = f"{nome_arquivo}_{timestamp}.html"
    caminho = os.path.join('relatorios', nome_arquivo_final)
    
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write(html)
    
    return caminho