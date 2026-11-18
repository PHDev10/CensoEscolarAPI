import psycopg2
from flask import jsonify

from helpers.logger import logger
from services.excecoes import (
    ConflitoError,
    ErroInternoError,
    NaoEncontradoError,
    ServicoError,
    ServicoIndisponivelError,
    ValidacaoError,
)

STATUS_POR_ERRO = {
    ValidacaoError: 400,
    NaoEncontradoError: 404,
    ConflitoError: 409,
    ErroInternoError: 500,
    ServicoIndisponivelError: 503,
}


def registrar_handlers(app):
    """Traduz exceções (de domínio e do Flask) em respostas JSON com o status HTTP."""

    @app.errorhandler(ServicoError)
    def erro_de_servico(erro):
        return jsonify({"erro": str(erro)}), STATUS_POR_ERRO[type(erro)]

    @app.errorhandler(404)
    def rota_nao_encontrada(_erro):
        return jsonify({"erro": "Rota não encontrada"}), 404

    @app.errorhandler(405)
    def metodo_nao_permitido(_erro):
        return jsonify({"erro": "Método não permitido para esta rota"}), 405

    @app.errorhandler(psycopg2.OperationalError)
    def banco_indisponivel(_erro):
        logger.exception("Banco de dados indisponível")
        return jsonify({"erro": "Banco de dados indisponível"}), 503

    @app.errorhandler(psycopg2.Error)
    def erro_banco(_erro):
        logger.exception("Erro de banco de dados não tratado")
        return jsonify({"erro": "Erro interno: falha no banco de dados"}), 500
