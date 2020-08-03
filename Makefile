deploy:
	pip3 freeze >code/requirements.txt
	docker build -t registry.appuio.ch/silvan-privat/schaltuhr .
	docker push registry.appuio.ch/silvan-privat/schaltuhr:latest
