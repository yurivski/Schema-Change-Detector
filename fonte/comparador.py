"""
Arquivo que irá comparar os metadados e identificar se houve alteração, 
qual, quando e onde.
"""

import os
import json
import glob
from exportador import extrair_metadados
from classificador import classificar_mudanca

def carregar_json(caminho_arquivo):
    try:
        with open(caminho_arquivo, 'r', encoding='utf-8') as arquivo:
            dados = json.load(arquivo)
            return dados
    except json.JSONDecodeError:
        print(f"Erro no '{caminho_arquivo}'")
        return None
    except Exception as e:
        print (f"Deu erro: {e}")
        return None


def analisar_mudancas(colunas_antigas, colunas_novas):
    antigas_keys = set(colunas_antigas.keys())
    novas_keys = set(colunas_novas.keys())
    
    comuns = antigas_keys & novas_keys
    removidas = antigas_keys - novas_keys
    adicionadas = novas_keys - antigas_keys
    
    return {
        "comuns": list(comuns),
        "removidas": list(removidas),
        "adicionadas": list(adicionadas)
    }

def comparar(colunas_antigas, colunas_novas, nome_coluna):
    mudancas = []
    comparar_campos = ['tipo', 'not_null', 'default', 'primary_key', 'unique', 'foreign_key']

    for campo in comparar_campos:
        v_antigo = colunas_antigas.get(campo)
        v_novo = colunas_novas.get(campo)

        if v_antigo != v_novo:
            mudancas.append({
                'tipo': 'type_changed' if campo == 'tipo' else 'property_changed',  
                'coluna': nome_coluna,
                'campo': campo,
                'valor_antigo': v_antigo,
                'valor_novo': v_novo

            })

    return mudancas

def comparar_jsons(antigo, novo):
    dados_antes = carregar_json(antigo)
    dados_depois = carregar_json(novo)
    if dados_antes is None or dados_depois is None:
        return "Erro ao carregar arquivos."
    
    lista_mudancas = []
    analise = analisar_mudancas(
    dados_antes['colunas'],
    dados_depois['colunas']
)

    # Mensagem de alterações nas colunas: (existente para None = coluna removida)
    for col in analise['adicionadas']:
        lista_mudancas.append({
            'tipo': 'column_added',
            'coluna': col,
            'campo': 'alteracao',
            'valor_antigo': None,
            'valor_novo': 'adicionado'
        })
    for col in analise['removidas']:
        lista_mudancas.append({
            'tipo': 'column_removed',
            'coluna': col,
            'campo': 'alteracao',
            'valor_antigo': 'existente',
            'valor_novo': None
        })

    for col in analise['comuns']:
        detalhes = comparar(dados_antes['colunas'][col], dados_depois['colunas'][col], col)
        lista_mudancas.extend(detalhes)
    return lista_mudancas

def exibir_mudancas(mudancas):
    adicionadas = [m for m in mudancas if m['tipo'] == 'column_added']
    removidas = [m for m in mudancas if m['tipo'] == 'column_removed']
    modificadas = [m for m in mudancas if m['tipo'] in ['type_changed', 'property_changed']]

    print("\nMUDANÇAS DETECTADAS:")
    print(f"Adicionadas: {len(adicionadas)} | Removidas: {len(removidas)} | Modificadas: {len(modificadas)}")
    
    # Exibe colunas adicionadas, removidas e modificadas
    for m in adicionadas:
        print(f" • {m['coluna']}: SAFE - Coluna adicionada")

    for m in removidas:
        print(f" • {m['coluna']}: BREAKING - Coluna removida")

    for m in modificadas:
        print(f" • {m['coluna']} - {m['campo']}: de {m['valor_antigo']} para {m['valor_novo']}") 


def teste_comparacao():
    pasta = 'historico'
    padrao = os.path.join(pasta, "*em_execucao.json")
    arquivo_antes = glob.glob(padrao)

    if not arquivo_antes:
        print(f"Nenhum arquivo 'em_execucao.json' encontrado na pasta '{pasta}'")
        return

    print(f"Iniciando verificacao em: {pasta}")

    for caminho_antes in arquivo_antes:
        caminho_depois = caminho_antes.replace("em_execucao.json", "para_analise.json")
        nome_tabela = os.path.basename(caminho_antes).replace("_em_execucao.json", "")
        
        if os.path.exists(caminho_depois):
            print(f"\nTabela {nome_tabela.upper()}")

            resultado = comparar_jsons(caminho_depois, caminho_antes)

            if isinstance(resultado, list):
                exibir_mudancas(resultado)
            else:
                print(f"Erro: {resultado}")
        else:
            print(f"\nPar 'depois' não encontrado para {caminho_antes}")

if __name__ == "__main__":
    teste_comparacao()