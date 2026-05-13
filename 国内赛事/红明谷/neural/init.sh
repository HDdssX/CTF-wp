#!/bin/bash
# NeuralChat initialization script
# Engine runs as root, Flask runs as neuralchat (privilege separation)

echo "[*] Starting NeuralChat services..."

# Start the C backend engine as root (needed for flag access via VNM/system())
/opt/neuralchat/bin/engine &
ENGINE_PID=$!
echo "[*] Engine started with PID $ENGINE_PID (root)"

# Wait for socket to be ready
for i in $(seq 1 10); do
    if [ -S /opt/neuralchat/run/engine.sock ]; then
        echo "[*] Engine socket ready"
        break
    fi
    sleep 0.5
done

# Ensure socket is accessible by neuralchat user
chmod 777 /opt/neuralchat/run/engine.sock

# Start the Flask frontend as unprivileged neuralchat user
echo "[*] Starting Flask frontend as neuralchat user..."
cd /opt/neuralchat/frontend
exec su -s /bin/bash neuralchat -c "python3 /opt/neuralchat/frontend/app.py"
