import datetime
import os

from tuw_nlp.common.utils import ensure_dir
from tuw_nlp.grammar.alto import get_rule_string, run_alto
from tuw_nlp.grammar.utils import get_dummy_input


class IRTGGrammar():
    def __init__(self):
        self.tmpdir = os.getenv("TUWNLP_TMPDIR", "tmp")
        ensure_dir(self.tmpdir)

    def transform_input(self, input_obj):
        return input_obj

    def transform_output(self, output_obj):
        return output_obj

    def parse(self, input_obj, input_int, output_int, output_codec):
        if input_int not in self.interpretations:
            raise ValueError(f"unknown interpretation: {input_int}")
        transformed_input = self.transform_input(input_obj)
        output = self.run(
            transformed_input, input_int, output_int, output_codec)
        return self.transform_output(output)

    def gen_file_names(self):
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        path = os.path.join(self.tmpdir, timestamp)
        ensure_dir(path)
        return tuple(os.path.join(path, fn) for fn in (
            "input.txt", "grammar.irtg", "output.txt"))

    def gen_grammar_header(self):
        for name, algebra in self.interpretations.items():
            yield f"interpretation {name}: {algebra}"

    def gen_input_header(self, input_int):
        algebra = self.interpretations[input_int]
        yield "# IRTG unannotated corpus file, v1.0"
        yield f"# interpretation {input_int}: {algebra}"

    def write_input_file(self, transformed_input, input_fn, input_int):
        input_alg = self.interpretations[input_int]
        dummy_input = get_dummy_input(input_alg)
        with open(input_fn, 'w') as f:
            for line in self.gen_input_header(input_int):
                f.write(f"{line}\n")
            f.write('\n')
            f.write(f"{transformed_input}\n")
            f.write(f"{dummy_input}\n")

    def write_grammar_file(self, grammar_fn):
        with open(grammar_fn, 'w') as f:
            for line in self.gen_grammar_header():
                f.write(f"{line}\n")
            f.write('\n')
            term_rule_strings = []
            for irtg_rule, interpretations, rule_type in self.gen_rules():
                rule_string = get_rule_string(irtg_rule, interpretations)
                if rule_type == 'terminal':
                    term_rule_strings.append(rule_string)
                    continue
                f.write(f"{rule_string}\n")

            for rule_string in term_rule_strings:
                f.write(f"{rule_string}\n")

    def create_alto_files(self, transformed_input, input_int):
        input_fn, grammar_fn, output_fn = self.gen_file_names()
        self.write_input_file(transformed_input, input_fn, input_int)
        self.write_grammar_file(grammar_fn)
        return input_fn, grammar_fn, output_fn

    def run(self, transformed_input, input_int, output_int, output_codec):
        input_fn, grammar_fn, output_fn = self.create_alto_files(
            transformed_input, input_int)
        success = run_alto(
            input_fn, grammar_fn, output_fn, input_int, output_int,
            output_codec)
        if success:
            outputs, _ = self.parse_output(output_fn)
            return outputs[0]
        return None

    def parse_output(self, output_fn):
        derivs, outputs = [], []
        with open(output_fn) as f:
            for i, raw_line in enumerate(f):
                line = raw_line.strip()
                if line in ('null', '<null>'):
                    line = None
                if i % 2 == 0:
                    derivs.append(line)
                else:
                    outputs.append(line)

        return outputs, derivs

    def gen_rules(self):
        raise NotImplementedError
