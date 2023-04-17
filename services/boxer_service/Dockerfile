FROM python:3.9-slim
RUN apt-get update

RUN apt-get install opam -y
RUN apt-get install wget m4 unzip librsvg2-bin curl bubblewrap -y
RUN opam init --disable-sandboxing
RUN opam switch create 4.13.1 4.13.1
RUN eval $(opam env --switch=4.13.1)
RUN opam remote add grew "http://opam.grew.fr"
RUN opam install grew grewpy -y
RUN eval $(opam env)
RUN opam uninstall grew grewpy libcaml-grew -y
RUN opam install grew.1.8.1 grewpy.1.8.0 libcaml-grew.1.9.2 -y

RUN eval $(opam env)
WORKDIR /data
RUN git clone https://github.com/adaamko/ud-boxer.git /data/ud-boxer

WORKDIR /data/ud-boxer

RUN pip install -r requirements/requirements.txt
RUN pip install flask

CMD [  "bash" , "start.sh" ]