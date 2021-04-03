SRC_DIR="/mnt/c/Code/tinyMQ/tinyMQ"
DST_DIR="/mnt/c/Code/tinyMQ/tinyMQ"


protoc -I=$SRC_DIR --python_out=$DST_DIR $SRC_DIR/message.proto

