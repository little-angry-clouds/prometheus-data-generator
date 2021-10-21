# prometheus-data-generator

Creates arbitrary prometheus metrics.

## Why use this?

When creating Grafana dashboards or Prometheus alerts, it is common to make
mistakes. You define a threshold that they have to meet, but when modified the
next time you may forget those thresholds.

Using this tool, you can create data with the format you want and
thus being able to base alerts and graphics on data that resemble reality.

To use this, you'll create a configuration file in which you will define a
metric name, description, type and labels and sequences of certain operations.

For example, you'll be able to create a alarm called `http_requests` with the
labels `{path=/login/, return_code=200}` which will be updated as you wish.

## Configuration

There's an example configuration file called `config.yml` in the root of the
repository. It has the next format:

``` yaml
config:
  - name: number_of_fruits
    description: The number of fruits we have.
    type: gauge
    labels: [name, color]
    sequence:
      - time: 5
        eval_time: 5
        values: 0-20
        operation: inc
        labels:
          name: apple
          color: red
      - time: 5
        eval_time: 5
        values: 0-20
        operation: inc
        labels:
          name: apple
          color: green
      - time: 5
        eval_time: 5
        values: 0-5
        operation: dec
        labels:
          name: apple
          color: green
      - time: 5
        eval_time: 5
        value: 3
        operation: inc
        labels:
          name: apple
          color: yellow
```

The generated metric will be like this:

``` text
number_of_fruits{color="red",name="apple"} 14.0
number_of_fruits{color="green",name="apple"} 10.0
number_of_fruits{color="yellow",name="apple"} 4.0
```

### Supported keywords

- `name`: The [metric
  name](https://prometheus.io/docs/instrumenting/writing_clientlibs/#metric-names).
  [**Type**: string] [**Required**]
- `description`: The description to be shown as
  [HELP](https://prometheus.io/docs/instrumenting/writing_clientlibs/#metric-description-and-help).
  [**Type**: string] [**Required**]
- `type`: It should be one of the supported metric types, which you can see in the next section.
  [**Type**: string] [**Required**]
- `labels`: The labels that will be used with the metric. [**Type**: list of
  strings] [**Optional**]
- `sequence.eval_time`: Number of seconds that the sequence will be running.
  [**Type**: int] [**Required**]
- `sequence.interval`: The interval of seconds between each operation will be
  performed. 1 second is a sane number. [**Type**: int] [**Required**]
- `sequence.value`: The value that the operation will apply. It must be a single
  value. You must choose between `value` and `values`. [**Type**: int] [**Optional**]
- `sequence.values`: The range of values that will randomly be choosed and the
  operation will apply. It must be two values separed by a dash. You must choose
  between `value` and `values`. [**Type**: string (int-int / float-float)] [**Optional**]
- `sequence.operation`: The operation that will be applied. It only will be used
  with the gauge type, and you can choose between `inc`, `dec` or `set`. [**Optional**]
- `sequence.labels`: The labels of the sequence. They must be used if `labels`
  are declared. [**Optional**]

### Supported metric types

The ones defined [here](https://prometheus.io/docs/concepts/metric_types/).
- Counter
- Gauge
- Histogram
- Summary

## Manual use

```bash
git clone https://github.com/little-angry-clouds/prometheus-data-generator.git
virtualenv -p python3 venv
pip install -r requirements.txt
python prometheus_data_generator/main.py
curl localhost:9000/metrics/
```

## Use in docker

``` bash
wget https://raw.githubusercontent.com/little-angry-clouds/prometheus-data-generator/master/config.yml
docker run -ti -v `pwd`/config.yml:/config.yml -p 127.0.0.1:9000:9000 \
    littleangryclouds/prometheus-data-generator
curl localhost:9000/metrics/
```

## Use in kubernetes

There's some example manifests in the `kubernetes` directory. There's defined a
service, configmap, deployment (with
[configmap-reload](https://github.com/jimmidyson/configmap-reload) configured)
and a Service Monitor to be used with the [prometheus
operator](https://github.com/coreos/prometheus-operator).

You may deploy the manifests:

``` bash
kubectl create namespace prom-data-gen
kubectl -n prom-data-gen apply -f kubernetes/
kubectl -n prom-data-gen port-forward service/prometheus-data-generator 9000:9000
curl localhost:9000/metrics/
```

You can edit the configmap as you wish and the configmap-reload will
eventually reload the configuration without killing the pod.

## Generate prometheus alerts unit tests

TODO

## Tests

TODO
