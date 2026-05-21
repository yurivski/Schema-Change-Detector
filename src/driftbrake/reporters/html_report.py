"""
Reporter HTML - gera relatórios HTML usando os templates existentes em templates/.

Adapta os templates legados {{placeholder}} para o novo modelo DiffResult
usando Jinja2 para renderização.
"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any

from driftbrake.models import DiffResult, SchemaChange, Severity


_TEMPLATES_DIR = Path(__file__).parent.parent.parent.parent.parent / "templates"


def _find_templates_dir() -> Path:
    """
    Localiza o diretório templates/ relativo à raiz do projeto.

    Pesquisa a partir do local do arquivo para cima até encontrar um diretório
    contendo base.html.
    """
    candidates = [
        Path(__file__).parent.parent.parent.parent.parent / "templates",
        Path(__file__).parent.parent.parent.parent / "templates",
        Path(__file__).parent.parent.parent / "templates",
        Path("templates"),
    ]
    for candidate in candidates:
        if candidate.exists() and (candidate / "base.html").exists():
            return candidate
    raise FileNotFoundError(
        "Could not find the templates/ directory. "
        "Make sure it exists at the project root."
    )


def _render_template(template_str: str, context: dict[str, Any]) -> str:
    """
    Renderiza uma string de template usando Jinja2 se disponível,
    caindo para substituição simples {{key}} caso contrário.
    """
    try:
        from jinja2 import Environment, BaseLoader
        env = Environment(loader=BaseLoader(), autoescape=False)
        # Converte {{key}} para {{ key }} para compatibilidade com Jinja2
        jinja_template = re.sub(r"\{\{(\w+)\}\}", r"{{ \1 }}", template_str)
        tpl = env.from_string(jinja_template)
        return tpl.render(**context)
    except ImportError:
        result = template_str
        for key, value in context.items():
            result = result.replace(f"{{{{{key}}}}}", str(value))
        return result


class HtmlReporter:
    """
    Gera um relatório HTML de alterações de schema usando templates legados.

    Os templates usam sintaxe {{placeholder}} e estão localizados em templates/.
    """

    def __init__(
        self,
        output_path: str | Path,
        templates_dir: str | Path | None = None,
    ) -> None:
        self.output_path = Path(output_path)
        if templates_dir is not None:
            self.templates_dir = Path(templates_dir)
        else:
            self.templates_dir = _find_templates_dir()

    def _load_template(self, name: str) -> str:
        path = self.templates_dir / f"{name}.html"
        if not path.exists():
            raise FileNotFoundError(f"Template not found: {path}")
        return path.read_text(encoding="utf-8")

    def write(self, result: DiffResult) -> None:
        """
        Renderiza e grava o relatório HTML no disco.
        result: O DiffResult a ser renderizado.
        """
        html = self.render(result)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.output_path.write_text(html, encoding="utf-8")

    def render(self, result: DiffResult) -> str:
        # Renderiza o relatório HTML completo como string.
        base_template = self._load_template("base")
        tabelas_html = self._render_all_tables(result)

        timestamp = result.compared_at.strftime("%d/%m/%Y às %H:%M:%S")

        return _render_template(
            base_template,
            {
                "timestamp": timestamp,
                "total_breaking": result.total_breaking,
                "total_warning": result.total_warnings,
                "total_safe": result.total_safe,
                "tabelas_html": tabelas_html,
            },
        )

    def _render_all_tables(self, result: DiffResult) -> str:
        if not result.changes:
            return (
                '<div class="table-section">'
                '<div class="no-changes">Nenhuma mudança detectada</div>'
                "</div>"
            )

        changes_by_table = result.changes_by_table()
        html_parts = []

        for table_key, changes in changes_by_table.items():
            # table_key está no formato "schema.tabela"
            parts = table_key.split(".", 1)
            table_display = parts[1].upper() if len(parts) == 2 else table_key.upper()

            breaking = [c for c in changes if c.severity == Severity.BREAKING]
            warnings = [c for c in changes if c.severity == Severity.WARNING]
            safe = [c for c in changes if c.severity == Severity.SAFE]

            sections_html = ""
            if breaking:
                sections_html += self._render_section(breaking, "breaking")
            if warnings:
                sections_html += self._render_section(warnings, "warning")
            if safe:
                sections_html += self._render_section(safe, "safe")

            table_template = self._load_template("tabela")
            table_html = _render_template(
                table_template,
                {
                    "nome_tabela": table_display,
                    "breaking": len(breaking),
                    "warning": len(warnings),
                    "safe": len(safe),
                    "secoes_html": sections_html,
                },
            )
            html_parts.append(table_html)

        return "\n".join(html_parts)

    def _render_section(self, changes: list[SchemaChange], tipo: str) -> str:
        template = self._load_template(f"secao_{tipo}")
        rows = "".join(self._render_row(change, tipo) for change in changes)
        return _render_template(
            template,
            {
                "count": len(changes),
                "linhas": rows,
            },
        )

    def _render_row(self, change: SchemaChange, tipo: str) -> str:
        col = f"<code>{change.column_name}</code>" if change.column_name else "—"
        change_label = self._change_label(change, tipo)
        old_val = self._format_value(change.old_value)
        new_val = self._format_value(change.new_value)

        if tipo == "safe":
            return (
                f"<tr>"
                f"<td>{col}</td>"
                f"<td><span class='badge-safe'>{change_label}</span></td>"
                f"<td>{change.description}</td>"
                f"</tr>"
            )

        return (
            f"<tr>"
            f"<td>{col}</td>"
            f"<td><span class='badge-{tipo}'>{change_label}</span></td>"
            f"<td>{old_val}</td>"
            f"<td>{new_val}</td>"
            f"</tr>"
        )

    def _change_label(self, change: SchemaChange, tipo: str) -> str:
        labels = {
            "table_added": "Tabela Adicionada",
            "table_removed": "Tabela Removida",
            "column_added": "Coluna Adicionada",
            "column_removed": "Coluna Removida",
            "type_changed": "Tipo Alterado",
            "nullable_changed": "Nullable Alterado",
            "default_changed": "Default Alterado",
            "primary_key_changed": "Primary Key Mudou",
            "unique_changed": "Unique Mudou",
            "foreign_key_changed": "Foreign Key Mudou",
            "foreign_key_added": "Foreign Key Adicionada",
            "ordinal_position_changed": "Posição Alterada",
            "possible_rename": "Possível Rename",
        }
        return labels.get(change.change_type.value, change.change_type.value)

    def _format_value(self, value: object) -> str:
        if value is None:
            return "—"
        s = str(value)
        if s and s != "None":
            return f"<code>{s}</code>"
        return "—"
