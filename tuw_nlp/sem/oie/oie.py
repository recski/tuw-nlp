import argparse
import json
import logging
import sys

from tqdm import tqdm


from tuw_nlp.sem.semparse import get_parser
from tuw_nlp.sem.oie.drs import drs_to_triplets
from tuw_nlp.sem.oie.ucca_oie import ucca_to_triplets
from tuw_nlp.sem.oie.ud import ud_to_triplets
from tuw_nlp.text.preprocessor import Preprocessor


class OIE:
    def __init__(self, args):
        self.parser = get_parser(args)
        self.format = args.format
        self.preproc = Preprocessor(args.preprocessor)

    def graph_to_triplets(self, graph):
        if self.format == "drs":
            yield from drs_to_triplets(graph)
        if self.format == "ucca":
            yield from ucca_to_triplets(graph)
        if self.format == "ud":
            yield from ud_to_triplets(graph)

    def get_triplets(self, sen):
        for graph in self.parser(sen):
            yield from self.graph_to_triplets(graph)


def get_args():
    parser = argparse.ArgumentParser(description="")
    parser.add_argument("-d", "--debug", action="store_true")
    parser.add_argument("-f", "--format", default=None, type=str)
    parser.add_argument("-cd", "--cache-dir", default="cache", type=str)
    parser.add_argument("-cn", "--nlp-cache", default=None, type=str)
    parser.add_argument("-l", "--lang", default=None, type=str, required=True)
    parser.add_argument("-p", "--preprocessor", default=None, type=str)
    parser.add_argument("-w", "--wire57", action="store_true")
    parser.add_argument("-n", "--max-sens", default=None, type=int)
    return parser.parse_args()


def read_wire57_sens(stream):
    data = json.load(stream)
    for dataset_id, sens in data.items():
        for sen in sens:
            yield sen["id"], sen["sent"]


def read_raw_sens(stream):
    for i, line in enumerate(stream):
        yield f"{i}", line.strip()


def write_wire57(output, stream):
    wire57_output = {}
    for sen_id in output:
        triplets = []
        for rel, args in output[sen_id]['triplets']:
            triplet = {
                "arg1": args[0],
                "arg2": args[1],
                "rel": rel,
                "extractor": 'sym',
                "score": 1.0}
            if len(args) > 2:
                triplet["arg3+"]: args[2:]

            triplets.append(triplet)

        wire57_output[sen_id] = triplets

    stream.write(json.dumps(wire57_output))


def write_raw(output, stream):
    for sen_id in output:
        stream.write(
            "{0}\t{1}\t{2}\n".format(
                sen_id,
                output[sen_id]['sen'],
                "\t".join(
                    "{0}({1})".format(rel, ", ".join(args))
                    for rel, args in output[sen_id]["triplets"]
                ),
            )
        )


def main():
    logging.basicConfig(
        format="%(asctime)s : "
        + "%(module)s (%(lineno)s) - %(levelname)s - %(message)s"
    )
    args = get_args()
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.WARNING)

    oie = OIE(args)

    reader = read_wire57_sens if args.wire57 else read_raw_sens

    output = {}
    count = 0
    for sen_id, sen in tqdm(reader(sys.stdin)):
        output[sen_id] = {"sen": sen, "triplets": []}
        for rel, arguments in oie.get_triplets(sen):
            output[sen_id]["triplets"].append((rel, arguments))

        count += 1
        if args.max_sens and args.max_sens == count:
            break

    if args.wire57:
        write_wire57(output, sys.stdout)
    else:
        write_raw(output, sys.stdout)


if __name__ == "__main__":
    main()
