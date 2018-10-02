
# Intro

This Workshop assumes [minikube](https://github.com/kubernetes/minikube/blob/v0.28.2/README.md) is installed (along with kubectl + kubernetes) and has only been tested in a Mac environment.

In addition, you will need a Datadog Account and have access to an API key -- Start a Free Trial [Here](https://www.datadoghq.com/lpg6/)!

This repo showcases a minikube-based path to deploying a simple flask app container that returns some sample text contained in a separate postgres container. 

The goal of this repo is to demonstrate the steps involved in installing a [Datadog](datadoghq.com/) agent to demonstrate the product's [Infrastructure Monitoring](https://www.datadoghq.com/server-monitoring/), [Application Performance Monitoring](https://www.datadoghq.com/blog/announcing-apm/), [Live Process/Container Monitoring](https://www.datadoghq.com/blog/live-process-monitoring/), and [Log Monitoring Capabilities](https://www.datadoghq.com/blog/announcing-logs/) in a Kubernetes x Docker based environment.

This repo makes no accommodations for proxy scenarios and does not fullyaccommodate situations where machines are unable to pull from the internet to download packages

# Steps to Success

The gist of the setup portion is:
1. Spin up Minikube Instance
2. Load Dockerfiles into images
3. Deploy!

## Set up 
Start Minikube instance 
```
minikube start
```
In Mac's case, there may be a need to use localkube as a bootstrapper

```
minikube start --bootstrapper=localkube
```

You will need to use minikube's docker engine by running:
```
eval $(minikube docker-env)
```

Store the API key in a kubernetes secret so its not directly in the deployment code
```
kubectl create secret generic datadog-api --from-literal=token=___INSERT_API_KEY_HERE
```
The key is then referenced in the Daemon file [here](https://github.com/ziquanmiao/minikube_datadog/blob/8b48b62278dc52f4f8d2834bc6df3ae8f955acaf/agent_daemon.yaml#L28-L32)

## build images

Then, build the images based off the provided Dockerfiles
```
docker build -t sample_flask:007 ./flask_app/
docker build -t sample_postgres:007 ./postgres/
```

## deploy things

Deploy the postgres container
```
kubectl create -f postgres_deployment.yaml
```

Deploy the application container and turn it into a service
Also create a configMap for the logs product
```
kubectl create -f app_deployment.yaml
```



Deploy the Datadog agent container

```
kubectl create -f agent_daemon.yaml
```

Deploy a nonfunction pause container to demonstrate Datadog [AutoDiscovery](https://docs.datadoghq.com/agent/autodiscovery/) via a simple HTTP check against www.google.com
```
kubectl create -f pause.yaml
```

Deploy kubernetes state files to demonstrate [kubernetes_state check](https://docs.datadoghq.com/integrations/kubernetes/#setup-kubernetes-state)

```
kubectl create -f kubernetes
```

And we are done!

# Use the Flask App

The Flask App offers 3 endpoints that returns some text `FLASK_SERVICE_IP:5000/`, `FLASK_SERVICE_IP:5000/query`, `FLASK_SERVICE_IP:5000/bad`

Run ```kubectl get services``` to find the [FLASK_SERVICE_IP](https://cl.ly/a344b20d5481) address of the flask application service

You can then access the endpoints within the minikube vm:
```
minikube ssh
```

then hit one of the following:
```
curl FLASK_SERVICE_IP:5000/
curl FLASK_SERVICE_IP:5000/query
curl FLASK_SERVICE_IP:5000/bad
```
to see the Flask application at work

# Some points of interest

The Datadog agent container should now be deployed and is acting as a collector and middleman between the services and Datadog's backend. Through actions -- curling the endpoints -- and doing nothing, metrics will be generated and directed to the corresponding Datadog Account based off your supplied API key

Below is a quick discussion on some points of interest

## Infrastructure Product
This part pertains to the ingestion of timeseries data, status checks, and events. 

By deploying the agent referencing the [Datadog Container Image](https://github.com/ziquanmiao/minikube_datadog/blob/ba94f6072fbfccbaaf8595020690df9b2f6ebdfb/agent_daemon.yaml#L13) in the agent_daemon.yaml file, the check automatically comes prepackaged with system level (CPU, Mem, IO, Disk), [Kubernetes](https://docs.datadoghq.com/agent/kubernetes/), and [Docker](https://docs.datadoghq.com/integrations/docker_daemon/) level checks.

The gist of the setup portion is:
1. Deploy the agent daemon the proper environment variables, volume and volumeMount arguments
2. Deploy relevant applications with annotations
3. Validate metrics go to agent and ends up in our application

### System Metric Requirements

[volumeMount](https://github.com/ziquanmiao/minikube_datadog/blob/ba94f6072fbfccbaaf8595020690df9b2f6ebdfb/agent_daemon.yaml#L65-L67) and [volume](https://github.com/ziquanmiao/minikube_datadog/blob/ba94f6072fbfccbaaf8595020690df9b2f6ebdfb/agent_daemon.yaml#L93-L95) for the proc directory is required from the host level

In the Datadog web application you can reference the [host map](datadoghq.com/infrastructure/map), and filter on the particular hostname to see what is going on.

### Kubernetes/Docker
docker.sock and cgroup [volumeMounts](https://github.com/ziquanmiao/minikube_datadog/blob/ba94f6072fbfccbaaf8595020690df9b2f6ebdfb/agent_daemon.yaml#L63-L70) and [volumes](https://github.com/ziquanmiao/minikube_datadog/blob/ba94f6072fbfccbaaf8595020690df9b2f6ebdfb/agent_daemon.yaml#L90-L98) are required to be attached in the daemonset

### Autodiscovery
Application/Service Pods and Containers go up and down. The Datadog agent traditionally requires a modification of the hardcoded host/port values of corresponding configuration files (example with [postgres](https://github.com/DataDog/integrations-core/blob/fd4414ed3d85a6ad835f6440f4bd091a4cf1a0f2/postgres/datadog_checks/postgres/data/conf.yaml.example#L4-L5)) and an agent restart to collect Data for installed software.

Rather than having a Mechanical Turk sit on standy ready to make the changes, the containerized accommodates makes this process automagic using [Autodiscovery](https://docs.datadoghq.com/agent/autodiscovery/) where the agent has the capability to monitor the annotations of deployments and automatically establish checks as pods come and go.

To set up autodiscovery, you will need to set up [volumes](https://github.com/ziquanmiao/minikube_datadog/blob/67c0d53f3d9fa2c55dc47986c1ab82625445a70e/agent_daemon.yaml#L109-L111) and [mountPaths](https://github.com/ziquanmiao/minikube_datadog/blob/67c0d53f3d9fa2c55dc47986c1ab82625445a70e/agent_daemon.yaml#L81-L82) to put the ethemeral configuration files

#### Postgres Example
Autodiscovery of the postgres pod in this container is straightforward, [simply annotation](https://github.com/ziquanmiao/minikube_datadog/blob/ba94f6072fbfccbaaf8595020690df9b2f6ebdfb/postgres_deployment.yaml#L14-L17) in the configuration file by adding in the typical check sections required.

Note the annotation arguments [here](https://cl.ly/d77e73e9786d) must be identical for the agent to properly connect to the container.

### Prometheus
Many services (like kubernetes itself) utilizes Prometheus as an enhancement to reveal custom internal metrics specific to the service. 

You can see what the structure of the prometheus metrics look like by running:

```
minikube ssh
curl localhost:10255/metrics
```

Datadog has the innate capability to read the log structure of prometheus produced metrics and turn it into custom metrics.
The scope of this repo doesn't really touch on it too much, but collecting prometheus metrics can simply be done via annotations done at the deployment level as seen [here](https://github.com/ziquanmiao/minikube_datadog/blob/67c0d53f3d9fa2c55dc47986c1ab82625445a70e/app_deployment.yaml#L15-L17) -- note this example fails on purpose so you can see what an error looks like in agent status

Read more about it via our [documentation](https://docs.datadoghq.com/agent/prometheus/)

## Live Processes/Containers
[Live Process/Container Monitoring](https://www.datadoghq.com/blog/live-process-monitoring/) is the capability to get container and process level granularity for all monitored systems.
This feature provides not only standard system level metrics at the process/container level, but also on the initial run commands used to set up the process/container.

Simply add [DD_PROCESS_AGENT_ENABLED](https://github.com/ziquanmiao/minikube_datadog/blob/ba94f6072fbfccbaaf8595020690df9b2f6ebdfb/agent_daemon.yaml#L38-L39) env variable in the daemonset to turn on this feature

### Requirements
Sometimes passwords are revealed in the initial run commands, the agent comes equipped with [passwd](https://github.com/ziquanmiao/minikube_datadog/blob/ba94f6072fbfccbaaf8595020690df9b2f6ebdfb/agent_daemon.yaml#L72-L74) to remove a [standard set of arguments](https://docs.datadoghq.com/graphing/infrastructure/process/#process-arguments-scrubbing)

We again need [docker.sock](https://docs.datadoghq.com/graphing/infrastructure/process/#kubernetes-daemonset) to get container information.

### Validation

run ``` kubectl get pods``` to get the pod name of the agent container.

run ```kubectl exec -it POD_NAME bash ``` to hop into the container

run ```agent status``` to see the status summary and look for the integrations section to see agent is collecting metrics

run ``` cat /var/log/datadog/agent.log``` to see logs pertaining to the agent

## APM Tracing
The same agent that handles infrastructure metrics can also accommodate receiving [Trace Data](https://www.datadoghq.com/blog/tag/apm/) from a designated [APM module](datadoghq.com/apm/docs) -- these modules sit on top of your applications and forward [payloads](https://docs.datadoghq.com/api/?lang=bash#send-traces) to a local Datadog agent to middle man to our backend.

Applications are spinning up in pods and we need payloads being fired to the sidecar agent pod. In this example, we set up a route between the pods with a port going through the host level.

### Requirements

#### From the agent daemon side
Enable agent to receive traces from the Agent deployment side via [environment variables](https://github.com/ziquanmiao/minikube_datadog/blob/ba94f6072fbfccbaaf8595020690df9b2f6ebdfb/agent_daemon.yaml#L26-L27)

Create a [port connection to host](https://github.com/ziquanmiao/minikube_datadog/blob/ba94f6072fbfccbaaf8595020690df9b2f6ebdfb/agent_daemon.yaml#L21-L24) via the 8126 port

#### From the application Side
Provide the deploy file with a [link to the host level](https://github.com/ziquanmiao/minikube_datadog/blob/ba94f6072fbfccbaaf8595020690df9b2f6ebdfb/app_deployment.yaml#L27-L32) for port 8126 via environmental variables, so that applications can reference the host/port values to fire traces to

##### Flask specific
Have the [ddtrace module](https://github.com/ziquanmiao/minikube_datadog/blob/ba94f6072fbfccbaaf8595020690df9b2f6ebdfb/flask_app/requirements.txt#L2)

In the app.py code, [import ddtrace module](https://github.com/ziquanmiao/minikube_datadog/blob/ba94f6072fbfccbaaf8595020690df9b2f6ebdfb/flask_app/app.py#L18-L25) and patch both [sqlalchemy](https://github.com/ziquanmiao/minikube_datadog/blob/ba94f6072fbfccbaaf8595020690df9b2f6ebdfb/flask_app/app.py#L27) and the [Flask app object](https://github.com/ziquanmiao/minikube_datadog/blob/ba94f6072fbfccbaaf8595020690df9b2f6ebdfb/flask_app/app.py#L37).

**Note**: the trace module is an implementation as all modules are. If certain spans are not being captured, you can always [hardcode](https://github.com/ziquanmiao/minikube_datadog/blob/ba94f6072fbfccbaaf8595020690df9b2f6ebdfb/flask_app/app.py#L102) them in.

### Validation

#### Agent Side
run ``` kubectl get pods``` to get the pod name of the agent container.

run ```kubectl exec -it POD_NAME bash ``` to hop into the container

run ```agent status``` to see the status summary and look for the tracing section to see agent has tracing turned on

run ``` cat /var/log/datadog/trace-agent.log``` to see logs pertaining to the trace agent

#### Datadog Side

head over to [Trace Services Page](datadoghq.com/apm/services) and look for your service level metrics and traces!

## Logs

The same agent polling for metrics periodically for infrastructure metrics, live process metrics, and middle manning trace transcations can also be set up to tail log instances.

Simply turn on [DD_LOGS_ENABLED](https://github.com/ziquanmiao/minikube_datadog/blob/67c0d53f3d9fa2c55dc47986c1ab82625445a70e/agent_daemon.yaml#L44-L45) via the environmental variable in the agent daemon file.

### Tailing Flask logs via Config Maps

Tailing logs from flask is pretty easy using kubernetes config maps.

#### Agent Side
Simply set up the [mountPath directory](https://github.com/ziquanmiao/minikube_datadog/blob/67c0d53f3d9fa2c55dc47986c1ab82625445a70e/agent_daemon.yaml#L79-L80) connected via the host and the [volume](https://github.com/ziquanmiao/minikube_datadog/blob/67c0d53f3d9fa2c55dc47986c1ab82625445a70e/agent_daemon.yaml#L106-L108) in the agent daemon

#### Flask side
Set up the corresponding mounts for [volume and mountPath](https://github.com/ziquanmiao/minikube_datadog/blob/67c0d53f3d9fa2c55dc47986c1ab82625445a70e/app_deployment.yaml#L37-L43) so we can connect the flask pod to the relevant agent pod via the host

In the app, set up the app level [logging configurations](https://github.com/ziquanmiao/minikube_datadog/blob/67c0d53f3d9fa2c55dc47986c1ab82625445a70e/flask_app/app.py#L55-L64) so logs are properly pushed to the right log file when routines are run ([example](https://github.com/ziquanmiao/minikube_datadog/blob/67c0d53f3d9fa2c55dc47986c1ab82625445a70e/flask_app/app.py#L73-L79))

### Validation

#### Agent Side
run ``` kubectl get pods``` to get the pod name of the agent container.

run ```kubectl exec -it POD_NAME bash ``` to hop into the container

run ```agent status``` to see the status summary and look for the logging section to see agent has logs turned on

run ``` cat /var/log/datadog/agent.log``` to see relevant log instances pertaining to the log agent

#### Datadog Side

Navigate to the [logs explorer page](datadoghq.com/logs) and look for flask logs!




