FROM python:3-slim

RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends \
        sudo \
        ca-certificates \
        netbase \
        pdftohtml \
    && apt-get clean \
    && apt-get autoremove \
    && rm -rf /var/lib/apt/lists/*

ENV USER_NAME="user" \
    USER_UID="1000" \
    USER_GID="1000"

RUN groupadd --gid $USER_GID $USER_NAME \
    && useradd --gid $USER_GID --uid $USER_UID --create-home $USER_NAME

USER user

COPY . /home/user

ENV PATH="${PATH}:/home/user/.local/bin"
RUN cd /home/user \
    && python -m pip install --upgrade pip \
    && pip install -r tools/requirements.txt


VOLUME ["/home/user/data"]
ENTRYPOINT ["python3"]
CMD ["/home/user/tools/download_and_convert.py"]
