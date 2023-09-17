from itertools import count
from typing import Optional, List
from flask import Flask, request, jsonify
from flask_pydantic_spec import FlaskPydanticSpec, Response, Request
from pydantic import BaseModel, Field
from tinydb import TinyDB, Query

server = Flask(__name__)
spec = FlaskPydanticSpec('flask', title='Projeto Stemis')
spec.register(server)
database = TinyDB('database.json')
c = count()

class ProdutoNaoEncontrado(Exception):
    pass

class ItemProduto(BaseModel):
    id: Optional[int] = Field(default_factory=lambda: next(c))
    produto: Optional[str]
    preco: Optional[int]

class Produtos(BaseModel):
    produtos: List[ItemProduto]
    count: int

@server.get('/produtos')
@spec.validate(resp=Response(HTTP_200=Produtos))
def get_produtos():
    """
    Retorna todos os produtos do banco de dados.

    Returns:
        JSON: Lista de produtos e contagem.
    """
    return jsonify(
        Produtos(
            produtos=database.all(),
            count=len(database.all())
        ).dict()
    )

@server.get('/produtos/<int:id>')
@spec.validate(resp=Response(HTTP_200=ItemProduto))
def get_produto(id):
    """
    Retorna um item de produto específico do banco de dados.

    Args:
        id (int): O ID do produto.

    Returns:
        JSON: Dados do produto encontrado.
    """
    try:
        produto = database.search(Query().id == id)[0]
        return jsonify(produto)
    except IndexError:
        raise ProdutoNaoEncontrado()  # Levanta exceção personalizada

@server.post('/produtos')
@spec.validate(
    body=Request(ItemProduto), resp=Response(HTTP_200=ItemProduto)
)
def post_produto():
    """
    Insere um item de produto no banco de dados.

    Returns:
        JSON: Dados do produto inserido.
    """
    body = request.context.body.dict()
    nome = body.get('produto')
    preco = body.get('preco')

    if not nome or not preco:
        return {'error': 'Nome e preço são campos obrigatórios.'}, 400

    database.insert(body)
    return body

@server.put('/produtos/<int:id>')
@spec.validate(
    body=Request(ItemProduto), resp=Response(HTTP_200=ItemProduto)
)
def put_produto(id):
    """
    Altera um item de produto no banco de dados.

    Args:
        id (int): O ID do produto a ser alterado.

    Returns:
        JSON: Dados do produto alterado.
    """
    try:
        ItemProduto = Query()
        body = request.context.body.dict()
        nome = body.get('produto')
        preco = body.get('preco')

        if not nome or not preco:
            return {'error': 'Nome e preço são campos obrigatórios.'}, 400

        database.update(body, ItemProduto.id == id)
        return jsonify(body)
    except IndexError:
        raise ProdutoNaoEncontrado()  # Levanta exceção personalizada

@server.delete('/produtos/<int:id>')
@spec.validate(resp=Response('HTTP_204'))
def delete_produto(id):
    """
    Remove um item de produto do banco de dados.

    Args:
        id (int): O ID do produto a ser removido.

    Returns:
        JSON: Mensagem de sucesso.
    """
    try:
        ItemProduto = Query()
        database.remove((ItemProduto.id == id))
    except IndexError:
        raise ProdutoNaoEncontrado()  # Levanta exceção personalizada
    return jsonify({})

if __name__ == "__main__":
    server.run(debug=True)
