DOCKER_CLI = sudo docker

DOCKER_TAG = $(CI_PIPELINE_ID)
ifeq ($(DOCKER_TAG),)
	DOCKER_TAG = local
endif

APP_NAME = campfire

# returns the ID of the Docker container
define DOCKER_CONTAINER_ID
	$(DOCKER_CLI) ps -aq --filter "name=$(1)"
endef

# returns the IP address assigned to a Docker container instance $(1)
define DOCKER_CONTAINER_IP
	$(DOCKER_CLI) inspect --format '{{ .NetworkSettings.IPAddress }}' $(1) 
endef

NET_NAME := $(APP_NAME)_net
# SERVER_NET=1.1.0.0/16
SERVER_IP=0.0.0.0
# SERVER_IP=1.1.0.22
SERVER_PORT=5002

ENTRYPOINT_SERVER = python
ENTRYPOINT_SERVER_ARGS = -u /app/app.py -a $(SERVER_IP) -p $(SERVER_PORT)

TEMPLATE_DIRS := $(wildcard src/vmsetup/*)

.PHONY: $(APP_NAME) $(TEMPLATE_DIRS) prereq run publish

key.pem:
	openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -subj "/C=US/ST=Washington/L=Seattle/O=F5 Networks/OU=Dataplane Group/CN=Rachel" 

$(TEMPLATE_DIRS):
	$(MAKE) -C $@ clean
	$(MAKE) -C $@ all

$(APP_NAME): key.pem $(TEMPLATE_DIRS) 
	$(DOCKER_CLI) build -t $(APP_NAME):$(DOCKER_TAG) .

prereq:
	# remove any stale pre-existing running container.
	# if $(APP_NAME) bad status, containers do not remove.
	$(eval PID = `$(call DOCKER_CONTAINER_ID,$(APP_NAME))`)
	if [ ! -z $(PID) ]; then \
		$(DOCKER_CLI) rm -f $(PID); \
	else \
		echo "running $(APP_NAME)"; \
	fi
# 	if [ -z `$(DOCKER_CLI) network ls | grep $(NET_NAME)` ]; then \
# 		$(DOCKER_CLI) network create --subnet $(SERVER_NET) $(NET_NAME); \
# 	else \
# 		echo "network already setup"; \
# 	fi

run: $(APP_NAME) prereq
	$(DOCKER_CLI) run -p $(SERVER_PORT):$(SERVER_PORT) \
		-d --name $(APP_NAME) \
		-it --entrypoint $(ENTRYPOINT_SERVER) $(APP_NAME):$(DOCKER_TAG) $(ENTRYPOINT_SERVER_ARGS)
	./proxyserver.sh $(SERVER_IP) $(SERVER_PORT); $(DOCKER_CLI) stop $(APP_NAME)

test:
	cd ./src/irulelogapi; python3.6 -m apitests.run_all_tests
