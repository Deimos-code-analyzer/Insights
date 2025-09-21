from flask import Flask, jsonify, request
from kubernetes import client, config
from flask_cors import CORS
from insight import Insight

app = Flask(__name__)
CORS(app)

# Load in-cluster config
config.load_incluster_config()
v1 = client.CoreV1Api()
apps_v1 = client.AppsV1Api()

# Initialize insight
insight = Insight()

@app.route("/pods", methods=["GET"])
def list_pods():
    namespace = request.args.get("namespace", "code-analyzer")
    pods = v1.list_namespaced_pod(namespace=namespace)
    pod_names = [pod.metadata.name for pod in pods.items]
    return jsonify({"pods": pod_names})

@app.route("/nodes", methods=["GET"])
def list_nodes():
    nodes = v1.list_node()
    node_names = [node.metadata.name for node in nodes.items]
    return jsonify({"nodes": node_names})

@app.route("/deployments", methods=["GET"])
def list_deployments():
    namespace = request.args.get("namespace", "code-analyzer")
    deployments = apps_v1.list_namespaced_deployment(namespace=namespace)
    deployment_names = [d.metadata.name for d in deployments.items]
    return jsonify({"deployments": deployment_names})

@app.route("/cluster-context", methods=["GET"])
def get_cluster_context():
    namespace = request.args.get("namespace", "code-analyzer")
    context = insight.get_cluster_context(namespace)
    return jsonify(context)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
