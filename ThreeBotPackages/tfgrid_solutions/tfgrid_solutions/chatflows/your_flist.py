from Jumpscale import j
import math
import requests
from Jumpscale.servers.gedis.GedisChatBot import StopChatFlow
import uuid


class FlistDeploy(j.servers.chatflow.get_class()):
    steps = [
        "flist_start",
        "flist_name",
        "container_resources",
        "container_volume",
        "container_volume_details",
        "select_pool",
        "flist_network",
        "flist_url",
        "container_interactive",
        "container_env",
        "container_node_id",
        "container_logs",
        "container_ip",
        "overview",
        "reservation",
        "container_access",
    ]

    @j.baseclasses.chatflow_step()
    def flist_start(self):
        self.solution_id = uuid.uuid4().hex
        user_info = self.user_info()
        self.env = dict()
        j.sal.reservation_chatflow.validate_user(user_info)
        self.md_show("# This wizard will help you deploy a container using any flist provided", md=True)

    @j.baseclasses.chatflow_step(title="Solution name")
    def flist_name(self):
        self.solution_name = j.sal.chatflow_deployer.ask_name(self)

    @j.baseclasses.chatflow_step(title="Container resources")
    def container_resources(self):
        self.resources = j.sal.chatflow_deployer.ask_container_resources(self)

    @j.baseclasses.chatflow_step(title="Attach Volume")
    def container_volume(self):
        volume_attach = self.drop_down_choice(
            "Would you like to attach an extra volume to the container", ["YES", "NO"], required=True, default="NO"
        )
        self.container_volume_attach = volume_attach == "YES" or False

    @j.baseclasses.chatflow_step(title="Volume details")
    def container_volume_details(self):
        if self.container_volume_attach:
            form = self.new_form()
            vol_disk_size = form.int_ask("Please specify the volume size in GiB", required=True, default=10)
            vol_mount_point = form.string_ask("Please enter the mount point", required=True, default="/data")
            form.ask()
            self.vol_size = vol_disk_size.value
            self.vol_mount_point = vol_mount_point.value

    @j.baseclasses.chatflow_step(title="Pool")
    def select_pool(self):
        query = {
            "cru": self.resources["cpu"],
            "mru": math.ceil(self.resources["memory"] / 1024),
            "sru": math.ceil(self.resources["disk_size"] / 1024),
        }
        if self.container_volume_attach:
            query["sru"] += math.ceil(self.vol_size / 1024)
        cu, su = j.sal.chatflow_deployer.calculate_capacity_units(**query)
        self.pool_id = j.sal.chatflow_deployer.select_pool(self, cu=cu, su=su)

    @j.baseclasses.chatflow_step(title="Network")
    def flist_network(self):
        self.network_view = j.sal.chatflow_deployer.select_network(self, self.pool_id)

    @j.baseclasses.chatflow_step(title="Flist url")
    def flist_url(self):
        self.flist_link = self.string_ask(
            "Please add the link to your flist to be deployed. For example: https://hub.grid.tf/usr/example.flist",
            required=True,
        )

        self.flist_link = self.flist_link.strip()

        if "hub.grid.tf" not in self.flist_link or ".md" in self.flist_link[-3:]:
            raise StopChatFlow(
                "This flist is not correct. Please make sure you enter a valid link to an existing flist For example: https://hub.grid.tf/usr/example.flist"
            )

        response = requests.head(self.flist_link)
        response_md5 = requests.head(f"{self.flist_link}.md5")
        if response.status_code != 200 or response_md5.status_code != 200:
            raise StopChatFlow("This flist doesn't exist. Please make sure you enter a valid link to an existing flist")

    @j.baseclasses.chatflow_step(title="Container ineractive & EntryPoint")
    def container_interactive(self):
        self.interactive = self.single_choice(
            "Would you like access to your container through the web browser (coreX)?", ["YES", "NO"], required=True
        )
        if self.interactive == "NO":
            self.entrypoint = self.string_ask("Please add your entrypoint for your flist") or ""
        else:
            self.port = "7681"
            self.entrypoint = ""

    @j.baseclasses.chatflow_step(title="Environment variables")
    def container_env(self):
        self.env.update(self.multi_values_ask("Set Environment Variables"))

    @j.baseclasses.chatflow_step(title="Container node id")
    def container_node_id(self):
        query = {
            "cru": self.resources["cpu"],
            "mru": math.ceil(self.resources["memory"] / 1024),
            "mru": math.ceil(self.resources["memory"] / 1024),
            "sru": self.resources["disk_size"],
        }
        self.selected_node = j.sal.chatflow_deployer.ask_container_placement(self, self.pool_id, **query)
        if not self.selected_node:
            self.selected_node = j.sal.chatflow_deployer.schedule_container(self.pool_id, **query)

    @j.baseclasses.chatflow_step(title="Container logs")
    def container_logs(self):
        self.container_logs_option = self.single_choice(
            "Do you want to push the container logs (stdout and stderr) onto an external redis channel",
            ["YES", "NO"],
            default="NO",
        )
        if self.container_logs_option == "YES":
            self.log_config = j.sal.chatflow_deployer.ask_container_logs(self, self.solution_name)
        else:
            self.log_config = {}

    @j.baseclasses.chatflow_step(title="Container IP")
    def container_ip(self):
        self.network_view_copy = self.network_view.copy()
        result = j.sal.chatflow_deployer.add_network_node(
            self.network_view.name, self.selected_node, self.network_view_copy
        )
        if result:
            for wid in result["ids"]:
                success = j.sal.chatflow_deployer.wait_workload(wid, self)
                if not success:
                    raise StopChatFlow(f"Failed to add node {self.selected_node.node_id} to network {wid}")
            self.network_view_copy = self.network_view_copy.copy()
        free_ips = self.network_view_copy.get_node_free_ips(self.selected_node)
        self.ip_address = self.drop_down_choice("Please choose IP Address for your solution", free_ips)

    @j.baseclasses.chatflow_step(title="Confirmation")
    def overview(self):
        self.metadata = {
            "Solution Name": self.solution_name,
            "Network": self.network_view.name,
            "Node ID": self.selected_node.node_id,
            "Pool": self.pool_id,
            "CPU": self.resources["cpu"],
            "Memory": self.resources["memory"],
            "Disk Size": self.resources["disk_size"],
            "IP Address": self.ip_address,
        }
        if self.container_volume_attach:
            self.metadata["Volume Size"] = self.vol_size
            self.metadata["Volume Mountpoint"] = self.vol_mount_point
        self.metadata.update(self.log_config)
        self.md_show_confirm(self.metadata)

    @j.baseclasses.chatflow_step(title="Reservation")
    def reservation(self):
        volume_config = {}
        if self.container_volume_attach:
            vol_id = j.sal.chatflow_deployer.deploy_volume(
                self.pool_id, self.selected_node.node_id, self.vol_size, solution_uuid=self.solution_id
            )
            success = j.sal.chatflow_deployer.wait_workload(vol_id, self)
            if not success:
                raise StopChatFlow(f"Failed to add node {self.selected_node.node_id} to network {vol_id}")
            volume_config[self.vol_mount_point] = vol_id

        metadata = {
            "name": self.solution_name,
            "form_info": {"chatflow": "flist", "Solution name": self.solution_name, "env": self.env},
        }
        self.resv_id = j.sal.chatflow_deployer.deploy_container(
            pool_id=self.pool_id,
            node_id=self.selected_node.node_id,
            network_name=self.network_view.name,
            ip_address=self.ip_address,
            flist=self.flist_link,
            cpu=self.resources["cpu"],
            memory=self.resources["memory"],
            disk_size=self.resources["disk_size"],
            env=self.env,
            interactive=self.interactive,
            entrypoint=self.entrypoint,
            log_config=self.log_config,
            volumes=volume_config,
            **metadata,
            solution_uuid=self.solution_id,
        )
        success = j.sal.chatflow_deployer.wait_workload(self.resv_id, self)
        if not success:
            # TODO: check if a volume is created and cancel it
            raise StopChatFlow(f"Failed to deploy workload {self.resv_id}")

    @j.baseclasses.chatflow_step(title="Success", disable_previous=True)
    def container_access(self):
        if self.interactive:
            res = f"""\
                    # Container has been deployed successfully: your reservation id is: {self.resv_id}
                    Open your browser at [http://{self.ip_address}:7681](http://{self.ip_address}:7681)
                    """
            self.md_show(j.core.text.strip(res), md=True)
        else:
            res = f"""\
                    # Container has been deployed successfully: your reservation id is: {self.resv_id}
                    Your IP is  ```{self.ip_address}```
                    """
            self.md_show(j.core.text.strip(res), md=True)


chat = FlistDeploy
