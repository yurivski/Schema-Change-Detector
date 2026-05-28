# Implementações do protocolo Prompter.

from __future__ import annotations


class StdinPrompter:
    """Lê confirmação via input(). Default em modo interativo."""

    def confirm_create_contract(self, contract_path: str) -> bool:
        try:
            answer = (
                input("Create a new contract from the current PostgreSQL schema? [Y/n]: ")
                .strip()
                .lower()
            )
        except (EOFError, KeyboardInterrupt):
            return False
        return answer in ("", "y", "yes")

    def confirm_continue_with_warnings(self, result) -> bool:
        try:
            answer = input("Continue pipeline execution? [y/N]: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            return False
        return answer in ("", "y", "yes")

    def confirm_continue_with_safe(self, result) -> bool:
        try:
            answer = input("Continue pipeline execution? [y/N]: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            return False
        return answer in ("", "y", "yes")


class NonInteractivePrompter:
    """Sempre retorna False. Usado quando interactive efetivo == False."""

    def confirm_create_contract(self, contract_path: str) -> bool:
        return False

    def confirm_continue_with_warnings(self, result) -> bool:
        return False

    def confirm_continue_with_safe(self, result) -> bool:
        return False
