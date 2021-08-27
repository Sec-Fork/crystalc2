import random


def randomize_string_case(ps_script):
    # todo only apply to cmdlets etc.
    return "".join(random.choice([char.upper(), char]) for char in ps_script)


def obfuscate_powershell(ps_script: str) -> str:
    # ps_script = randomize_string_case(ps_script)
    # TODO
    raise NotImplementedError
    # return ps_script