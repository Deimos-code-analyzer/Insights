from kubernetes import client, config
from datetime import datetime

class Insight:
    def __init__(self):
        """Initialize the Kubernetes client configuration."""
        try:
            config.load_incluster_config()
        except:
            config.load_kube_config()
        
        self.v1 = client.CoreV1Api()
        self.apps_v1 = client.AppsV1Api()

    def get_cluster_context(self, namespace="code-analyzer"):
        """Get comprehensive cluster context data."""
        context = {
            "timestamp": datetime.now().isoformat(),
            "namespace": namespace,
            "nodes": [],
            "pods": [],
            "deployments": [],
            "services": [],
            "events": []
        }
        
        try:
            # Get Nodes
            nodes = self.v1.list_node()
            for node in nodes.items:
                node_info = {
                    "name": node.metadata.name,
                    "status": "Ready" if any(c.type == "Ready" and c.status == "True" 
                                           for c in node.status.conditions) else "NotReady",
                    "cpu_capacity": node.status.capacity.get("cpu"),
                    "memory_capacity": node.status.capacity.get("memory"),
                    "conditions": [{"type": c.type, "status": c.status} for c in node.status.conditions]
                }
                context["nodes"].append(node_info)
            
            # Get Pods
            pods = self.v1.list_namespaced_pod(namespace=namespace)
            for pod in pods.items:
                pod_info = {
                    "name": pod.metadata.name,
                    "status": pod.status.phase,
                    "ready": sum(1 for c in (pod.status.container_statuses or []) if c.ready),
                    "total_containers": len(pod.spec.containers),
                    "restart_count": sum(c.restart_count for c in (pod.status.container_statuses or [])),
                    "node": pod.spec.node_name
                }
                context["pods"].append(pod_info)
            
            # Get Deployments
            deployments = self.apps_v1.list_namespaced_deployment(namespace=namespace)
            for deployment in deployments.items:
                deployment_info = {
                    "name": deployment.metadata.name,
                    "replicas": deployment.spec.replicas,
                    "ready_replicas": deployment.status.ready_replicas or 0,
                    "available_replicas": deployment.status.available_replicas or 0
                }
                context["deployments"].append(deployment_info)
            
            # Get Services
            services = self.v1.list_namespaced_service(namespace=namespace)
            for service in services.items:
                service_info = {
                    "name": service.metadata.name,
                    "type": service.spec.type,
                    "cluster_ip": service.spec.cluster_ip
                }
                context["services"].append(service_info)
            
            # Get Recent Events (last 5)
            events = self.v1.list_namespaced_event(namespace=namespace)
            recent_events = sorted(events.items, 
                                 key=lambda x: x.metadata.creation_timestamp or datetime.min, 
                                 reverse=True)[:5]
            for event in recent_events:
                event_info = {
                    "type": event.type,
                    "reason": event.reason,
                    "message": event.message,
                    "object": f"{event.involved_object.kind}/{event.involved_object.name}"
                }
                context["events"].append(event_info)
            
        except Exception as e:
            context["error"] = str(e)
        
        return context