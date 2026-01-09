import subprocess


def verify(path: str) -> bool:
    result = subprocess.run(
        ["python", "agents/verifier/verify_payload.py", path],
        capture_output=True,
        text=True
    )
    return result.returncode == 0
