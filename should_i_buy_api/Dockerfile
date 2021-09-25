FROM python:3.9 AS lock
WORKDIR /var/lib/pandas/
RUN pip install pipenv==2021.5.29
RUN pipenv --python 3.9
COPY Pipfile* /var/lib/pandas/
RUN pipenv lock --requirements > requirements.txt
RUN pipenv lock --requirements --dev > requirements-dev.txt

FROM python:3.9-alpine
WORKDIR /var/lib/pandas/
COPY --from=lock /var/lib/pandas/ .
RUN apk add --no-cache libstdc++  && \
    apk add --no-cache --virtual .build-deps g++ && \
    ln -s /usr/include/locale.h /usr/include/xlocale.h && \
    pip install $(grep -Eoh 'numpy==[0-9.]+' requirements.txt) && \
    pip install -r requirements.txt && \
    apk del .build-deps

WORKDIR /app

ENV ALPHAVANTAGE_API_KEY=${ALPHAVANTAGE_API_KEY}
ENV DBPASS=${DBPASS}

RUN apk add --no-cache gcc musl-dev linux-headers

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

EXPOSE 80
COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]