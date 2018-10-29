FROM java:8
WORKDIR /
ADD SpringBoot.jar /app/SpringBoot.jar
ADD dd-java-agent.jar /app/dd-java-agent.jar

CMD java -javaagent:/app/dd-java-agent.jar \
    -jar /app/SpringBoot.jar