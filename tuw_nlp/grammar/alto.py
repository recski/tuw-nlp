import logging
import os
import subprocess

ALTO_JAR = os.getenv(
    'ALTO_JAR',
    # '/home/recski/tools/alto/build/libs/alto-2.3.7-SNAPSHOT-all.jar')
    #'/home/recski/tools/alto-2.3-SNAPSHOT-jar-with-dependencies.jar')
    '/home/adaamko/projects/wikt2def/fourlang/grammars/alto-2.3.6-SNAPSHOT-all.jar')


def get_alto_command(
        input_fn, grammar_fn, output_fn, input_int, output_int, output_codec,
        timeout=60, memory='32G'):
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
