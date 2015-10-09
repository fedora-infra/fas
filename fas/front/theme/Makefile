BIN = ./node_modules/.bin
FONT_DIR      ?= ./../../static/theme/fedoraproject/assets/fonts
FONTELLO_HOST ?= http://fontello.com

install:
	npm install
	npm install gulp
	$(BIN)/bower install

reinstall:
	rm -Rf vendor
	rm -Rf node_modules
	make install

update:
	npm prune
	npm install || sudo chown -R $$USER ~/.npm node_modules && npm install
	$(BIN)/bower prune
	$(BIN)/bower update

watch: build
#	make build # first compile
	$(BIN)/gulp watch

build:
	$(BIN)/gulp less
	$(BIN)/gulp js

# remove existing token if any
fontgettoken:
	curl --silent --show-error --fail --output .fontello --form "config=@${FONT_DIR}/config.json" ${FONTELLO_HOST}

# open the fontello project from your mac
fontopenmac:
	make fontgettoken
	cat .fontello
	open -a "Google Chrome" ${FONTELLO_HOST}/`cat .fontello`

# open the fontello project with your linux
fontopenlinux:
	make fontgettoken
	/opt/google/chrome/google-chrome --enable-plugins ${FONTELLO_HOST}/`cat .fontello`

# save the session font in local and extract it
fontsave:
	@if test ! `which unzip` ; then \
		echo 'Install unzip first.' >&2 ; \
		exit 128 ; \
		fi

	rm -rf .fontello.src .fontello.zip

	curl --silent --show-error --fail --output .fontello.zip \
		${FONTELLO_HOST}/`cat .fontello`/get

	unzip .fontello.zip -d .fontello.src

	rm -rf ${FONT_DIR}
	mv `find ./.fontello.src -maxdepth 1 -name 'fontello-*'` ${FONT_DIR}
	rm -rf .fontello.src .fontello.zip
