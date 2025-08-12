PROTO_DIR=app/grpc
PY_OUT=app/grpc

proto:
	python -m grpc_tools.protoc -I$(PROTO_DIR) --python_out=$(PY_OUT) --grpc_python_out=$(PY_OUT) $(PROTO_DIR)/balance.proto

run-rest:
	uvicorn app.main:app --host 0.0.0.0 --port 8000

run-grpc:
	python -m app.grpc.server
