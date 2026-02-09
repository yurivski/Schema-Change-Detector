import os
import json
import glob
from comparador import comparar

def classificar_mudanca(antigo, novo):
    if antigo is None and novo is not None:
        if not novo.get('not_null', False):
            return "SAFE: Coluna adicionada (nulable)"
    elif 'default' in novo:
        return "SAFE: DEFAULT adicionado em coluna nova"
        
    if antigo is None and novo is not None:
            return "BREAKING: Coluna removida"

    elif antigo is not None and novo is None:
            return "BREAKING: Coluna removida"

    elif antigo is not None and novo is not None:
            return "BREAKING: Tipo de dado mudou"

    if not antigo.get('not_null', False) and novo.get('not_null', True):
            return "BREAKING: NOT NULL adicionado em coluna existente"

    if antigo.get('primary_key') != novo.get('primary_key'):
            return "BREAKING: PRIMARY KEY mudou"

    if antigo.get('default') != novo.get('default'):
            return "BREAKING: DEFAULT VALUE mudou"

    if antigo.get('not_null') == True and novo.get('not_null') == False:
            return "WARNING: NOT NULL removido"

    if not antigo.get('foreign_key') and novo.get('foreign_key'):
            return "WARNING: FOREIGN KEY adicionada"

if __name__ == "__main__":

    colunas_v1 = {"tipo": "VARCHAR", "tamanho": 100, "null": True}
    colunas_v2 = {"tipo": "VARCHAR", "tamanho": 45, "null": True}

    print(classificar_mudanca(colunas_v1, colunas_v2))