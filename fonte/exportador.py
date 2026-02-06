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


def extrair_metadados(inspector, nome_tabela):
    """
    Extrai os metadados das colunas das tabelas do banco de dados PostgreSQL.
    Metadados extraidos: colunas, PKs, FKs, Índices e Constraints
    """

    colunas = inspector.get_columns(nome_tabela)
    pk_info = inspector.get_pk_constraint(nome_tabela)
    fk_info = inspector.get_foreign_keys(nome_tabela)
    indices = inspector.get_indexes(nome_tabela)
    unique_constraints = inspector.get_unique_constraints(nome_tabela)
    check_constraints = inspector.get_check_constraints(nome_tabela)

    # Mapeia as colunas
    info_colunas = {}
    for col in colunas:
        nome_col = col['name']

        # Mapeamento detalhado das colunas: 
        # 'tipo': str(col['type']) para extrair o tipo completo, ex: VARCHAR(50)
        info_colunas[nome_col] = {
            'tipo': str(col['type']),
            'not_null': not col['nullable'],
            'default': col.get('default'),
            'primary_key': nome_col in pk_info.get('constrained_columns', []),
            'unique': any(nome_col in u['column_names'] for u in unique_constraints),
            # Usei list comprehension para filtrar FKs especídifcas desta coluna
            'foreign_key': [fk for fk in fk_info if nome_col in fk['constrained_columns']]
        }


    return {
        'capturado_em': datetime.now().isoformat(),
        'tabela': nome_tabela,
        'qtd_colunas': len(colunas),
        'colunas': info_colunas,
        'indices': [idx['name'] for idx in indices],
        'constraints_check': [c['sqltext'] for c in check_constraints]

    }    

def salvar_json(tabelas, diretorio='historico', sufixo=None):

    if sufixo is None:
        sufixo = datetime.now.strftime('%y-%m-%d_%H-%M-%S')

    print(f"\nJson salvo em: {diretorio}/")

    for tabela in tabelas:
        
        try:
            schema = extrair_metadados(inspector, tabela)
            arquivo = f"{tabela}_{sufixo}.json"
            caminho_arquivo = os.path.join(diretorio, arquivo)
            with open(caminho_arquivo, 'w', encoding='utf-8') as f:
                # indent=4 deixa o arquivo organizado para leitura humana
                # # ensure_ascii=False permite caracteres especiais (acentos)
                json.dump(schema, f, indent=4, ensure_ascii=False)
            print(f"{tabela}: {arquivo}")
        except Exception as e:
                print(f"Erro no dicionário: {tabela}: {e}")

# Execução principal
if __name__ == "__main__":

    tabelas = ['categories', 
                'customers', 
                'departments', 
                'order_items', 
                'orders', 
                'products', 
                'order_detail_v', 
                'clientes_teste']
    
    # Salvando a lista em arquivo json noameado de acordo com a tabelas
    salvar_json(tabelas, diretorio='historico', sufixo='em_execucao')

