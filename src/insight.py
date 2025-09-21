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
        self.networking_v1 = client.NetworkingV1Api()

    def get_cluster_context(self, namespace="code-analyzer"):
        """Get comprehensive cluster context data."""
        context = {
            "timestamp": datetime.now().isoformat(),
            "namespace": namespace,
            "nodes": [],
            "pods": [],
            "deployments": [],
            "services": [],
            "events": [],
            "persistent_volumes": [],
            "persistent_volume_claims": [],
            "config_maps": [],
            "secrets": [],
            "ingresses": [],
            "replica_sets": [],
            "daemon_sets": [],
            "stateful_sets": [],
            "namespaces": []
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
            
            # Get Persistent Volumes (cluster-wide)
            pvs = self.v1.list_persistent_volume()
            for pv in pvs.items:
                pv_info = {
                    "name": pv.metadata.name,
                    "capacity": pv.spec.capacity.get("storage") if pv.spec.capacity else None,
                    "access_modes": pv.spec.access_modes or [],
                    "status": pv.status.phase,
                    "reclaim_policy": pv.spec.persistent_volume_reclaim_policy,
                    "storage_class": pv.spec.storage_class_name
                }
                context["persistent_volumes"].append(pv_info)
            
            # Get Persistent Volume Claims
            pvcs = self.v1.list_namespaced_persistent_volume_claim(namespace=namespace)
            for pvc in pvcs.items:
                pvc_info = {
                    "name": pvc.metadata.name,
                    "status": pvc.status.phase,
                    "capacity": pvc.status.capacity.get("storage") if pvc.status.capacity else None,
                    "access_modes": pvc.spec.access_modes or [],
                    "storage_class": pvc.spec.storage_class_name,
                    "volume_name": pvc.spec.volume_name
                }
                context["persistent_volume_claims"].append(pvc_info)
            
            # Get ConfigMaps
            config_maps = self.v1.list_namespaced_config_map(namespace=namespace)
            for cm in config_maps.items:
                cm_info = {
                    "name": cm.metadata.name,
                    "data_keys": list(cm.data.keys()) if cm.data else [],
                    "binary_data_keys": list(cm.binary_data.keys()) if cm.binary_data else []
                }
                context["config_maps"].append(cm_info)
            
            # Get Secrets
            secrets = self.v1.list_namespaced_secret(namespace=namespace)
            for secret in secrets.items:
                secret_info = {
                    "name": secret.metadata.name,
                    "type": secret.type,
                    "data_keys": list(secret.data.keys()) if secret.data else []
                }
                context["secrets"].append(secret_info)
            
            # Get Ingresses
            try:
                ingresses = self.networking_v1.list_namespaced_ingress(namespace=namespace)
                for ingress in ingresses.items:
                    ingress_info = {
                        "name": ingress.metadata.name,
                        "hosts": [rule.host for rule in (ingress.spec.rules or []) if rule.host],
                        "tls": len(ingress.spec.tls or []) > 0,
                        "class": ingress.spec.ingress_class_name
                    }
                    context["ingresses"].append(ingress_info)
            except Exception:
                pass  # Ingress might not be available in some clusters
            
            # Get ReplicaSets
            replica_sets = self.apps_v1.list_namespaced_replica_set(namespace=namespace)
            for rs in replica_sets.items:
                rs_info = {
                    "name": rs.metadata.name,
                    "replicas": rs.spec.replicas,
                    "ready_replicas": rs.status.ready_replicas or 0,
                    "available_replicas": rs.status.available_replicas or 0,
                    "owner": rs.metadata.owner_references[0].name if rs.metadata.owner_references else None
                }
                context["replica_sets"].append(rs_info)
            
            # Get DaemonSets
            daemon_sets = self.apps_v1.list_namespaced_daemon_set(namespace=namespace)
            for ds in daemon_sets.items:
                ds_info = {
                    "name": ds.metadata.name,
                    "desired": ds.status.desired_number_scheduled or 0,
                    "current": ds.status.current_number_scheduled or 0,
                    "ready": ds.status.number_ready or 0,
                    "available": ds.status.number_available or 0
                }
                context["daemon_sets"].append(ds_info)
            
            # Get StatefulSets
            stateful_sets = self.apps_v1.list_namespaced_stateful_set(namespace=namespace)
            for ss in stateful_sets.items:
                ss_info = {
                    "name": ss.metadata.name,
                    "replicas": ss.spec.replicas,
                    "ready_replicas": ss.status.ready_replicas or 0,
                    "current_replicas": ss.status.current_replicas or 0,
                    "updated_replicas": ss.status.updated_replicas or 0
                }
                context["stateful_sets"].append(ss_info)
            
            # Get all Namespaces (cluster-wide info)
            namespaces = self.v1.list_namespace()
            for ns in namespaces.items:
                ns_info = {
                    "name": ns.metadata.name,
                    "status": ns.status.phase,
                    "created": ns.metadata.creation_timestamp.isoformat() if ns.metadata.creation_timestamp else None
                }
                context["namespaces"].append(ns_info)
            
        except Exception as e:
            context["error"] = str(e)
        
        return context