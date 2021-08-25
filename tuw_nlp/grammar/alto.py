import logging
import os
import subprocess

ALTO_JAR = os.getenv('ALTO_JAR')
if ALTO_JAR == None:
    if os.path.isfile(os.path.expanduser("~/tuw_nlp_resources/alto-2.3.6-SNAPSHOT-all.jar")):
        ALTO_JAR = os.path.expanduser(
            "~/tuw_nlp_resources/alto-2.3.6-SNAPSHOT-all.jar")

assert ALTO_JAR, 'ALTO is not downloaded, for setup please use tuw_nlp.download_alto(), or download ALTO manually and set the ALTO_JAR enviroment variable to the correct path'


def get_alto_command(
        input_fn, grammar_fn, output_fn, input_int, output_int, output_codec,
        timeout=60, memory='32G'):
    if os.name == 'nt':  # timeout not available on windows
        return [
            'java', f'-Xmx{memory}', '-cp',
            ALTO_JAR,
            'de.up.ling.irtg.script.ParsingEvaluator', input_fn,
            '-g', grammar_fn, '-I', input_int,
            '-O', f"{output_int}={output_codec}", '-o', output_fn]
    elif os.name == "posix":
        return [
            'java', f'-Xmx{memory}', '-cp',
            ALTO_JAR,
            'de.up.ling.irtg.script.ParsingEvaluator', input_fn,
            '-g', grammar_fn, '-I', input_int,
            '-O', f"{output_int}={output_codec}", '-o', output_fn]
    else:
        return [
            'timeout', str(timeout), 'java', f'-Xmx{memory}', '-cp',
            ALTO_JAR,
            'de.up.ling.irtg.script.ParsingEvaluator', input_fn,
            '-g', grammar_fn, '-I', input_int,
            '-O', f"{output_int}={output_codec}", '-o', output_fn]


def get_rule_string(irtg_rule, interpretations):
    lines = [irtg_rule] + [
        f"[{int_name}] {int_rule}"
        for int_name, int_rule in interpretations.items()]
    return "\n".join(lines)


def run_alto(
        input_fn, grammar_fn, output_fn, input_int, output_int, output_codec,
        timeout=60, memory='32G'):
    command = get_alto_command(
        input_fn, grammar_fn, output_fn, input_int, output_int, output_codec,
        timeout=60, memory='32G')
    logging.info("running alto: {}".format(" ".join(command)))
    cproc = subprocess.run(command)
    if cproc.returncode == 124:
        logging.warning('alto timeout')
        return False
    elif cproc.returncode != 0:
        logging.warning('alto error')
        return False

    return True
