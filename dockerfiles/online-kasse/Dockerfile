FROM ubuntu:22.04 as builder

# update everything
RUN apt update -y && apt upgrade -y && apt install git sudo wget gcc libc-dev -y 
# clone some code
RUN git clone https://github.com/DiaElectronics/online_kasse


RUN wget https://golang.org/dl/go1.17.7.linux-amd64.tar.gz && tar -C /usr/local -xzf go1.17.7.linux-amd64.tar.gz

RUN chmod 777 /usr/local/go/bin/go

RUN export PATH=$PATH:/usr/local/go/bin && cd /online_kasse/cmd/web && go build

FROM ubuntu:22.04
RUN apt update -y && apt upgrade -y && apt install -y p7zip-full gcc libc-dev wget libusb-1.0-0

RUN wget -O driver.zip  "http://fs.atol.ru/_layouts/15/atol.templates/Handlers/FileHandler.ashx?guid=700b2df4-42a8-4b0f-8ca1-ab0e2390cc56&webUrl="
RUN 7z x driver.zip

RUN chmod 777 "/10.8.1.0/installer/deb/libfptr10_10.8.1.0_amd64.deb" && \
    apt-get install -y "./10.8.1.0/installer/deb/libfptr10_10.8.1.0_amd64.deb"
COPY --from=builder /online_kasse/cmd/web/web /kasse
COPY --from=builder /online_kasse/cmd/web/key.pem /
COPY --from=builder /online_kasse/cmd/web/cert.pem /

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# let's build everything
CMD [ "/entrypoint.sh" ]
