## Python installation

Perform a platform indepent installation using PyPI.

!!! note
    Ensure build requirements are met, see below.

!!! warning
    At runtime Odoo will always require the **LESSC** compiler, 
    and most likely **WKHTMLTOPDF**. Odooku's deployment methods
    take care of this, however for any other installation method
    you should install this yourself.

``` bash
pip install odooku-odoo-addons
pip install odooku
```

This will install the full Odoo suite. If you want to keep installation and dependency size to a minimal,
feel free to install the seperate packages like so:

``` bash
pip install odooku-odoo-[app]
```

Available options are:

 - account
 - account_accountant
 - board
 - calendar
 - contacts
 - crm
 - **extra:** This package provides point of sale hardware modules and a few test modules.
 - fleet 
 - hr 
 - hr_attendance 
 - hr_expense
 - hr_holidays
 - hr_recruitment
 - hr_timesheet
 - im_livechat
 - l10n_fr_certification
 - lunch
 - mail
 - maintenance
 - mass_mailing
 - mrp
 - mrp_repair
 - note
 - point_of_sale
 - project
 - project_issue
 - purchase
 - sale
 - stock
 - survey
 - website
 - website_blog
 - website_event
 - website_forum
 - website_sale
 - website_slides


## Build requirements

### Ubuntu 16.04

``` bash
sudo apt-get install libpq-dev libxml2-dev libxslt1-dev libldap2-dev libsasl2-dev libssl-dev
```

### OSX

``` bash
brew install postgresql
```