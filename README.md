## erpnext demo 

#### For v7

In v7, demo is merged into ERPNext. 

Don't install this app, just run

```
bench --site [site] execute erpnext.demo.demo.make
```

#### For v6

```
$ bench get-app erpnext_demo https://github.com/frappe/erpnext_demo
$ bench new-site {site}
$ bench --site {site} install-app erpnext
$ bench --site {site} install-app erpnext_demo
```

- Creates a fresh db
- Installs erpnext
- Installs erpnext-demo
