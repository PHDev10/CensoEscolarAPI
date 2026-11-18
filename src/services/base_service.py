from contextlib import contextmanager

import psycopg2

from helpers.environment import LIMIT_MAXIMO_PAGINA
from helpers.logger import logger
from services.excecoes import (
    ErroInternoError,
    ServicoIndisponivelError,
    ValidacaoError,
)

TIPOS_DELETE_VALIDOS = ("logico", "fisico")


class BaseService:
    """Regras comuns aos services: paginação, validação do corpo e do tipo de delete."""

    limit_padrao = 100

    def __init__(self, repositorio):
        self.repositorio = repositorio

    def listar(self, page=None, limit=None):
        """Retorna (registros, total) sempre paginados (page=1, limit=100 por padrão)."""
        page, limit = self._ler_paginacao(page, limit)
        total = self.repositorio.contar_ativos()
        return self.repositorio.listar(page=page, limit=limit), total

    def _ler_paginacao(self, raw_page, raw_limit):
        page, limit = 1, self.limit_padrao
        try:
            if raw_page is not None:
                page = int(raw_page)
            if raw_limit is not None:
                limit = int(raw_limit)
        except (TypeError, ValueError):
            raise ValidacaoError(
                "Os parâmetros 'page' e 'limit' devem ser números inteiros"
            )

        if page < 1 or limit < 1:
            raise ValidacaoError(
                "Os parâmetros 'page' e 'limit' devem ser números inteiros positivos"
            )

        return page, min(limit, LIMIT_MAXIMO_PAGINA)

    @staticmethod
    def _validar_corpo(corpo):
        if not isinstance(corpo, dict) or not corpo:
            raise ValidacaoError("Corpo da requisição inválido: envie um JSON válido")

    @staticmethod
    def _validar_tipo_delete(tipo):
        if tipo not in TIPOS_DELETE_VALIDOS:
            raise ValidacaoError("O parâmetro 'tipo' deve ser 'logico' ou 'fisico'")

    @staticmethod
    @contextmanager
    def _erro_interno(mensagem):
        """Converte falhas do PostgreSQL em erros de serviço, registrando o log."""
        try:
            yield
        except psycopg2.OperationalError:
            logger.exception(mensagem)
            raise ServicoIndisponivelError("Banco de dados indisponível")
        except psycopg2.Error:
            logger.exception(mensagem)
            raise ErroInternoError(mensagem)
