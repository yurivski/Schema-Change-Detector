import os
from datetime import datetime

def gerar_relatorio_html(mudancas, nome_tabela):
    breaking = 0
    warning = 0
    safe = 0
    
    # Separar mudanças por tipo
    adicionadas = []
    removidas = []
    modificadas = []
    
    for m in mudancas:
        if m['tipo'] == 'column_removed':
            breaking += 1
            removidas.append(m)
        elif m['tipo'] == 'column_added':
            safe += 1
            adicionadas.append(m)
        elif m['tipo'] in ['type_changed', 'property_changed']:
            modificadas.append(m)
            if m['campo'] == 'tipo':
                breaking += 1
            elif m['campo'] == 'not_null':
                if m['valor_novo'] == True:
                    breaking += 1
                else:
                    warning += 1
            elif m['campo'] == 'primary_key':
                breaking += 1
            elif m['campo'] == 'default':
                breaking += 1
            elif m['campo'] == 'foreign_key':
                if not m['valor_antigo'] and m['valor_novo']:
                    warning += 1
                else:
                    breaking += 1
            elif m['campo'] == 'unique':
                warning += 1

    agora = datetime.now().strftime('%d/%m/%Y às %H:%M:%S')
    
    # Gerar HTML das tabelas de mudanças
    html_breaking = ""
    html_warning = ""
    html_safe = ""
    
    # Tabela BREAKING
    if breaking > 0:
        html_breaking = """
        <div class="section">
            <h2 class="section-title breaking">🔴 Breaking Changes ({0})</h2>
            <table class="changes-table">
                <thead>
                    <tr>
                        <th>Coluna</th>
                        <th>Tipo de Mudança</th>
                        <th>Antes</th>
                        <th>Depois</th>
                    </tr>
                </thead>
                <tbody>
        """.format(breaking)
        
        for m in removidas:
            html_breaking += f"""
                    <tr>
                        <td><code>{m['coluna']}</code></td>
                        <td><span class="badge-breaking">Coluna Removida</span></td>
                        <td>Existente</td>
                        <td>—</td>
                    </tr>
            """
        
        for m in modificadas:
            if m['campo'] == 'tipo':
                html_breaking += f"""
                    <tr>
                        <td><code>{m['coluna']}</code></td>
                        <td><span class="badge-breaking">Tipo Alterado</span></td>
                        <td><code>{m['valor_antigo']}</code></td>
                        <td><code>{m['valor_novo']}</code></td>
                    </tr>
                """
            elif m['campo'] == 'not_null' and m['valor_novo'] == True:
                html_breaking += f"""
                    <tr>
                        <td><code>{m['coluna']}</code></td>
                        <td><span class="badge-breaking">NOT NULL Adicionado</span></td>
                        <td>NULL permitido</td>
                        <td>NOT NULL</td>
                    </tr>
                """
            elif m['campo'] == 'primary_key':
                html_breaking += f"""
                    <tr>
                        <td><code>{m['coluna']}</code></td>
                        <td><span class="badge-breaking">Primary Key Mudou</span></td>
                        <td>{m['valor_antigo']}</td>
                        <td>{m['valor_novo']}</td>
                    </tr>
                """
        
        html_breaking += """
                </tbody>
            </table>
        </div>
        """
    
    # Tabela WARNING
    if warning > 0:
        html_warning = """
        <div class="section">
            <h2 class="section-title warning">🟡 Warnings ({0})</h2>
            <table class="changes-table">
                <thead>
                    <tr>
                        <th>Coluna</th>
                        <th>Tipo de Mudança</th>
                        <th>Antes</th>
                        <th>Depois</th>
                    </tr>
                </thead>
                <tbody>
        """.format(warning)
        
        for m in modificadas:
            if m['campo'] == 'not_null' and m['valor_novo'] == False:
                html_warning += f"""
                    <tr>
                        <td><code>{m['coluna']}</code></td>
                        <td><span class="badge-warning">NOT NULL Removido</span></td>
                        <td>NOT NULL</td>
                        <td>NULL permitido</td>
                    </tr>
                """
            elif m['campo'] == 'unique':
                html_warning += f"""
                    <tr>
                        <td><code>{m['coluna']}</code></td>
                        <td><span class="badge-warning">UNIQUE Mudou</span></td>
                        <td>{m['valor_antigo']}</td>
                        <td>{m['valor_novo']}</td>
                    </tr>
                """
        
        html_warning += """
                </tbody>
            </table>
        </div>
        """
    
    # Tabela SAFE
    if safe > 0:
        html_safe = """
        <div class="section">
            <h2 class="section-title safe">🟢 Safe Changes ({0})</h2>
            <table class="changes-table">
                <thead>
                    <tr>
                        <th>Coluna</th>
                        <th>Tipo de Mudança</th>
                        <th>Detalhes</th>
                    </tr>
                </thead>
                <tbody>
        """.format(safe)
        
        for m in adicionadas:
            html_safe += f"""
                    <tr>
                        <td><code>{m['coluna']}</code></td>
                        <td><span class="badge-safe">Coluna Adicionada</span></td>
                        <td>Nova coluna adicionada</td>
                    </tr>
            """
        
        html_safe += """
                </tbody>
            </table>
        </div>
        """

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Schema Change Report - {nome_tabela}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
            background: #f5f5f5;
            color: #333;
            line-height: 1.6;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px 40px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        .header h1 {{
            font-size: 2em;
            font-weight: 600;
            margin-bottom: 10px;
        }}
        
        .metadata {{
            font-size: 0.95em;
            opacity: 0.95;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 30px 40px;
        }}
        
        .overview {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .stat-card {{
            background: white;
            padding: 25px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            border-left: 4px solid;
        }}
        
        .stat-card.breaking {{
            border-left-color: #e53e3e;
        }}
        
        .stat-card.warning {{
            border-left-color: #dd6b20;
        }}
        
        .stat-card.safe {{
            border-left-color: #38a169;
        }}
        
        .stat-number {{
            font-size: 3em;
            font-weight: 700;
            line-height: 1;
            margin-bottom: 8px;
        }}
        
        .stat-card.breaking .stat-number {{
            color: #e53e3e;
        }}
        
        .stat-card.warning .stat-number {{
            color: #dd6b20;
        }}
        
        .stat-card.safe .stat-number {{
            color: #38a169;
        }}
        
        .stat-label {{
            font-size: 0.9em;
            color: #718096;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            font-weight: 600;
        }}
        
        .section {{
            background: white;
            margin-bottom: 25px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            overflow: hidden;
        }}
        
        .section-title {{
            font-size: 1.3em;
            font-weight: 600;
            padding: 20px 25px;
            margin: 0;
            border-bottom: 2px solid #e2e8f0;
        }}
        
        .section-title.breaking {{
            background: #fff5f5;
            color: #c53030;
        }}
        
        .section-title.warning {{
            background: #fffaf0;
            color: #c05621;
        }}
        
        .section-title.safe {{
            background: #f0fff4;
            color: #276749;
        }}
        
        .changes-table {{
            width: 100%;
            border-collapse: collapse;
        }}
        
        .changes-table th {{
            background: #f7fafc;
            padding: 15px 25px;
            text-align: left;
            font-weight: 600;
            font-size: 0.85em;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: #4a5568;
            border-bottom: 2px solid #e2e8f0;
        }}
        
        .changes-table td {{
            padding: 15px 25px;
            border-bottom: 1px solid #e2e8f0;
        }}
        
        .changes-table tbody tr:hover {{
            background: #f7fafc;
        }}
        
        .changes-table tbody tr:last-child td {{
            border-bottom: none;
        }}
        
        code {{
            background: #edf2f7;
            padding: 3px 8px;
            border-radius: 4px;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 0.9em;
            color: #2d3748;
        }}
        
        .badge-breaking,
        .badge-warning,
        .badge-safe {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: 600;
        }}
        
        .badge-breaking {{
            background: #fed7d7;
            color: #c53030;
        }}
        
        .badge-warning {{
            background: #feebc8;
            color: #c05621;
        }}
        
        .badge-safe {{
            background: #c6f6d5;
            color: #276749;
        }}
        
        .footer {{
            text-align: center;
            padding: 30px;
            color: #718096;
            font-size: 0.9em;
        }}
        
        @media (max-width: 768px) {{
            .container {{
                padding: 20px;
            }}
            
            .header {{
                padding: 20px;
            }}
            
            .overview {{
                grid-template-columns: 1fr;
            }}
            
            .changes-table {{
                font-size: 0.9em;
            }}
            
            .changes-table th,
            .changes-table td {{
                padding: 10px 15px;
            }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Schema Change Report</h1>
        <div class="metadata">
            <strong>Tabela:</strong> {nome_tabela.upper()} | 
            <strong>Gerado em:</strong> {agora}
        </div>
    </div>
    
    <div class="container">
        <div class="overview">
            <div class="stat-card breaking">
                <div class="stat-number">{breaking}</div>
                <div class="stat-label">Breaking Changes</div>
            </div>
            <div class="stat-card warning">
                <div class="stat-number">{warning}</div>
                <div class="stat-label">Warnings</div>
            </div>
            <div class="stat-card safe">
                <div class="stat-number">{safe}</div>
                <div class="stat-label">Safe Changes</div>
            </div>
        </div>
        
        {html_breaking}
        {html_warning}
        {html_safe}
    </div>
    
    <div class="footer">
        <p><strong>Schema Change Detector</strong> | Desenvolvido por Yuri Pontes</p>
    </div>
</body>
</html>
"""
    
    return html

def salvar_relatorio(html, nome_tabela):
    os.makedirs('relatorios', exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    nome_arquivo = f"relatorio_{nome_tabela}_{timestamp}.html"
    caminho = os.path.join('relatorios', nome_arquivo)
    
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write(html)
    
    return caminho
