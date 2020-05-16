# Security

## Securing your installation

The HTTP API is essentially accessing the database read-only, so data can't be changed. We still recommend to only allow the intended users to access the API because it's easy to run requests which take a lot of resources. The server can be overloaded with requests.

Same goes for your Postgresql database.

For example block outside IP addresses, block ports, add password protection. Refer to your webserver and Postgresql documentation.


## Reporting security issues

Email reports about any security related issues you find to nominatim@lonvia.de. Don't use the public issue tracker. Do not publish any information until we fixed it.

Please describe which version of Nominatim you tested, on which website (e.g. https://openstreetmap.org) if any, operating system and version, database version, what you think the impact of the issue is, and who could exploit it.

We support the latest stable release and the two previous minor releases. https://github.com/osm-search/Nominatim/releases

We're looking for issue related to Cross-site scripting (XSS), SQL injection, server-side code execution, direct write access to the database, access to usage logs.

Less for issues related to security best practices like preventing high resource use, DDoS, crashing an installation, setting of HTTP headers or webserver configuration, but appreciate if you found something that can be fixed.

Off-topic are issues related to the returned geographic data. That data is public and open already.

When we release patches they're annouced on [geocoding@openstreetmap.org](https://lists.openstreetmap.org/listinfo/geocoding) and
[dev@openstreetmap.org](https://lists.openstreetmap.org/listinfo/dev) mailing lists.


### Known fixed issues

* [2020-05-04] Nominatim 3.4.2, 3.3.1, 3.2.1 Fixes issue where the /details endpoint failed to properly sanitize user input and used it as is in an SQL query. We thank bladeswords for reporting it.
