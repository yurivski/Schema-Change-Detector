# Conectar no PostgreSQL e extrair as informações completas das tabelas

import os 
import pandas as pd 
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

tabelas = ['categories', 'customers', 'departments', 'order_items', 'orders', 'products']
dicionario = {}

# Dados da tabela
for dados in tabelas:
    colunas = inspector.get_columns(dados)
    pk_info = inspector.get_pk_constraint(dados)
    fk_info = inspector.get_foreign_keys(dados)
    indices = inspector.get_indexes(dados)

    unique_constraints = inspector.get_unique_constraints(dados)
    check_constraints = inspector.get_check_constraints(dados)

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
            'foreign_key': fk_info
        }


    dicionario[dados] = {
        'capturado_em': datetime.now().isoformat(),
        'nome': dados,
        'qtd_colunas': len(colunas),
        'colunas': info_colunas,
        'indices': [idx['name'] for idx in indices],
        'constraints_check': [c['sqlcheck'] for c in check_constraints]
    }    

# Salvando a lista nos arquivos json nomeados de acordo com as tabelas:
salvar_json = 'historico'
print("\nSalvando dados na pasta")
print()

# Iterando pelo dicionário:
for dados, info_colunas in dicionario.items():
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    caminho_arquivo = os.path.join(salvar_json, f"{dados}_{timestamp}.json")

    try:
        with open(caminho_arquivo, 'w', encoding='utf-8') as f:
            # indent=4 deixa o arquivo organizado para leitura humana
            # # ensure_ascii=False permite caracteres especiais (acentos)
            json.dump(info_colunas, f, indent=4, ensure_ascii=False)
        print(f"Lista de dicionários salvos em: {caminho_arquivo}")
    except Exception as e:
        print(f"Erro nos dicionários: {dados}: {e}")
