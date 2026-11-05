"""Contract fault injection, deliberately distinct from real-provider integration."""
from unittest.mock import patch
import httpx
import pytest
from kb.config import Config
from kb.models import Embeddings, ModelFailure, answer


def response(data):
    return httpx.Response(200, json=data, request=httpx.Request('POST', 'https://contract.invalid'))


def config():
    return Config(mode='remote', api_base='https://generation.invalid/v1', api_key='test-key',
                  embedding_base='https://embedding.invalid/v1', embedding_key='embedding-key',
                  embedding_model='embed', chat_model='chat', dimension=32, batch_size=2)


def test_batch_reorders_and_uses_distinct_endpoint():
    cfg = config()
    with patch('httpx.Client.post', return_value=response({'data': [
        {'index': 1, 'embedding': [0.2]*32}, {'index': 0, 'embedding': [0.1]*32}]})) as post:
        result = Embeddings(cfg).get_text_embedding_batch(['one', 'two'])
        assert result[0] == [0.1]*32 and result[1] == [0.2]*32
        assert post.call_args.args[0] == cfg.embedding_base+'/embeddings'
        assert post.call_args.kwargs['headers']['Authorization'] == 'Bearer embedding-key'
        assert post.call_args.kwargs['json']['input'] == ['one', 'two']


@pytest.mark.parametrize('items', [
    [{'index':0,'embedding':[0.1]*32}],
    [{'index':0,'embedding':[0.1]*32},{'index':0,'embedding':[0.2]*32}],
    [{'index':0,'embedding':[0.0]*32},{'index':1,'embedding':[0.2]*32}],
    [{'index':0,'embedding':[True]*32},{'index':1,'embedding':[0.2]*32}],
])
def test_batch_rejects_invalid_contract(items):
    with patch('httpx.Client.post', return_value=response({'data':items})):
        with pytest.raises(ModelFailure):
            Embeddings(config()).get_text_embedding_batch(['one', 'two'])


def test_explicit_refusal_and_empty_response():
    with patch('httpx.Client.post', return_value=response({'choices':[{'message':{'content':'<REFUSE>'}}]})):
        assert answer(config(), 'q', [{'text':'evidence'}])[1]
    with patch('httpx.Client.post', return_value=response({'choices':[{'message':{'content':''}}]})):
        with pytest.raises(ModelFailure):
            answer(config(), 'q', [{'text':'evidence'}])
