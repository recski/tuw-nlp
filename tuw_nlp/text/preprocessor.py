from tuw_nlp.text.preprocess.germeval import preprocess_germeval


PREPROCESSOR_FUNCTIONS = {
    "germeval": preprocess_germeval
}


class Preprocessor():
    def __init__(self, what):
        if what is None:
            self.fnc = lambda x: x
        else:
            self.fnc = PREPROCESSOR_FUNCTIONS[what]

    def __call__(self, input_text):
        return self.fnc(input_text)
