default:
	@echo "Please specify a target to build"

TAG=0.0.5
build:
	cd src/frontend && bun run build
	rm -rf src/backend/wwwroot
	mkdir src/backend/wwwroot
	cp -r src/frontend/dist/* src/backend/wwwroot/.
	cd src/backend && docker build . -t am8850/aiassistant01:$(TAG)

docker-run:
	cd src/backend && docker build run --rm -p 8080:80 --env-file=.env am8850/aiassistant01:$(TAG)

deploy: build
	docker push am8850/aiassistant01:$(TAG)