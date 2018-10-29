FROM java:8
WORKDIR /
ADD SpringBoot.jar /app/SpringBoot.jar
ADD dd-java-agent.jar /app/dd-java-agent.jar

CMD java -javaagent:/app/dd-java-agent.jar \
	-Ddd.agent.host=$DD_AGENT_SERVICE_HOST \
    -Ddd.agent.port=$DD_AGENT_SERVICE_PORT \
    -Ddd.jmxfetch.enabled=true \
    -jar /app/SpringBoot.jar