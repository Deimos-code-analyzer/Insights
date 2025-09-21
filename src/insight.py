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
            "stateful_sets": []
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
                # Container details
                containers = []
                for container in pod.spec.containers:
                    container_info = {
                        "name": container.name,
                        "image": container.image,
                        "ports": [{"container_port": p.container_port, "protocol": p.protocol} for p in (container.ports or [])],
                        "resources": {
                            "requests": container.resources.requests if container.resources and container.resources.requests else {},
                            "limits": container.resources.limits if container.resources and container.resources.limits else {}
                        },
                        "env_vars": len(container.env or []),
                        "volume_mounts": [{"name": vm.name, "mount_path": vm.mount_path} for vm in (container.volume_mounts or [])]
                    }
                    containers.append(container_info)
                
                # Container statuses
                container_statuses = []
                if pod.status.container_statuses:
                    for status in pod.status.container_statuses:
                        status_info = {
                            "name": status.name,
                            "ready": status.ready,
                            "restart_count": status.restart_count,
                            "state": {},
                            "last_state": {}
                        }
                        
                        # Current state
                        if status.state.running:
                            status_info["state"] = {
                                "status": "running",
                                "started_at": status.state.running.started_at.isoformat() if status.state.running.started_at else None
                            }
                        elif status.state.waiting:
                            status_info["state"] = {
                                "status": "waiting",
                                "reason": status.state.waiting.reason,
                                "message": status.state.waiting.message
                            }
                        elif status.state.terminated:
                            status_info["state"] = {
                                "status": "terminated",
                                "reason": status.state.terminated.reason,
                                "exit_code": status.state.terminated.exit_code,
                                "finished_at": status.state.terminated.finished_at.isoformat() if status.state.terminated.finished_at else None
                            }
                        
                        # Last state
                        if status.last_state and status.last_state.terminated:
                            status_info["last_state"] = {
                                "status": "terminated",
                                "reason": status.last_state.terminated.reason,
                                "exit_code": status.last_state.terminated.exit_code,
                                "finished_at": status.last_state.terminated.finished_at.isoformat() if status.last_state.terminated.finished_at else None
                            }
                        
                        container_statuses.append(status_info)
                
                # Pod conditions
                conditions = []
                if pod.status.conditions:
                    for condition in pod.status.conditions:
                        condition_info = {
                            "type": condition.type,
                            "status": condition.status,
                            "reason": condition.reason,
                            "message": condition.message,
                            "last_transition_time": condition.last_transition_time.isoformat() if condition.last_transition_time else None
                        }
                        conditions.append(condition_info)
                
                # Volumes
                volumes = []
                if pod.spec.volumes:
                    for volume in pod.spec.volumes:
                        volume_info = {
                            "name": volume.name,
                            "type": "unknown"
                        }
                        
                        if volume.config_map:
                            volume_info["type"] = "configMap"
                            volume_info["config_map_name"] = volume.config_map.name
                        elif volume.secret:
                            volume_info["type"] = "secret"
                            volume_info["secret_name"] = volume.secret.secret_name
                        elif volume.persistent_volume_claim:
                            volume_info["type"] = "persistentVolumeClaim"
                            volume_info["pvc_name"] = volume.persistent_volume_claim.claim_name
                        elif volume.empty_dir:
                            volume_info["type"] = "emptyDir"
                        elif volume.host_path:
                            volume_info["type"] = "hostPath"
                            volume_info["host_path"] = volume.host_path.path
                        
                        volumes.append(volume_info)
                
                pod_info = {
                    "name": pod.metadata.name,
                    "status": pod.status.phase,
                    "ready": sum(1 for c in (pod.status.container_statuses or []) if c.ready),
                    "total_containers": len(pod.spec.containers),
                    "restart_count": sum(c.restart_count for c in (pod.status.container_statuses or [])),
                    "node": pod.spec.node_name,
                    "created": pod.metadata.creation_timestamp.isoformat() if pod.metadata.creation_timestamp else None,
                    "labels": pod.metadata.labels or {},
                    "annotations": {k: v for k, v in (pod.metadata.annotations or {}).items() if not k.startswith("kubectl.kubernetes.io")},
                    "service_account": pod.spec.service_account_name,
                    "restart_policy": pod.spec.restart_policy,
                    "dns_policy": pod.spec.dns_policy,
                    "pod_ip": pod.status.pod_ip,
                    "host_ip": pod.status.host_ip,
                    "qos_class": pod.status.qos_class,
                    "containers": containers,
                    "container_statuses": container_statuses,
                    "conditions": conditions,
                    "volumes": volumes
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
            
        except Exception as e:
            context["error"] = str(e)
        
        return context