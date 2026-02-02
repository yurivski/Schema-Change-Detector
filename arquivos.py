"""
Script simples que escrevi para criar todas as pastas e arquivos do projeto
automaticamente. É muito chato ficar criando pastas e arquivos um por um. 

(Deus abençoe Alan Turing, Ada Lovelace e Dennis Ritchie)
"""
import os

# 'Nome da Pasta': ['Lista', 'de', 'Arquivos']
estrutura = {
    '': ['cli.py'],
    'config': ['config.yaml'],
    'fonte': ['__init__.py', 'capt.py', 'comparador.py', 'classificador.py', 'relator.py', 'armazenamento.py'],
    'historico': ['categories.json', 'customers.json', 'departments.json', 'order_items.json', 'orders.json', 'products.json'],
    'relatorios': ['mudancas.py'],
    'testes': ['teste_capt.py', 'teste_comp.py', 'teste_classific.py']
}

for pasta, arquivos in estrutura.items():
    # Cria a pasta
    os.makedirs(pasta, exist_ok=True)
    
    # Cria cada arquivo dentro da respectiva pasta
    for nome_arquivo in arquivos:
        caminho_completo = os.path.join(pasta, nome_arquivo)
#        with open(caminho_completo, 'w', encoding='utf-8') as f:
#            f.write(f"# Arquivo {nome_arquivo} criado via script")

print("Pastas e arquivos criados com sucesso.")
