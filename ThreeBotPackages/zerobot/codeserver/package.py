from Jumpscale import j


class Package(j.baseclasses.threebot_package):
    def start(self):
        """
        called when the 3bot starts
        :return:
        """
        server = self.openresty
        server.configure()

        for port in (443, 80):
            website = server.get_from_port(port=port)
            locations = website.locations.get(f"codeserver_{port}")

            auth_location = locations.get_location_custom("codeserver")
            auth_location.config = """
            location /codeserver/ {
                # FIXME: need to update nginx/openresty with auth module, know yields unkown directive
                # auth_request /admin/codeserver/auth;

                access_by_lua '
                    local res = ngx.location.capture("/admin/codeserver/auth")

                    if res.status == ngx.HTTP_OK then
                        return
                    else
                        return ngx.redirect("/admin/codeserver")
                    end
                ';

                proxy_http_version 1.1;
                proxy_set_header Upgrade $http_upgrade;
                proxy_set_header Connection "Upgrade";
                proxy_set_header HOST $host;
                proxy_set_header X-Forwarded-Proto $scheme;
                proxy_set_header X-Real-IP $remote_addr;
                proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

                proxy_pass HTTP://127.0.0.1:8080/;
            }
            """

            proxy_location = locations.get_location_proxy("admin_codeserver")
            proxy_location.path_url = "/admin/codeserver/"
            proxy_location.ipaddr_dest = "127.0.0.1"
            proxy_location.port_dest = 8909
            proxy_location.path_dest = "/"
            locations.configure()
            website.configure()

        # Start code server
        cmd_start = "./code-server --auth none"
        self.startupcmd = j.servers.startupcmd.get("codeserver", cmd_start=cmd_start, path="/sandbox/bin", ports=8080)
        if not j.sal.fs.exists("/sandbox/bin/code-server"):
            j.builders.apps.codeserver.install()

        self.startupcmd.start()

        from threebot_packages.zerobot.codeserver.bottle.rooter import app_with_session

        self.gevent_rack.bottle_server_add(name="codeserver_auth", port=8909, app=app_with_session, websocket=True)

    def stop(self):
        # Stop code server
        if not j.sal.fs.exists("/sandbox/bin/code-server"):
            j.builders.apps.codeserver.install()
        self.startupcmd.stop()
