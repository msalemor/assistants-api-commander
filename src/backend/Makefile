default:
	@echo "Please specify a target to build"

clean:
	rm -rf wwwroot
	mkdir wwwroot
	touch wwwroot/.gitkeep

build-ui: clean
	cd ../frontend && bun run build && cp -r dist/* ../backend/wwwroot
