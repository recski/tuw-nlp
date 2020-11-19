import datetime
import json
import logging
import os
import random
from collections import defaultdict

from dict_recursive_update import recursive_update

from tuw_nlp.common.utils import ensure_dir
from tuw_nlp.grammar.alto import get_rule_string, run_alto
from tuw_nlp.grammar.utils import get_dummy_input


class IRTGCache():
    @staticmethod
    def load(fn):
        with open(fn) as f:
            cache = json.load(f)
        ints = sorted(cache.keys())
        logging.warning(f'loaded cache from {fn} with interpretations: {ints}')
        obj = IRTGCache(ints, fn)
        obj.cache.update(cache)
        return obj

    def update_file(self, fn):
        old = IRTGCache.load(fn)
        assert old.interpretations == self.interpretations
        recursive_update(old.cache, self.cache)
        with open(fn, 'w') as f:
            json.dump(old.cache, f)
        logging.warning(f'updated cache in {fn}')

    def __init__(self, interpretations, fn, new=False):
        self.fn = fn
        self.interpretations = interpretations
        self.cache = {i: {} for i in interpretations}
        if new:
            with open(fn, 'w') as f:
                json.dump(self.cache, f)

    def get(
            self, input_obj, input_int,
            output_int, output_codec, create_path=False):

        if input_obj not in self.cache[input_int]:
            if create_path:
                self.cache[input_int][input_obj] = defaultdict(
                    lambda: defaultdict(dict))
        else:
            return self.cache[input_int][input_obj][output_int].get(
                output_codec)

        return None

    def add(self, input_obj, input_int, output_int, output_codec, output_obj):

        assert self.get(
            input_obj, input_int, output_int, output_codec,
            create_path=True) is None

        self.cache[input_int][input_obj][output_int][output_codec] = output_obj


class IRTGGrammar():
    def __init__(self, **kwargs):
        self.tmpdir = os.getenv("TUWNLP_TMPDIR", "tmp")
        ensure_dir(self.tmpdir)
        self.load_cache(**kwargs)

    def load_cache(self, **kwargs):
        cache_path = kwargs.get('cache_dir') or 'cache'
        cache_fn = kwargs.get('cache_fn') or f'{self.__class__.__name__}.json'
        ensure_dir(cache_path)
        fn = os.path.join(cache_path, cache_fn)
        if not os.path.exists(fn):
            logging.warning(f'setting up new cache file: {fn}')
            self.cache = IRTGCache(
                sorted(self.interpretations.keys()), fn, new=True)
        else:
            logging.warning(f'loading cache from file: {fn}')
            self.cache = IRTGCache.load(fn)
        self.cache_fn = fn

    def preprocess_input(self, input_obj, **kwargs):
        return input_obj

    def postprocess_output(self, output_obj, **kwargs):
        return output_obj

    def _parse(self, input_obj, input_int, output_int, output_codec, **kwargs):
        output = self.run(
            input_obj, input_int, output_int, output_codec)
        return self.postprocess_output(output, **kwargs)

    def parse(self, orig_input, input_int, output_int, output_codec, **kwargs):
        if input_int not in self.interpretations:
            raise ValueError(f"unknown interpretation: {input_int}")
        if output_int not in self.interpretations:
            raise ValueError(f"unknown interpretation: {output_int}")

        input_obj = self.preprocess_input(orig_input, **kwargs)

        cached = self.cache.get(
            input_obj, input_int, output_int, output_codec)

        if cached is None:
            output_obj = self._parse(
                input_obj, input_int, output_int, output_codec, **kwargs)
            self.cache.add(
                input_obj, input_int, output_int, output_codec, output_obj)
            self.cache.update_file(self.cache_fn)
            return output_obj
        return cached

    def gen_file_names(self):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        rand_id = random.randrange(100000, 999999)
        path = os.path.join(self.tmpdir, f"{timestamp}_{rand_id}")
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
            for rule_string in self.gen_rule_strings():
                f.write(f"{rule_string}\n")

    def gen_rule_strings(self):
        term_rule_strings = []
        for irtg_rule, interpretations, rule_type in self.gen_rules():
            rule_string = get_rule_string(irtg_rule, interpretations)
            if rule_type == 'terminal':
                term_rule_strings.append(rule_string)
                continue
            yield rule_string
        yield from term_rule_strings

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
