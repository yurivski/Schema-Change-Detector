```Markdown
DriftBrake
==========

DriftBrake é uma ferramenta Python para validar contratos de schema antes da execução de
pipelines de dados.

Ela lê automaticamente o schema atual do PostgreSQL, compara contra um contrato versionado,
classifica mudanças por impacto (BREAKING, WARNING, SAFE) e bloqueia pipelines quando detectar
mudanças incompatíveis, antes que elas causem falhas em produção.


A ferramenta
============

  DriftBrake não é uma ferramenta de migration. Ela não aplica mudanças no banco e não gera
  scripts SQL.

  Ela atua ANTES da execução de pipelines, verificando se o banco real ainda respeita o
  contrato esperado pelos consumidores de dados.


Exemplo
=======

  Pipelines de dados quebram silenciosamente quando o schema do banco muda sem aviso:

  - coluna removida ou renomeada
  - tipo de dado alterado
  - NOT NULL adicionado sem default
  - foreign key modificada

  Essa ferramenta executa uma validação automática antes do pipeline começar e bloqueia a
  execução se o banco não estiver compatível com o contrato esperado.

  Uso rápido:

    driftbrake init     # cria o contrato schema.lock.json
    driftbrake check    # verifica se o banco mudou
    driftbrake diff     # compara dois estados sem tocar no contrato


Documentação
============

  - DOCUMENTATION.md  (Referência técnica completa: CLI, biblioteca Python, arquitetura)
  - CHANGELOG.md      (Histórico de versões)
  - Makefile          (Atalhos pra tarefas comuns do projeto)
```
