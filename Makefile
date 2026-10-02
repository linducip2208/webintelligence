PY=source/python
GO=source/go/collector
OUT=build/linux/collector
.PHONY: test build all
test:
	python -m pytest source/python/tests tests/unit -q
	cd $(GO) && go test ./...
build:
	cd $(GO) && go build -o ../../../$(OUT) ./cmd/collector
all: test build
