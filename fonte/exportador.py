# Conectar no PostgreSQL e extrair as informações completas das tabelas

import os
from sqlalchemy import create_engine, inspect
from dotenv import load_dotenv
from datetime import datetime
import json

load_dotenv()

host=os.getenv('DB_HOST')
database=os.getenv('DB_NAME')
user=os.getenv('DB_USER')
password=os.getenv('DB_PASSWORD')
port=os.getenv('DB_PORT')

conn_str = f'postgresql://{user}:{password}@{host}/{database}'
engine = create_engine(conn_str)
inspector = inspect(engine)


# Transformando a execução em função reutilizavel para ser importada no arquivo comparador
"""
Para um projeto com mais de um arquivo, precisamos criá-los para que a execução do arquivo
base se transforme em uma função reutilizavel para usar em outro arquivo, 
caso contrário, o trabalho será grande para refazer.
"""
def extrair_metadados(inspector, nome_tabela):
    # dados da tabela
    colunas = inspector.get_columns(nome_tabela)
    pk_info = inspector.get_pk_constraint(nome_tabela)
    fk_info = inspector.get_foreign_keys(nome_tabela)
    indices = inspector.get_indexes(nome_tabela)
    unique_constraints = inspector.get_unique_constraints(nome_tabela)
    check_constraints = inspector.get_check_constraints(nome_tabela)


    info_colunas = {}
    for col in colunas:
        nome_col = col['name']

        # Mapeamento detalhado das colunas:
        # .__visit_name__ para extrair o tipo da coluna, ex: VARCHAR 
        # 'tipo': str(col['type']) para extrair o tipo completo, ex: VARCHAR(50)
        info_colunas[nome_col] = {
            'tipo': str(col['type']),
            'not_null': not col['nullable'],
            'default': col.get('default'),
            'primary_key': nome_col in pk_info.get('constrained_columns', []),
            'unique': any(nome_col in u['column_names'] for u in unique_constraints),
            #'tamanho_max': getattr(col['type'], 'length', None),
            'foreign_key': [fk for fk in fk_info if nome_col in fk['constrained_columns']]
        }


    return {
        'capturado_em': datetime.now().isoformat(),
        'tabela': nome_tabela,
        'qtd_colunas': len(colunas),
        'colunas': info_colunas,
        'indices': [idx['name'] for idx in indices],
        'constraints_check': [[c['sqltext'] for c in check_constraints]]

    }    

print("\nSalvando dados na pasta")
print()

if __name__ == "__main__":
    tabelas = ['categories', 'customers', 'departments', 'order_items', 'orders', 'products', 
                'order_detail_v', 'clientes_teste']

# Salvando a lista nos arquivos json nomeados de acordo com as tabelas:
salvar_json = 'historico'

for metadados in tabelas:
    extrair = extrair_metadados(inspector, metadados)
    caminho_arquivo = os.path.join(salvar_json, f"{metadados}_DEPOIS_5x.json")

    try:
        with open(caminho_arquivo, 'w', encoding='utf-8') as f:
            # indent=4 deixa o arquivo organizado para leitura humana
            # # ensure_ascii=False permite caracteres especiais (acentos)
            json.dump(extrair, f, indent=4, ensure_ascii=False)
        print(f"Lista de dicionários salvos em: {caminho_arquivo}")
    except Exception as e:
        print(f"Erro no dicionário: {metadados}: {e}")

