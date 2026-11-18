from flask import jsonify

from serializers import dump


def resposta_lista(registros, serializacao, total):
    """Serializa uma lista paginada e expõe o total de registros em X-Total-Count"""
    resposta = jsonify(dump(registros, many=True, **serializacao))
    resposta.headers["X-Total-Count"] = str(total)
    return resposta, 200
