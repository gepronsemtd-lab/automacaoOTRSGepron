import requests

from core.otrs_service import _post_com_retry


class SessaoFake:
    def __init__(self, respostas):
        self.respostas = respostas
        self.chamadas = 0

    def post(self, *args, **kwargs):
        resposta = self.respostas[self.chamadas]
        self.chamadas += 1
        return resposta


def criar_resposta(status_code):
    resposta = requests.Response()
    resposta.status_code = status_code
    resposta.url = "https://atendimento.sead.pb.gov.br/otrs/index.pl"
    resposta._content = b"ok"
    return resposta


def test_post_com_retry_repete_erro_502_e_retorna_sucesso(monkeypatch):
    monkeypatch.setattr("core.otrs_service.time.sleep", lambda _: None)

    sessao = SessaoFake([criar_resposta(502), criar_resposta(200)])

    resposta = _post_com_retry(
        sessao,
        url="https://atendimento.sead.pb.gov.br/otrs/index.pl",
        tentativas=2,
        espera_inicial=1,
    )

    assert resposta.status_code == 200
    assert sessao.chamadas == 2


def test_post_com_retry_nao_repete_erro_nao_transitorio(monkeypatch):
    monkeypatch.setattr("core.otrs_service.time.sleep", lambda _: None)

    sessao = SessaoFake([criar_resposta(401)])

    try:
        _post_com_retry(
            sessao,
            url="https://atendimento.sead.pb.gov.br/otrs/index.pl",
            tentativas=3,
            espera_inicial=1,
        )
    except requests.exceptions.HTTPError:
        pass
    else:
        raise AssertionError("HTTPError deveria ser relancado para erro nao transitorio")

    assert sessao.chamadas == 1
