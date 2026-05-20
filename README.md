```text
DriftBrake - Em processo de renomeação e desenvolvimento
==========

DriftBrake é uma ferramenta Python para validar contratos de schema antes da execução de 
pipelines de dados.

Ela lê automaticamente o schema atual do PostgreSQL, compara contra um contrato versionado, classifica mudanças por impacto (BREAKING, WARNING, SAFE) e bloqueia pipelines quando detectar mudanças incompatíveis, antes que elas causem falhas em produção.


Exemplo
=======

  Pipelines de dados quebram silenciosamente quando o schema do banco muda sem aviso:

  - coluna removida ou renomeada
  - tipo de dado alterado
  - NOT NULL adicionado sem default
  - foreign key modificada

  Essa ferramenta executa uma validação automática antes do pipeline começar e bloqueia a 
  execução se o banco não estiver compatível com o contrato esperado.


Documentação
============

  Será criado arquivos específicos para cada tipo de documentação, por exemplo:

  - Os detalhes técnicos e conceituais da ferramenta estará no arquivo DOCUMENTATION.md
  - O guia de uso com comandos detalhados por CLI estará no arquivo GUIDE.md
  - Histórico de versões atualizadas no CHANGELOG.md
  - Makefile pra facilitar tarefas comuns do projeto  
```