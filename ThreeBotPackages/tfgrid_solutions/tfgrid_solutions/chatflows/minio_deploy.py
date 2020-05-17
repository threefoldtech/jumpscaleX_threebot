from Jumpscale import j
import math


class MinioDeploy(j.servers.chatflow.get_class()):
    steps = [
        "deployment_start",
        "network_selection",
        "solution_name",
        "storage_type",
        "access_credentials",
        "container_resources",
        "minio_resources",
        "expiration_datetime",
        "zdb_nodes",
        "minio_node",
        "ip_selection",
        "overview",
        "zdb_reservation",
        "minio_reservation",
        "success",
    ]

    @j.baseclasses.chatflow_step(title="")
    def deployment_start(self):
        self.user_info = self.user_info()
        j.sal.reservation_chatflow.validate_user(self.user_info)
        self.user_form_data = {}
        self.user_form_data["chatflow"] = "minio"
        self.md_show("# This wizard will help you deploy a minio cluster")

    @j.baseclasses.chatflow_step(title="Network")
    def network_selection(self):
        self.network = j.sal.reservation_chatflow.network_select(self, j.me.tid)

    @j.baseclasses.chatflow_step(title="Solution name")
    def solution_name(self):
        model = j.threebot.packages.tfgrid_solutions.tfgrid_solutions.bcdb_model_get("tfgrid.solutions.minio.1")
        self.user_form_data["Solution name"] = j.sal.reservation_chatflow.solution_name_add(self, model)

    @j.baseclasses.chatflow_step(title="Storage")
    def storage_type(self):
        self.user_form_data["Disk type"] = self.drop_down_choice(
            "Please choose a the type of disk for zdb", ["SSD", "HDD"], required=True, default="SSD"
        )

    @j.baseclasses.chatflow_step(title="Access credentials")
    def access_credentials(self):
        name = self.user_info["username"]
        accesskey_string = f"{name.split('.')[0]}"
        secret_string = "secret12345"
        form = self.new_form()
        accesskey = form.string_ask(
            "Please add the key to be used for minio when logging in. Make sure not to lose it",
            default=accesskey_string,
            min_length=3,
        )
        secret = form.string_ask(
            "Please add the secret to be used for minio when logging in to match the previous key. Make sure not to lose it",
            default=secret_string,
            min_length=8,
        )
        form.ask()

        self.user_form_data["Access key"] = accesskey.value
        self.user_form_data["Secret"] = secret.value

    @j.baseclasses.chatflow_step(title="Container resources")
    def container_resources(self):
        form = self.new_form()
        cpu = form.int_ask("Please add how many CPU cores are needed", default=1)
        memory = form.int_ask("Please add the amount of memory in MB", default=1024)
        form.ask()
        self.user_form_data["CPU"] = cpu.value
        self.user_form_data["Memory"] = memory.value

    @j.baseclasses.chatflow_step(title="Resources for minio")
    def minio_resources(self):
        form = self.new_form()
        data_number = form.int_ask(
            "Please add the number of locations you need. Take care of the ratio between the locations and locations allowed to fail that you will specify next",
            default=2,
        )
        parity = form.int_ask("Please add the number of locations allowed to fail", default=1)

        form.ask()
        self.user_form_data["Locations"] = int(data_number.value)
        self.user_form_data["Locations allowed to fail"] = int(parity.value)
        self.user_form_data["ZDB number"] = int(data_number.value) + int(parity.value)

    @j.baseclasses.chatflow_step(title="Expiration")
    def expiration_datetime(self):
        self.expiration = self.datetime_picker(
            "Please enter solution expiration time.",
            required=True,
            min_time=[3600, "Date/time should be at least 1 hour from now"],
            default=j.data.time.epoch + 3900,
        )
        self.user_form_data["Solution expiration"] = j.data.time.secondsToHRDelta(self.expiration - j.data.time.epoch)

    @j.baseclasses.chatflow_step(title="Zdb (storage) nodes selection")
    def zdb_nodes(self):
        zdb_nodequery = {}
        zdb_nodequery["currency"] = self.network.currency
        if self.user_form_data["Disk type"] == "SSD":
            zdb_nodequery["sru"] = 10
        if self.user_form_data["Disk type"] == "HDD":
            zdb_nodequery["hru"] = 10

        zdb_farms = j.sal.reservation_chatflow.farm_names_get(
            self.user_form_data["ZDB number"], self, message="zdb", **zdb_nodequery
        )
        self.nodes_selected = j.sal.reservation_chatflow.nodes_get(
            number_of_nodes=self.user_form_data["ZDB number"], farm_names=zdb_farms, **zdb_nodequery
        )

    @j.baseclasses.chatflow_step(title="Minio container node selection")
    def minio_node(self):
        nodequery = {}
        nodequery["currency"] = self.network.currency
        nodequery["mru"] = math.ceil(self.user_form_data["Memory"] / 1024)
        nodequery["cru"] = self.user_form_data["CPU"]
        nodequery["sru"] = 1
        cont_farms = j.sal.reservation_chatflow.farm_names_get(1, self, message="minio container", **nodequery)
        self.cont_node = j.sal.reservation_chatflow.nodes_get(number_of_nodes=1, farm_names=cont_farms, **nodequery)[0]

    @j.baseclasses.chatflow_step(title="Minio container IP")
    def ip_selection(self):
        self.network_copy = j.sal.reservation_chatflow.network_get_from_reservation(
            self, j.me.tid, self.network.name, self.network.resv_id
        )
        for node_selected in self.nodes_selected:
            self.network_copy.add_node(node_selected)

        if self.cont_node not in self.nodes_selected:
            self.network_copy.add_node(self.cont_node)

        self.ip_address = self.network_copy.ask_ip_from_node(
            self.cont_node, "Please choose IP Address for your solution"
        )
        self.user_form_data["IP Address"] = self.ip_address

    @j.baseclasses.chatflow_step(title="Confirmation")
    def overview(self):
        self.md_show_confirm(self.user_form_data)

    @j.baseclasses.chatflow_step(title="Reserve zdb", disable_previous=True)
    def zdb_reservation(self):
        self.network = self.network_copy
        self.network.update(j.me.tid, currency=self.network.currency, bot=self)
        # create new reservation
        self.reservation = j.sal.zosv2.reservation_create()

        self.password = j.data.idgenerator.generateGUID()

        for node in self.nodes_selected:
            j.sal.zosv2.zdb.create(
                reservation=self.reservation,
                node_id=node.node_id,
                size=10,
                mode="seq",
                password=self.password,
                disk_type=self.user_form_data["Disk type"],
                public=False,
            )
        self.volume = j.sal.zosv2.volume.create(
            self.reservation, self.cont_node.node_id, size=10, type=self.user_form_data["Disk type"]
        )

        # register the reservation for zdb db
        self.zdb_rid = j.sal.reservation_chatflow.reservation_register_and_pay(
            self.reservation, self.expiration, customer_tid=j.me.tid, currency=self.network.currency, bot=self
        )
        res = f"# Database has been deployed with reservation id: {self.zdb_rid}. Click next to continue with deployment of the minio container"

        self.reservation_result = j.sal.reservation_chatflow.reservation_wait(self, self.zdb_rid)
        self.md_show(res)

    @j.baseclasses.chatflow_step(title="Reserve minio container", disable_previous=True)
    def minio_reservation(self):
        # read the IP address of the 0-db namespaces after they are deployed to be used in the creation of the minio container
        namespace_config = []
        for result in self.reservation_result:
            if result.category == "ZDB":
                data = result.data_json
                cfg = f"{data['Namespace']}:{self.password}@[{data['IP']}]:{data['Port']}"
                namespace_config.append(cfg)

        entry_point = "/bin/entrypoint"
        flist_url = "https://hub.grid.tf/tf-official-apps/minio-2020-01-25T02-50-51Z.flist"

        minio_secret_encrypted = j.sal.zosv2.container.encrypt_secret(
            self.cont_node.node_id, self.user_form_data["Secret"]
        )
        shards_encrypted = j.sal.zosv2.container.encrypt_secret(self.cont_node.node_id, ",".join(namespace_config))
        secret_env = {"SHARDS": shards_encrypted, "SECRET_KEY": minio_secret_encrypted}

        # create container
        cont = j.sal.zosv2.container.create(
            reservation=self.reservation,
            node_id=self.cont_node.node_id,
            network_name=self.network.name,
            ip_address=self.ip_address,
            flist=flist_url,
            entrypoint=entry_point,
            cpu=self.user_form_data["CPU"],
            memory=self.user_form_data["Memory"],
            env={
                "DATA": str(self.user_form_data["Locations"]),
                "PARITY": str(self.user_form_data["Locations allowed to fail"]),
                "ACCESS_KEY": self.user_form_data["Access key"],
            },
            secret_env=secret_env,
        )

        j.sal.zosv2.volume.attach_existing(
            container=cont, volume_id=f"{self.zdb_rid}-{self.volume.workload_id}", mount_point="/data"
        )

        res = j.sal.reservation_chatflow.solution_model_get(
            self.user_form_data["Solution name"], "tfgrid.solutions.minio.1", self.user_form_data
        )
        self.reservation = j.sal.reservation_chatflow.reservation_metadata_add(self.reservation, res)
        self.resv_id = j.sal.reservation_chatflow.reservation_register_and_pay(
            self.reservation, self.expiration, customer_tid=j.me.tid, currency=self.network.currency, bot=self
        )
        j.sal.reservation_chatflow.reservation_save(
            self.resv_id, self.user_form_data["Solution name"], "tfgrid.solutions.minio.1", self.user_form_data
        )

    @j.baseclasses.chatflow_step(title="Success", disable_previous=True)
    def success(self):
        res = f"""\
            # Minio cluster has been deployed successfully. Your reservation id is: {self.resv_id}
            Open your browser at [http://{self.ip_address}:9000](http://{self.ip_address}:9000). It may take a few minutes.
            """
        self.md_show(j.core.text.strip(res))


chat = MinioDeploy
