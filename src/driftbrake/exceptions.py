# Exceções personalizadas do DriftBrake.


class SchemaDetectorError(Exception):
    """Exceção base para todos os erros do schema detector."""


class SchemaContractNotFoundError(SchemaDetectorError):
    """Lançada quando o arquivo de contrato de schema não é encontrado ou não pode ser carregado."""


class SchemaConnectionError(SchemaDetectorError):
    """Lançada quando não é possível estabelecer conexão com o banco de dados."""


class BreakingSchemaChangeError(SchemaDetectorError):
    """Lançada quando alterações críticas são detectadas e fail_on está configurado."""


class ConfigurationError(SchemaDetectorError):
    """Lançada quando há um erro no arquivo de configuração ou nas definições."""
