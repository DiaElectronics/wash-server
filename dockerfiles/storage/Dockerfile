FROM ubuntu:22.04 as storagebuilder

# update everything
RUN apt update -y && apt upgrade -y && apt install git sudo wget -y 

# install gcc
RUN apt install build-essential -y

# install golang
#RUN apt install golang -y

# clone some code
RUN git clone https://github.com/openrbt/lea-central-wash



RUN /lea-central-wash/install/ubuntu2004/2_install_golang.sh
RUN /lea-central-wash/install/ubuntu2004/3_install_dev_tools.sh

RUN export PATH=$PATH:/usr/local/go/bin && cd /lea-central-wash && go build ./cmd/storage 

FROM ubuntu:22.04

RUN apt update -y && \
    apt upgrade -y && \
    apt install -y git && \
    apt clean && \
    rm -rf /var/lib/apt/lists/* && \
    git config --global --add safe.directory /app/stations/openwashing

COPY --from=storagebuilder /lea-central-wash/storage /storage
COPY --from=storagebuilder /lea-central-wash/cmd/storage/internal/migration /migration

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# let's build everything
CMD [ "/entrypoint.sh" ]
