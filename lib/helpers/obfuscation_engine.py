import random


def randomize_string_case(ps_script):
    return "".join(random.choice([char.upper(), char]) for char in ps_script)


def obfuscate_powershell(ps_script: str) -> str:
    ps_script = randomize_string_case(ps_script)
    # TODO more
    return ps_script