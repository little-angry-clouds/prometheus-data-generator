FROM alpine:3.7 as builder
RUN mkdir -p /var/cache/apk && ln -s /var/cache/apk /etc/apk/cache && apk add \
    --update python3 python3-dev gcc musl-dev
COPY requirements.txt /root/
RUN ln -s /usr/bin/pip3 /usr/bin/pip
RUN pip install wheel && pip wheel --wheel-dir=/root/wheel -r \
    /root/requirements.txt

FROM alpine:3.7 as production
COPY --from=builder /root/wheel /root/wheel
COPY --from=builder /root/.cache /root/.cache
COPY --from=builder /etc/apk/cache /etc/apk/cache
COPY requirements.txt /root/
COPY prometheus_data_generator /opt/prometheus_data_generator
COPY config.yml /
RUN apk add python3 python3-dev && ln -s /usr/bin/pip3 /usr/bin/pip && pip \
    install --no-index --find-links=/root/wheel -r /root/requirements.txt && \
    rm -rf /root/.cache /root/requirements.txt /etc/apk/cache/* /root/wheel/
ENTRYPOINT ["python3", "/opt/prometheus_data_generator/main.py"]

FROM alpine:3.7 as debug
COPY --from=builder /root/wheel /root/wheel
COPY --from=builder /root/.cache /root/.cache
COPY --from=builder /etc/apk/cache /etc/apk/cache
COPY --from=production /opt/prometheus_data_generator/ /opt/prometheus_data_generator/
COPY requirements.txt /root/
COPY config.yml /
RUN apk add --update python3 python3-dev gcc musl-dev && ln -s /usr/bin/pip3 \
    /usr/bin/pip && pip install wheel && pip wheel --wheel-dir=/root/wheel \
    pdbpp -r /root/requirements.txt && pip install --no-index \
    --find-links=/root/wheel pdbpp -r /root/requirements.txt
ENTRYPOINT ["python3", "/opt/prometheus_data_generator/main.py"]
