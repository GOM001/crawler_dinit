build_service:
	@echo "Intall python 3"
	sudo apt install python3
	@echo "Put geckodriver in path"
	sudo cp resorces/geckodriver /usr/local/bin/geckodriver
	@echo "Install Firefox"
	sudo apt-get update -y
	sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys A6DCF7707EBC211F
	sudo apt-add-repository "deb http://ppa.launchpad.net/ubuntu-mozilla-security/ppa/ubuntu focal main"
	sudo apt-get install -y firefox
	@echo "Install Pip"
	sudo apt install -y python3-pip
	@echo "Install Requirements"
	sudo pip3 install -U -r requirements.txt
	@echo "Buld Env"
	export FLASK_APP=restApi
	export FLASK_ENV=development
	@echo "Rodando flask"
	python3 app.py