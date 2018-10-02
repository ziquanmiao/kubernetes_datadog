docker build -t sample_flask:latest .
docker run -d -p 5000:5000 sample_flask


HYGIENE:

#see logs
docker log CONTAINER_NAME_OR_ID
#kill container
docker kill CONTAINER_NAME_OR_ID