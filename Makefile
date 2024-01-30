default:
	@echo "Please specify a target to build"

TAG=0.0.10
DOCKER_PATH=am8850
DOCKER_NAME=aiassistant01
build:
	cd src/frontend && bun run build
	rm -rf src/backend/wwwroot
	mkdir src/backend/wwwroot
	cp -r src/frontend/dist/* src/backend/wwwroot/.
	
docker-build: build
	cd src/backend && docker build . -t am8850/aiassistant01:$(TAG)

docker-run: build
	cd src/backend && docker run --rm -p 8080:80 --env-file=.env am8850/aiassistant01:$(TAG)

docker-deploy: build
	docker push $(DOCKER_PATH)/$(DOCKER_NAME):$(TAG)