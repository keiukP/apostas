"""Servidor local: serve site/ e expõe o botão de ativar/desativar o modo contínuo.

Só escuta em 127.0.0.1. Uso: python servidor.py
"""
from __future__ import annotations

import json
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import controlo

RAIZ = Path(__file__).resolve().parent
SITE = RAIZ / "site"
PORTA = 8800


class Pedidos(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api/estado":
            return self._json(controlo.estado())
        super().do_GET()

    def do_POST(self):
        if self.path != "/api/ativo":
            return self._json({"erro": "não encontrado"}, 404)
        tamanho = int(self.headers.get("Content-Length", 0))
        try:
            corpo = json.loads(self.rfile.read(tamanho) or b"{}")
        except json.JSONDecodeError:
            return self._json({"erro": "JSON inválido"}, 400)
        if not isinstance(corpo.get("ativo"), bool):
            return self._json({"erro": "campo 'ativo' em falta"}, 400)
        return self._json(controlo.definir_ativo(corpo["ativo"]))

    def _json(self, dados: dict, codigo: int = 200):
        corpo = json.dumps(dados, ensure_ascii=False).encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(corpo)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(corpo)


def main() -> None:
    SITE.mkdir(exist_ok=True)
    servidor = ThreadingHTTPServer(("127.0.0.1", PORTA), partial(Pedidos, directory=str(SITE)))
    print(f"Site em http://127.0.0.1:{PORTA}/index.html (Ctrl+C para parar)")
    servidor.serve_forever()


if __name__ == "__main__":
    main()
