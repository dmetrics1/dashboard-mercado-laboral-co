"""
Push al repositorio de GitHub usando el token del archivo .env

Ejecutar desde la raiz del proyecto:
    python scripts/push.py
    python scripts/push.py "mensaje del commit personalizado"
"""
import os
import subprocess
import sys
from pathlib import Path


def cargar_env() -> dict:
    env_path = Path(__file__).parent.parent / ".env"
    if not env_path.exists():
        raise FileNotFoundError(
            f"No se encontro {env_path}\n"
            "Crea el archivo .env con tu GITHUB_TOKEN."
        )
    variables = {}
    for linea in env_path.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#"):
            continue
        if "=" in linea:
            clave, valor = linea.split("=", 1)
            variables[clave.strip()] = valor.strip()
    return variables


def run(cmd: str) -> str:
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())
    return result.stdout.strip()


if __name__ == "__main__":
    env = cargar_env()

    token  = env.get("GITHUB_TOKEN", "")
    user   = env.get("GITHUB_USER", "")
    repo   = env.get("GITHUB_REPO", "")
    branch = env.get("GITHUB_BRANCH", "master")

    if not token or token == "pega_tu_token_aqui":
        print("ERROR: Abre el archivo .env y pega tu token en GITHUB_TOKEN")
        sys.exit(1)

    remote_url = f"https://{token}@github.com/{user}/{repo}.git"

    print(f"Subiendo a github.com/{user}/{repo} (rama {branch}) ...")
    try:
        # Configura remote con token (solo para este push, no se guarda en config)
        run(f'git remote set-url origin "{remote_url}"')
        output = run(f"git push origin {branch}")
        print("Push exitoso.")
        if output:
            print(output)
    finally:
        # Restaura la URL sin token para que no quede en git config
        url_limpia = f"https://github.com/{user}/{repo}.git"
        run(f'git remote set-url origin "{url_limpia}"')
        print(f"Remote restaurado a: {url_limpia}")
