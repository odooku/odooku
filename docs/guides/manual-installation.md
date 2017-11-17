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

- mail
- account_invoicing
- board
- calendar
- contacts
- crm
- fleet
- hr
- hr_attendance
- hr_expense
- hr_holidays
- hr_recruitment
- project
- hr_timesheet
- im_livechat
- lunch
- maintenance
- mass_mailing
- stock
- mrp
- sale_management
- mrp_repair
- note
- point_of_sale
- purchase
- website
- survey
- website_blog
- website_event
- website_forum
- website_sale
- website_slides
- extra

## Build requirements

### Ubuntu 16.04

``` bash
sudo apt-get install libpq-dev libxml2-dev libxslt1-dev libldap2-dev libsasl2-dev libssl-dev
```

### OSX

``` bash
brew install postgresql libjpeg zlib
```