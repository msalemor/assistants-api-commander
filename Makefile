default:
	@echo "Please specify a target to build"

TAG=0.0.2
DOCKER_PATH=am8850
DOCKER_NAME=asstcommander
build:
	cd src/frontend && bun run build
	rm -rf src/backend/wwwroot
	mkdir src/backend/wwwroot
	cp -r src/frontend/dist/* src/backend/wwwroot/.
	
docker-build: build
	cd src/backend && docker build . -t $(DOCKER_PATH)/$(DOCKER_NAME):$(TAG)

docker-run: docker-build
	cd src/backend && docker run --rm -p 8080:80 --env-file=.env $(DOCKER_PATH)/$(DOCKER_NAME):$(TAG)

docker-push: docker-build
	docker push $(DOCKER_PATH)/$(DOCKER_NAME):$(TAG)