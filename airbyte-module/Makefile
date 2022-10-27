include Makefile.env

DOCKER_HOSTNAME ?= ghcr.io
DOCKER_NAMESPACE ?= elsalant
DOCKER_TAG ?= 0.0.1
DOCKER_NAME ?= airbyte-module
DOCKER_CLIENT_NAME ?= airbyte-module-client
KIND_CLUSTER ?= sm-read

IMG := ${DOCKER_HOSTNAME}/${DOCKER_NAMESPACE}/${DOCKER_NAME}:${DOCKER_TAG}
CLIENT_IMG := ${DOCKER_HOSTNAME}/${DOCKER_NAMESPACE}/${DOCKER_CLIENT_NAME}:${DOCKER_TAG}

export HELM_EXPERIMENTAL_OCI=1

all: test build

.PHONY: test
test:
	pipenv run python -m unittest discover

.PHONY: build
build:
	pipenv lock -r | sed -n '/^#/,$$p' > requirements.txt
	docker build -f build/Dockerfile . -t ${IMG}
	rm requirements.txt

	cd helm/client; docker build --tag ${CLIENT_IMG} .

.PHONY: docker-push
docker-push:
	docker push ${IMG}
	docker push ${CLIENT_IMG}

.PHONY: push-to-kind
push-to-kind:
	kind load docker-image ${IMG} --name $(KIND_CLUSTER)

.PHONY: helm-package
helm-package:
	helm package helm/abm -d /tmp
	helm push /tmp/airbyte-module-chart-0.0.0-els.tgz oci://ghcr.io/elsalant

include hack/make-rules/helm.mk
include hack/make-rules/tools.mk
