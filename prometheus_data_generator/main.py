#!/usr/bin/env python3

import time
import random
import threading
import logging
from os import _exit, environ
import yaml
from flask import Flask, Response
from prometheus_client import Gauge, Counter, Summary, Histogram
from prometheus_client import generate_latest, CollectorRegistry


if "PDG_LOG_LEVEL" in environ:
    supported_log_levels = ["INFO", "ERROR", "DEBUG"]
    if environ["PDG_LOG_LEVEL"].upper() not in supported_log_levels:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s.%(msecs)03d %(levelname)s - %(funcName)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        logger = logging.getLogger("prometheus-data-generator")
    logging.basicConfig(
        format="%(asctime)s.%(msecs)03d %(levelname)s - %(funcName)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logger = logging.getLogger("prometheus-data-generator")
    logger.setLevel(environ["PDG_LOG_LEVEL"].upper())
else:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s.%(msecs)03d %(levelname)s - %(funcName)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logger = logging.getLogger("prometheus-data-generator")


def read_configuration():
    """
    Read configuration from the environmental variable PDG_PATH.
    """
    # TODO validate the yaml
    if "PDG_CONFIG" in environ:
        path = environ["PDG_CONFIG"]
    else:
        path = "config.yml"
    config = yaml.safe_load(open(path))
    return config


class PrometheusDataGenerator:
    def __init__(self):
        """
        Initialize the flask endpoint and launch the function that will throw
        the threads that will update the metrics.
        """
        self.app = Flask(__name__)
        self.serve_metrics()
        self.init_metrics()

    def init_metrics(self):
        """
        Launch the threads that will update the metrics.
        """
        self.threads = []
        self.registry = CollectorRegistry()
        self.data = read_configuration()
        for metric in self.data["config"]:
            if "labels" in metric:
                labels = metric["labels"]
            else:
                labels = []
            if metric["type"].lower() == "counter":
                instrument = Counter(
                    metric["name"],
                    metric["description"],
                    labels,
                    registry=self.registry
                )
            elif metric["type"].lower() == "gauge":
                instrument = Gauge(
                    metric["name"],
                    metric["description"],
                    labels,
                    registry=self.registry
                )
            elif metric["type"].lower() == "summary":
                instrument = Summary(
                    metric["name"],
                    metric["description"],
                    labels,
                    registry=self.registry
                )
            elif metric["type"].lower() == "histogram":
                # TODO add support to overwrite buckets
                instrument = Histogram(
                    metric["name"],
                    metric["description"],
                    labels,
                    registry=self.registry
                )
            t = threading.Thread(
                target=self.update_metrics,
                args=(instrument, metric)
            )
            t.start()
            self.threads.append(t)

    def update_metrics(self, metric_object, metric_metadata):
        """
        Updates the metrics.

        Arguments:
        metric_object: a Prometheus initialized object. It can be a Gauge,
          Counter, Histogram or Summary.
        metric_metadata: the configuration related to the initialzed Prometheus
          object. It comes from the config.yml.
        """
        self.stopped = False
        while True:
            if self.stopped:
                break
            for sequence in metric_metadata["sequence"]:
                if self.stopped:
                    break
                if "labels" in sequence:
                    labels = [key for key in sequence["labels"].values()]
                else:
                    labels = []
                timeout = time.time() + sequence["eval_time"]
                logger.debug(
                    "Changing sequence in {} metric".format(metric_metadata["name"])
                )
                interval = sequence["interval"]
                while True:
                    if self.stopped:
                        break
                    if time.time() > timeout:
                        break
                    if "value" in sequence:
                        value = sequence["value"]
                        if "." in value:
                            value = float(value)
                        else:
                            value = int(value)
                    elif "values" in sequence:
                        if "." in sequence["values"].split("-")[0]:
                            initial_value = float(sequence["values"].split("-")[0])
                            end_value = float(sequence["values"].split("-")[1])
                            value = random.uniform(initial_value, end_value)
                        else:
                            initial_value = int(sequence["values"].split("-")[0])
                            end_value = int(sequence["values"].split("-")[1])
                            value = random.randrange(initial_value, end_value)
                    if metric_metadata["type"].lower() == "gauge":
                        try:
                            operation = sequence["operation"].lower()
                        except:
                            logger.error(
                                "You must set an operation when using Gauge"
                            )
                            _exit(1)
                        if operation == "inc":
                            if labels == []:
                                metric_object.inc(value)
                            else:
                                metric_object.labels(*labels).inc(value)
                        elif operation == "dec":
                            if labels == []:
                                metric_object.dec(value)
                            else:
                                metric_object.labels(*labels).dec(value)
                        elif operation == "set":
                            if labels == []:
                                metric_object.set(value)
                            else:
                                metric_object.labels(*labels).set(value)
                    elif metric_metadata["type"].lower() == "counter":
                        if labels == []:
                            metric_object.inc(value)
                        else:
                            metric_object.labels(*labels).inc(value)
                    elif metric_metadata["type"].lower() == "summary":
                        if labels == []:
                            metric_object.observe(value)
                        else:
                            metric_object.labels(*labels).observe(value)
                    elif metric_metadata["type"].lower() == "histogram":
                        if labels == []:
                            metric_object.observe(value)
                        else:
                            metric_object.labels(*labels).observe(value)
                    time.sleep(interval)

    def serve_metrics(self):
        """
        Main method to serve the metrics. It's used mainly to get the self
        parameter and pass it to the next function.
        """
        @self.app.route("/")
        def root():
            """
            Exposes a blank html page with a link to the metrics.
            """
            page = "<a href=\"/metrics/\">Metrics</a>"
            return page

        @self.app.route("/metrics/")
        def metrics():
            """
            Plain method to expose the prometheus metrics. Every time it's
            called it will recollect the metrics and generate the rendering.
            """
            metrics = generate_latest(self.registry)
            return Response(metrics,
                            mimetype="text/plain",
                            content_type="text/plain; charset=utf-8")

        @self.app.route("/-/reload")
        def reload():
            """
            Stops the threads and restarts them.
            """
            self.stopped = True
            for thread in self.threads:
                thread.join()
            self.init_metrics()
            logger.info("Configuration reloaded. Metrics will be restarted.")
            return Response("OK")

    def run_webserver(self):
        """
        Launch the flask webserver on a thread.
        """
        threading.Thread(
            target=self.app.run,
            kwargs={"port": "9000", "host": "0.0.0.0"}
        ).start()


if __name__ == "__main__":
    PROM = PrometheusDataGenerator()
    PROM.run_webserver()
