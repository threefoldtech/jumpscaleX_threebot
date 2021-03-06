from Jumpscale import j
import math
import uuid
from Jumpscale.servers.gedis.GedisChatBot import StopChatFlow


class MonitoringSolutionDeploy(j.servers.chatflow.get_class()):
    # TODO: merge containers resources steps, no?
    steps = [
        "deployment_start",
        "choose_name",
        "public_key_get",
        "prometheus_container_resources",
        "prometheus_volume_details",
        "grafana_container_resources",
        "redis_container_resources",
        "select_pool",
        "network_selection",
        "container_node_id",
        "prometheus_container_ip",
        "grafana_container_ip",
        "redis_container_ip",
        "overview",
        "reservation",
        "success",
    ]

    @j.baseclasses.chatflow_step()
    def deployment_start(self):
        self.tools_names = ["Prometheus", "Grafana", "Redis"]
        self.solution_id = uuid.uuid4().hex
        user_info = self.user_info()
        j.sal.reservation_chatflow.validate_user(user_info)
        self.env_var_dict = dict()
        self.prometheus_query = dict()
        self.grafana_query = dict()
        self.redis_query = dict()
        self.query = {"Prometheus": self.prometheus_query, "Grafana": self.grafana_query, "Redis": self.redis_query}
        self.ip_addresses = {"Prometheus": "", "Grafana": "", "Redis": ""}
        self.md_show(
            "# This wizard will help you deploy a monitoring system that includes Prometheus, Grafana, and redis",
            md=True,
        )

    @j.baseclasses.chatflow_step(title="Solution name")
    def choose_name(self):
        valid = False
        while not valid:
            self.solution_name = j.sal.chatflow_deployer.ask_name(self)
            solutions = j.sal.chatflow_solutions.list_monitoring_solutions(sync=False)
            valid = True
            for sol in solutions:
                if sol["Name"] == self.solution_name:
                    valid = False
                    self.md_show("The specified solution name already exists. please choose another.")
                    break
                valid = True

    @j.baseclasses.chatflow_step()
    def public_key_get(self):
        self.env_var_dict["SSH_KEY"] = self.upload_file(
            """Please add your public ssh key, this will allow you to access the deployed containers using ssh.
                Just upload the file with the key.
                Note: please use keys compatible with Dropbear server eg: rsa """,
            required=True,
        ).split("\n")[0]

    @j.baseclasses.chatflow_step(title="Prometheus container resources")
    def prometheus_container_resources(self):
        self.prometheus_query = j.sal.chatflow_deployer.ask_container_resources(self, disk_type=True)
        self.query["Prometheus"] = self.prometheus_query

    @j.baseclasses.chatflow_step(title="Prometheus volume details")
    def prometheus_volume_details(self):
        form = self.new_form()
        vol_disk_size = form.int_ask("Please specify the volume size in GiB", required=True, default=10)
        form.ask()
        self.vol_size = vol_disk_size.value
        self.vol_mount_point = "/data"

    @j.baseclasses.chatflow_step(title="Grafana container resources")
    def grafana_container_resources(self):
        self.grafana_query = j.sal.chatflow_deployer.ask_container_resources(self, disk_type=True)
        self.query["Grafana"] = self.grafana_query

    @j.baseclasses.chatflow_step(title="Redis container resources")
    def redis_container_resources(self):
        self.redis_query = j.sal.chatflow_deployer.ask_container_resources(self, disk_type=True)
        self.query["Redis"] = self.redis_query

    @j.baseclasses.chatflow_step(title="Pool")
    def select_pool(self):
        query = {"cru": 0, "mru": 0, "sru": 0, "hru": 0}
        for name in self.tools_names:
            query["cru"] += self.query[name]["cpu"]
            query["mru"] += math.ceil(self.query[name]["memory"] / 1024)
            if self.query[name]["disk_type"] == "SSD":
                query["sru"] += math.ceil(self.query[name]["disk_size"] / 1024)
            else:
                query["hru"] += math.ceil(self.query[name]["disk_size"] / 1024)
        query["sru"] += self.vol_size
        cu, su = j.sal.chatflow_deployer.calculate_capacity_units(**query)
        self.pool_id = j.sal.chatflow_deployer.select_pool(self, cu=cu, su=su)

    @j.baseclasses.chatflow_step(title="Network")
    def network_selection(self):
        self.network_view = j.sal.chatflow_deployer.select_network(self, self.pool_id)

    @j.baseclasses.chatflow_step(title="Containers' node id")
    def container_node_id(self):
        self.nodes_selected = {"Prometheus": None, "Grafana": None, "Redis": None}
        for name in self.tools_names:
            query = {
                "cru": self.query[name]["cpu"],
                "mru": math.ceil(self.query[name]["memory"] / 1024),
                "sru": math.ceil(self.query[name]["disk_size"] / 1024),
            }
            self.nodes_selected[name] = j.sal.chatflow_deployer.ask_container_placement(
                self, self.pool_id, workload_name=name, **query
            )
            if not self.nodes_selected[name]:
                self.nodes_selected[name] = j.sal.chatflow_deployer.schedule_container(self.pool_id, **query)

    @j.baseclasses.chatflow_step(title="Prometheus container IP")
    def prometheus_container_ip(self):
        self.prometheus_network = self.network_view.copy()
        result = j.sal.chatflow_deployer.add_network_node(
            self.network_view.name, self.nodes_selected["Prometheus"], self.pool_id, self.prometheus_network
        )
        if result:
            for wid in result["ids"]:
                success = j.sal.chatflow_deployer.wait_workload(wid, self)
                if not success:
                    raise StopChatFlow(
                        f"Failed to add node {self.nodes_selected['Prometheus'].node_id} to network {wid}"
                    )
            self.prometheus_network = self.prometheus_network.copy()
        free_ips = self.prometheus_network.get_node_free_ips(self.nodes_selected["Prometheus"])
        self.ip_addresses["Prometheus"] = self.drop_down_choice(
            "Please choose IP Address for your Prometheus container", free_ips
        )

    @j.baseclasses.chatflow_step(title="Grafana container IP")
    def grafana_container_ip(self):
        self.grafana_network = self.prometheus_network.copy()
        result = j.sal.chatflow_deployer.add_network_node(
            self.network_view.name, self.nodes_selected["Grafana"], self.pool_id, self.prometheus_network
        )
        if result:
            for wid in result["ids"]:
                success = j.sal.chatflow_deployer.wait_workload(wid, self)
                if not success:
                    raise StopChatFlow(f"Failed to add node {self.nodes_selected['Grafana'].node_id} to network {wid}")
            self.grafana_network = self.grafana_network.copy()
        free_ips = self.grafana_network.get_node_free_ips(self.nodes_selected["Grafana"])
        if self.ip_addresses["Prometheus"] in free_ips:
            free_ips.remove(self.ip_addresses["Prometheus"])
        self.ip_addresses["Grafana"] = self.drop_down_choice(
            "Please choose IP Address for your Grafana container", free_ips
        )

    @j.baseclasses.chatflow_step(title="Redis container IP")
    def redis_container_ip(self):
        self.redis_network = self.grafana_network.copy()
        result = j.sal.chatflow_deployer.add_network_node(
            self.network_view.name, self.nodes_selected["Redis"], self.pool_id, self.prometheus_network
        )
        if result:
            for wid in result["ids"]:
                success = j.sal.chatflow_deployer.wait_workload(wid, self)
                if not success:
                    raise StopChatFlow(f"Failed to add node {self.nodes_selected['Redis'].node_id} to network {wid}")
            self.redis_network = self.redis_network.copy()
        free_ips = self.redis_network.get_node_free_ips(self.nodes_selected["Redis"])
        if self.ip_addresses["Prometheus"] in free_ips:
            free_ips.remove(self.ip_addresses["Prometheus"])
        if self.ip_addresses["Grafana"] in free_ips:
            free_ips.remove(self.ip_addresses["Grafana"])
        self.ip_addresses["Redis"] = self.drop_down_choice(
            "Please choose IP Address for your Redis container", free_ips
        )

    @j.baseclasses.chatflow_step(title="Confirmation")
    def overview(self):
        self.metatata = {
            "Solution Name": self.solution_name,
            "Pool": self.pool_id,
            "Network": self.network_view.name,
            "Prometheus Node ID": self.nodes_selected["Prometheus"].node_id,
            "Prometheus CPU": self.query["Prometheus"]["cpu"],
            "Prometheus Memory": self.query["Prometheus"]["memory"],
            "Prometheus Disk Size": self.query["Prometheus"]["disk_size"],
            "Prometheus Disk Type": self.query["Prometheus"]["disk_type"],
            "Prometheus IP Address": self.ip_addresses["Prometheus"],
            "Grafana Node ID": self.nodes_selected["Grafana"].node_id,
            "Grafana CPU": self.query["Grafana"]["cpu"],
            "Grafana Memory": self.query["Grafana"]["memory"],
            "Grafana Disk Size": self.query["Grafana"]["disk_size"],
            "Grafana Disk Type": self.query["Grafana"]["disk_type"],
            "Grafana IP Address": self.ip_addresses["Grafana"],
            "Redis Node ID": self.nodes_selected["Redis"].node_id,
            "Redis CPU": self.query["Redis"]["cpu"],
            "Redis Memory": self.query["Redis"]["memory"],
            "Redis Disk Size": self.query["Redis"]["disk_size"],
            "Redis Disk Type": self.query["Redis"]["disk_type"],
            "Redis IP Address": self.ip_addresses["Redis"],
        }
        self.md_show_confirm(self.metatata)

    @j.baseclasses.chatflow_step(title="Reservation")
    def reservation(self):
        metadata = {
            "name": self.solution_name,
            "form_info": {"chatflow": "monitoring", "Solution name": self.solution_name,},
        }
        self.network = self.redis_network

        redis_ip_address = self.ip_addresses["Redis"]

        # create redis container
        redis_flist = f"https://hub.grid.tf/tf-official-apps/redis_zinit.flist"
        self.redis_resv_id = j.sal.chatflow_deployer.deploy_container(
            pool_id=self.pool_id,
            node_id=self.nodes_selected["Redis"].node_id,
            network_name=self.network_view.name,
            ip_address=redis_ip_address,
            flist=redis_flist,
            cpu=self.query["Redis"]["cpu"],
            memory=self.query["Redis"]["memory"],
            disk_size=self.query["Redis"]["disk_size"],
            disk_type=self.query["Redis"]["disk_type"],
            env=self.env_var_dict,
            interactive=False,
            entrypoint="",
            **metadata,
            solution_uuid=self.solution_id,
        )
        success = j.sal.chatflow_deployer.wait_workload(self.redis_resv_id, self)
        if not success:
            j.sal.chatflow_solutions.cancel_solution([self.redis_resv_id])
            raise StopChatFlow(f"Failed to deploy workload {self.redis_resv_id}")

        # create prometheus container
        prometheus_flist = "https://hub.grid.tf/tf-official-apps/prometheus:latest.flist"
        log_config = {
            "channel_type": "redis",
            "channel_host": redis_ip_address,
            "channel_port": 6379,
            "channel_name": "prometheus",
        }
        vol_id = j.sal.chatflow_deployer.deploy_volume(
            self.pool_id, self.nodes_selected["Prometheus"].node_id, self.vol_size, solution_uuid=self.solution_id
        )
        success = j.sal.chatflow_deployer.wait_workload(vol_id, self)
        if not success:
            j.sal.chatflow_solutions.cancel_solution([self.redis_resv_id])
            raise StopChatFlow(f"Failed to add node {self.nodes_selected['Prometheus'].node_id} to network {vol_id}")
        volume_config = {self.vol_mount_point: vol_id}

        self.prometheus_resv_id = j.sal.chatflow_deployer.deploy_container(
            pool_id=self.pool_id,
            node_id=self.nodes_selected["Prometheus"].node_id,
            network_name=self.network_view.name,
            ip_address=self.ip_addresses["Prometheus"],
            flist=prometheus_flist,
            cpu=self.query["Prometheus"]["cpu"],
            memory=self.query["Prometheus"]["memory"],
            disk_size=self.query["Prometheus"]["disk_size"],
            disk_type=self.query["Prometheus"]["disk_type"],
            env=self.env_var_dict,
            interactive=False,
            entrypoint="",
            log_config=log_config,
            volumes=volume_config,
            **metadata,
            solution_uuid=self.solution_id,
        )
        success = j.sal.chatflow_deployer.wait_workload(self.prometheus_resv_id, self)
        if not success:
            j.sal.chatflow_solutions.cancel_solution([self.redis_resv_id])
            raise StopChatFlow(f"Failed to deploy workload {self.prometheus_resv_id}")

        # create grafana container
        grafana_flist = "https://hub.grid.tf/azmy.3bot/grafana-grafana-latest.flist"
        log_config = {
            "channel_type": "redis",
            "channel_host": redis_ip_address,
            "channel_port": 6379,
            "channel_name": "grafana",
        }
        self.grafana_resv_id = j.sal.chatflow_deployer.deploy_container(
            pool_id=self.pool_id,
            node_id=self.nodes_selected["Grafana"].node_id,
            network_name=self.network_view.name,
            ip_address=self.ip_addresses["Grafana"],
            flist=grafana_flist,
            cpu=self.query["Grafana"]["cpu"],
            memory=self.query["Grafana"]["memory"],
            disk_size=self.query["Grafana"]["disk_size"],
            disk_type=self.query["Grafana"]["disk_type"],
            env={},
            interactive=False,
            entrypoint="",
            log_config=log_config,
            **metadata,
            solution_uuid=self.solution_id,
        )
        success = j.sal.chatflow_deployer.wait_workload(self.grafana_resv_id, self)
        if not success:
            j.sal.chatflow_solutions.cancel_solution([self.redis_resv_id])
            raise StopChatFlow(f"Failed to deploy workload {self.grafana_resv_id}")

    @j.baseclasses.chatflow_step(title="Success", disable_previous=True)
    def success(self):
        res = f"""\
            # Your containers have been deployed successfully. Your reservation ids are: {self.prometheus_resv_id}, {self.grafana_resv_id}, {self.redis_resv_id}
            ## Prometheus
            #### Access container by ```ssh root@{self.ip_addresses["Prometheus"]}``` where you can manually customize the solutions you want to monitor
            #### Access Prometheus UI through ```{self.ip_addresses["Prometheus"]}:9090/graph``` which is accessed through your browser
            ## Grafana
            #### Access Grafana UI through ```{self.ip_addresses["Grafana"]}:3000``` which is accessed through your browser where you can manually configure to use prometheus
            ## Redis
            ```redis-cli -h {self.ip_addresses["Redis"]}```
            ## It may take a few minutes.
            """
        self.md_show(j.core.text.strip(res), md=True)


chat = MonitoringSolutionDeploy
