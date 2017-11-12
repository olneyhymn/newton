
dependencies:
	STATIC_DEPS=true pip install -Ur requirements.pip -t .

prepare: dependencies
	rm -f lambda_bundle.zip
	zip -r lambda_bundle *

clean:
	git clean -xfd -e *.zip
