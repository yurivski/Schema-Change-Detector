import os
from datetime import datetime

def gerar_relatorio_html(mudancas, nome_tabela):
    breaking = [m for m in mudancas if 'BREAKING' in str(m)]
    warning = [m for m in mudancas if 'WARNING' in str(m)]
    safe = [m for m in mudancas if 'SAFE' in str(m)]

    agora = datetime.now().strftime('%d/%m/%Y %H:%M:%S')

    html = f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Relatório - {nome_tabela}</title>
        <style>
            /* CSS aqui - Tarefa 2 */
        </style>
    </head>
    <body>
        <header>
            <h1>Schema Change Report</h1>
            <p>Tabela: {nome_tabela}</p>
            <p>Gerado em: {agora}</p>
        </header>
        
        <section class="summary">
            <h2>Resumo</h2>
            <div class="badges">
                <span class="badge breaking">{len(breaking)} BREAKING</span>
                <span class="badge warning">{len(warning)} WARNING</span>
                <span class="badge safe">{len(safe)} SAFE</span>
            </div>
        </section>
        
        <!-- Tarefa 4: Tabelas aqui -->
        
    </body>
    </html>
    """
    
    return html

if __name__ == "__main__":
    mudancas_teste = [
        {'tipo': 'column_removed', 'coluna': 'test'}
    ]

    html = gerar_relatorio_html(mudancas_teste, "TESTE_TABLE")

    with open("teste_relatorio.html", "w") as f:
        f.write(html)

    print("Relatório de teste gerado: teste_relatorio.html")