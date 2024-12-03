# GeoCat Odoo modules

This repository contains the custom Odoo modules for our GeoCat office ERP. 
These modules are used to extend the functionality of the Odoo platform for the GeoCat-specific apps, e.g. software licensing.

## Installation

The GeoCat Odoo modules are automatically deployed on [Odoo.sh](https://odoo.sh).
Log in to Odoo.sh to move deployments from development to staging and production environments.

Once logged in to a GeoCat Odoo instance, enable debug/dev mode, go to `Apps` and click on `Update Apps List`.
Then, search for the GeoCat modules and install/activate them.

## Development

For local development, it is recommended to use PyCharm as the IDE.

For development, clone this repository as `geocat` (!!) into a folder on your local machine (e.g. `GeoCatERP`).
Then, also clone the community [`odoo`](https://github.com/odoo/odoo) repository into that same folder,
as well as the private [`enterprise`](https://github.com/odoo/enterprise) repository if you have access to it.
As paying `Odoo.sh` customers, we should have read-only access to the `enterprise` repository, so if you do not
have access yet, please contact Odoo and tell them your GitHub username, so they can grant it.

Make sure that the `odoo` and `enterprise` repositories are both set to the same version branch 
that corresponds to the version of Odoo that you are running (e.g. `18.0`).

Now set up a virtual environment in PyCharm in the `venv` folder inside the main `GeoCatERP` folder.
Then, install the requirements from the `odoo` repository in this virtual environment from the PyCharm terminal 
(which should now be running from the activated virtual environment):

```bash
pip install -r odoo/requirements.txt
```

The root-level folder structure should now look like this, 
where `geocat` is this repository and `odoo` and `enterprise` are the official Odoo repositories:

```
GeoCatERP/
├── enterprise/
├── geocat/
├── odoo/
└── venv/
```

Next, you will need to make sure that you have a PostgreSQL DB server running.
You do not have to create the database, as Odoo will do this for you the first time, but you will have to make sure that a DB role exists.
To do so, please use `pgAdmin` as described [here](https://www.odoo.com/documentation/18.0/administration/on_premise/source.html#postgresql).

Now we can set up a new _Run Configuration_ in PyCharm to run and debug Odoo.
Make sure to set the working directory to the `odoo` folder and the Python interpreter to the one in the virtual environment.

The script path to run is (for example):

```bash
odoo-bin --addons-path="addons\,..\enterprise\,..\geocat\" -d odoo-local -r odoo -w odoo
```

So in the PyCharm _Run Configuration_, set the script path to `odoo-bin` and set the rest as the _Script Parameters_ value.
In the example above, the `odoo-local` database is created with the `odoo` role as the owner (with the same password).

Now you can run Odoo from PyCharm and access it in your browser at `localhost:8069`.