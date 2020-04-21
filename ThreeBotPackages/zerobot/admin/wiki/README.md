# Admin package

This package provides an admin dashboard interface with some actors for your 3Bot health, logs..etc.

## What's included

### Home

Shows system versions, network, processes status, memory consumptions and some health checks
![images/dashboard.png](../images/dashboard.png)

### Logs
Allows seeing logs per application

![logs](../images/logs.png)


### Alerts
Advanced alerts system

![alerts](../images/alerts.png)

check [alerts.md](./alerts.md) for info about its actors
### Package management system
Easy way to install/stop packages available on the filesystem or from a trusted git repository

![packagemanager](../images/packagemanager.png)


### Online code editor

If you want to edit code from the dashboard directly you can do so using CodeServer package

![codeserver](../images/codeserverterminal.png)

## Installation

Admin dashboard is installed by default, you also can install it by path or git url as any other package.

You can view the dashboard by navigating to `http://<host>/admin`.

## Login

The dashboard is protected by 3Bot connect, you need to register your current 3Bot, from 3Bot server shell (for now, you need to suffix your name with `.3bot`):

```
j.tools.threebot.init_my_threebot()
```

Now, you can download [3Bot connect app](https://3bot.org/3bot.html) and use it to login with the 3Bot name you registered.

Also, other people can access the dashboard, but they need to be added to admins from `Settings`, Also, admins can be dded to `j.myidentities.default.admins` via `kosmos` shell:

```python3
j.myidentities.default.admins.append("ahmed.3bot")
j.myidentities.default.save()
```


## Extending Admin Dashboard

Please check [extending admin dashboard](./extending_admin.md)
