from flask import Flask, jsonify, request
from kubernetes import client, config
from kubernetes.client.exceptions import ApiException
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Load in-cluster config
config.load_incluster_config()
api_client = client.ApiClient()

@app.route("/full-context", methods=["GET"])
def full_context():
    namespace = request.args.get("namespace", "code-analyzer")
    result = {}

    # Discover all API resources
    api_discovery = client.ApisApi(api_client)
    core_v1 = client.CoreV1Api(api_client)

    # Core resources
    core_resources = ["pods", "services", "configmaps", "secrets", "persistentvolumeclaims"]
    for res in core_resources:
        try:
            func = getattr(core_v1, f"list_namespaced_{res}")
            items = func(namespace=namespace).items
            result[res] = [i.metadata.name for i in items]
        except ApiException as e:
            result[f"{res}_error"] = f"{e.status} {e.reason}"
        except AttributeError:
            pass  # resource not supported in this API

    # Cluster resources (nodes, persistentvolumes)
    cluster_resources = ["nodes", "persistentvolumes"]
    for res in cluster_resources:
        try:
            func = getattr(core_v1, f"list_{res}")
            items = func().items
            result[res] = [i.metadata.name for i in items]
        except ApiException as e:
            result[f"{res}_error"] = f"{e.status} {e.reason}"
        except AttributeError:
            pass

    # Apps API (deployments, statefulsets, daemonsets)
    apps_v1 = client.AppsV1Api(api_client)
    app_resources = ["deployments", "statefulsets", "daemonsets"]
    for res in app_resources:
        try:
            func = getattr(apps_v1, f"list_namespaced_{res}")
            items = func(namespace=namespace).items
            result[res] = [i.metadata.name for i in items]
        except ApiException as e:
            result[f"{res}_error"] = f"{e.status} {e.reason}"
        except AttributeError:
            pass

    return jsonify(result)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
