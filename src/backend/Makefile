.PHONY: default
default:
	@echo "Please specify a target to build"

.PHONY: clean
clean:
	rm -rf wwwroot
	mkdir wwwroot
	touch wwwroot/.gitkeep

.PHONY: build-ui
build-ui: clean
	cd ../frontend && bun run build && cp -r dist/* ../backend/wwwroot


TAG=am8850/asstapicommander
VERSION=0.0.1
.PHONY: build-docker
docker-build: build-ui
	docker build -t $(TAG):$(VERSION) .

.PHONY: push-docker
docker-push: build-docker
	docker push $(TAG):$(VERSION)