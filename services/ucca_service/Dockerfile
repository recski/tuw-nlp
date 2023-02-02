FROM --platform=linux/amd64 continuumio/miniconda3
RUN apt-get update && apt-get -y install gcc
#RUN apt-get install -y python3-dev build-essential cmake mercurial

RUN conda config --append channels conda-forge
RUN conda create -n env python=3.6
RUN echo "source activate env" > ~/.bashrc
ENV PATH /opt/conda/envs/env/bin:$PATH

# RUN conda install gxx_linux-64
# RUN conda install gcc_linux-64
RUN apt-get install -y git
RUN apt-get -y install cmake
RUN apt-get install -y g++
RUN apt-get install curl
RUN pip install pip -U
RUN pip install setuptools -U

WORKDIR /data
RUN git clone https://github.com/adaamko/tupa.git /data/tupa
RUN pip install cython
RUN pip install charset-normalizer==2.0.12
RUN pip install idna==3.3
#RUN pip install git+https://github.com/clab/dynet#egg=dynet

RUN pip install tupa
#RUN cd /data/tupa && pip install -r requirements_exact.txt

WORKDIR /data/tupa
RUN curl -LO https://github.com/huji-nlp/tupa/releases/download/v1.3.10/ucca-bilstm-1.3.10.tar.gz
RUN tar xvzf ucca-bilstm-1.3.10.tar.gz
RUN cp -r /data/tupa/vocab /data/tupa/server/vocab
WORKDIR /data/tupa/server
RUN pip install -r requirements.txt
RUN python -m spacy download en_core_web_md

CMD [  "python" , "parse_server.py" ]
