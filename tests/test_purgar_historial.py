"""Purga del historial del dataset de HF (`scripts/purgar_historial_hf.py`), con una API falsa: sin red."""

from types import SimpleNamespace as N

import pytest

from scripts import purgar_historial_hf as purga


class _ApiHF:
    def __init__(self, prs=(), con_mapa=True):
        self.commits = ["c3", "c2", "c1"]
        self.tags = ["mapa-1"]
        self.prs = list(prs)
        self.con_mapa = con_mapa
        self.llamadas = []

    def list_repo_refs(self, repo_id, repo_type, include_pull_requests=False):
        assert include_pull_requests
        return N(tags=[N(name=t) for t in self.tags], pull_requests=[N(ref=p) for p in self.prs])

    def list_repo_commits(self, repo_id, repo_type):
        return [N(commit_id=c) for c in self.commits]

    def delete_tag(self, repo_id, tag, repo_type):
        self.llamadas.append(("delete_tag", tag))
        self.tags.remove(tag)

    def list_repo_tree(self, repo_id, path_in_repo, repo_type):
        if not self.con_mapa:
            raise type("EntryNotFoundError", (Exception,), {})("404")
        return iter([N(path="data/mapa/estado.json")])

    def create_commit(self, repo_id, repo_type, operations, commit_message):
        self.llamadas.append(("borrar", [o.path_in_repo for o in operations]))
        self.commits.insert(0, "c4")

    def super_squash_history(self, repo_id, repo_type, branch, commit_message):
        self.llamadas.append(("squash", branch))
        self.commits = ["s1"]


def test_purga_borra_tags_retira_el_mapa_y_aplasta_main():
    api = _ApiHF()
    res = purga.purgar(api, "repo", retirar_mapa=True, servida=lambda repo, rev: False)
    assert api.llamadas == [("delete_tag", "mapa-1"), ("borrar", ["data/mapa/"]), ("squash", "main")]
    assert res["purgado"] and res["commit"] == "s1" and res["mapa_retirado"] and res["revisiones_aun_servidas"] == []


def test_avisa_si_una_revision_vieja_se_sigue_sirviendo():
    res = purga.purgar(_ApiHF(con_mapa=False), "repo", retirar_mapa=True, servida=lambda repo, rev: rev == "c2")
    assert not res["mapa_retirado"] and res["revisiones_aun_servidas"] == ["c2"]


@pytest.mark.parametrize("kwargs", [{"dry_run": True}, {"prs": ["refs/pr/1"]}])
def test_simulada_o_con_prs_de_hf_no_toca_nada(kwargs):
    api = _ApiHF(prs=kwargs.pop("prs", ()))
    res = purga.purgar(api, "repo", retirar_mapa=True, **kwargs)
    assert api.llamadas == [] and not res["purgado"]


def test_sin_confirmacion_no_purga(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["purgar", "--confirmar", "otro/repo"])
    monkeypatch.setenv("HF_TOKEN", "x")
    assert purga.main() == 2
    assert "--confirmar" in capsys.readouterr().err
