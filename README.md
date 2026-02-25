## Schema Change Detector
Sistema para detectar e classificar mudanças em schemas PostgreSQL, gerando relatórios HTML e no Terminal.


### Sobre o Projeto
---

Desenvolvi esta ferramenta para automatizar a detecção de mudanças em schemas de bancos de dados PostgreSQL. O sistema captura snapshots dos metadados das tabelas, compara versões diferentes e classifica as mudanças por nível de impacto (breaking, warning ou safe), gerando um relatório HTML consolidado e no Terminal.   

Pensei nesse projeto para me auxiliar em pipelines como: migrações de banco de dados para um sistema interno do setor onde trabalhava. Nele eu migrei de SQLite para PostgreSQL, tive que tomar a decisão técnica voltar para SQLite por necessidade, para facilitar a criação de um banco de dados diferente, criei um script para extrair os metadados do schema e salvar em arquivo JSON, para facilitar a criação do novo schema com novos indices e restrições, e na migração dos dados.

### Como Funciona
---
**O sistema funciona em quatro etapas principais:**
1. **Extração de Metadados:**   
O exportador conecta no PostgreSQL e extrai informações completas de cada tabela: nome das colunas, tipos de dados, constraints (NOT NULL, UNIQUE, PRIMARY KEY, FOREIGN KEY) e valores default. Tudo é salvo em arquivos JSON no diretório historico/.   

2. **Comparação de Snapshots:**  
O comparador lê dois snapshots JSON (antes e depois) e identifica três tipos de mudanças:

    Colunas adicionadas,  
    Colunas removidas,  
    Propriedades modificadas (tipo, constraints, defaults).  
    
3. **Classificação de Impacto:**  
Cada mudança detectada é classificada automaticamente:  

**BREAKING (quebra compatibilidade)**:

    Coluna removida,  
    Tipo de dado alterado,  
    NOT NULL adicionado em coluna existente,  
    PRIMARY KEY modificada,  
    DEFAULT VALUE alterado.  

**WARNING (atenção necessária):**

    NOT NULL removido,  
    FOREIGN KEY adicionada,  
    Constraint UNIQUE modificada.  

**SAFE (compatível):**

    Coluna nova adicionada (nullable)

4. **Geração de Relatório:**  
O sistema gera um único arquivo HTML com todas as tabelas analisadas. O relatório mostra um resumo geral (total de breaking/warning/safe) e detalha cada mudança por tabela, com design limpo inspirado em ferramentas de profiling de dados.

---
**Estrutura do Projeto:**  

    Schema-Change-Detector/
    ├── fonte/
    │   ├── exportador.py  # Extração de metadados do PostgreSQL
    │   ├── comparador.py  # Detecta e classifica mudanças
    │   └── relatorio.py  # Gera relatórios HTML
    ├── historico/  # Snapshots JSON das tabelas
    ├── relatorios/
    ├── templates/  # Templates do relatório versão HTML
    │   ├── base.html
    │   ├── secao_breaking.html
    │   ├── secao_safe.html
    │   ├── secao_warning.html
    │   └── tabela.html
    ├── .env  # Credenciais do banco para o exportador.py
    ├── requirements.txt
    └── README.md

### Como Usar
---
**Gerar snapshot inicial (antes das mudanças):**  

    bashpython3 fonte/exportador.py  

Isso cria arquivos `*_em_execucao.json` no diretório historico/ com o estado atual de cada tabela.   

**Fazer alterações no banco de dados:**   
Aplique suas migrations, alterações de schema, ou qualquer mudança estrutural.   

**Gerar novo snapshot e comparar:**   
O exportador renomeia automaticamente os arquivos antigos      
```
# para *_para_analise.json e cria novos *_em_execucao.json
python3 fonte/exportador.py

# Comparar e gerar relatório
python3 fonte/comparador.py
```

O sistema processa todas as tabelas, exibe um resumo no terminal e gera um relatório HTML consolidado em `relatorios/relatorio_consolidado_YYYY-MM-DD_HH-MM-SS.html`.

## Exemplos de Output

**Terminal:**
```
(venv) ┌─[✗]─[yuri@parrot]─[~/Desktop/Projetos/Schema-Change-Detector]
└──╼ $python3 fonte/comparador.py
Iniciando verificacao em: historico

Tabela CATEGORIES

MUDANÇAS DETECTADAS:
Adicionadas: 0 | Removidas: 1 | Modificadas: 2
 • category_name: BREAKING - Coluna removida
 • category_id (BREAKING: NOT NULL adicionado): not_null de False para True
 • category_id (WARNING: Constraint UNIQUE mudou): unique de False para True
Tabela CLIENTES_TESTE

MUDANÇAS DETECTADAS:
Adicionadas: 0 | Removidas: 0 | Modificadas: 4
 • id_teste (BREAKING: NOT NULL adicionado): not_null de False para True
 • nome_teste (WARNING: NOT NULL removido): not_null de True para False
 • nome_teste (BREAKING: PRIMARY KEY mudou): primary_key de False para True
 • nome_teste (WARNING: Constraint UNIQUE mudou): unique de False para True
Tabela CUSTOMERS

MUDANÇAS DETECTADAS:
Adicionadas: 0 | Removidas: 2 | Modificadas: 0
 • customer_email: BREAKING - Coluna removida
 • customer_lname: BREAKING - Coluna removida
Tabela DEPARTMENTS

MUDANÇAS DETECTADAS:
Adicionadas: 0 | Removidas: 1 | Modificadas: 1
 • department_name: BREAKING - Coluna removida
 • department_id (WARNING: NOT NULL removido): not_null de True para False
Tabela ORDER_DETAIL_V

MUDANÇAS DETECTADAS:
Adicionadas: 0 | Removidas: 1 | Modificadas: 2
 • order_customer_id: BREAKING - Coluna removida
 • order_date (BREAKING: NOT NULL adicionado): not_null de False para True
 • order_date (BREAKING: PRIMARY KEY mudou): primary_key de False para True
Tabela ORDER_ITEMS

MUDANÇAS DETECTADAS:
Adicionadas: 0 | Removidas: 0 | Modificadas: 0
Tabela ORDERS

MUDANÇAS DETECTADAS:
Adicionadas: 0 | Removidas: 0 | Modificadas: 0
Tabela PRODUCTS

MUDANÇAS DETECTADAS:
Adicionadas: 0 | Removidas: 0 | Modificadas: 0

Relatório HTML Consolidado: relatorios/relatorio_consolidado_2026-02-25_13-59-15.html
```

**Relatório HTML:**   


## Stack Técnica

**Backend:**  
SQLAlchemy (ORM e reflection),   
psycopg2 (driver PostgreSQL),  
python-dotenv (variáveis de ambiente).

**Frontend:**  
HTML/CSS  

**Arquitetura:**  
3 módulos independentes,   
Separação de responsabilidades,   
JSON como formato intermediário.   

## Limitações Conhecidas

**Detecção de tipo VARCHAR:**  
O sistema detecta mudança de VARCHAR(50) para VARCHAR(100) como "tipo mudou", mas não diferencia se foi aumento (safe) ou redução (breaking). Preciso implementar parsing do tamanho para classificar corretamente.   

**Ordem das colunas:**  
Não detecta reordenação de colunas (ex: coluna A que era a primeira agora é a terceira). Isso raramente importa, mas pode afetar queries que usam SELECT *.  

**Schemas múltiplos:**  
Assume que todas as tabelas estão no schema public. Se você usa múltiplos schemas, precisa adaptar o código do exportador.

## Casos de Uso

**Revisão de Migrations:**  
Antes de aplicar migração, gero um snapshot do ambiente de staging, aplico a migração, gero outro snapshot e analiso o relatório. Se aparecer algum breaking change inesperado, sei que preciso ajustar o código da aplicação antes do deploy.

**Documentação de Mudanças:**  
Os relatórios HTML servem como documentação histórica. Arquivamos junto com as migrations no Git, então qualquer pessoa do time pode entender exatamente o que mudou em cada release.  

**Detecção de Drift:**  
Comparando snapshots de produção vs desenvolvimento, consigo identificar quando alguém fez uma alteração manual no banco que não está nas migrations. Para novos desenvolvedores, mostra o histórico de relatórios para explicar como o schema evoluiu. É muito mais fácil que ler 50 arquivos de migration.

## Contribuindo

Se você encontrar bugs ou tiver sugestões, fique à vontade para abrir uma issue ou pull request. O código está organizado de forma modular justamente para facilitar contribuições.  

## Licença
***MIT License*** - use como quiser, modifique, distribua. Se for útil pra você, fico feliz.

## Autor
Yuri Pontes,  
Cabo do Exército Brasileiro, em transição para engenharia de dados, com foco em Python, SQL e automação de processos.

**LinkedIn:** [Yuri Pontes](https://www.linkedin.com/in/yuri-pontes-4ba24a345/)  
**GitHub:** [yurivski](https://github.com/yurivski)

---
Este projeto nasceu de uma necessidade real no trabalho e foi desenvolvido nas horas vagas.