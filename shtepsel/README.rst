==========================
SHTEPSEL
==========================

The software product is aimed at small trucking companies that do not have logistics hubs and transport goods directly from the supplier to the client.


Details
============

Model for determining route efficiency
--------------------------------------

In the model, the optimality of the route is evaluated from the point of view of material and technical costs for transportation (without taking into account delivery charges by customers) and depends on the following parameters:
 * car load as the maximum load share of the permissible volume V_order / V_car or masses m_order / m_car,
 * distance S_actloc_sup from the location of the car, current at the time of order approval, actloc before the start of transportation at the point of the supplier (the car covers this distance empty),
 * distances S_sup_cli for cargo transportation from the supplier to the client (in the case of the "one carrier - many orders" route, only sections of the route are taken into account with loaded car),
 * distance S_cli_base after completion of the transportation to return the car to the base depot (a new route can be defined for the car immediately after the completion of the previous one, but this option allows you to give a slight advantage to the end of the route near the depot).

 route_efficiency =
           max(V_order / V_car, m_order / m_car) * S_sup_cli / (S_actloc_sup + S_sup_cli + S_cli_base * 0.1)


Features of software implementation:
------------------------------------

The RouteConstruction Wizard wizard model is used to create routes.
The initial distribution of routes is carried out automatically in the "one carrier - one order" mode. The recursive route optimization procedure uses the route efficiency indicator route_efficiency and searches for the shortest path in the order of bypassing the points of the directed edges "supplier (loading) - customer (unloading)" with a check of cargo capacity, vehicle dimensions and delivery times.
Based on the initial allocation, the operator can manually move (kanban) allocated and unallocated orders between carriers and target the change in performance of each route.
There are two reasons for providing a manual adjustment option: fully automatic formation is a complex logistic problem with a large number of options that can be solved using, for example, Dijkstra-type algorithms for directed graphs; it requires the development of a complex algorithm, therefore it is a separate study; as a rule, software customers prefer to be able to adjust automated processes, since the individual characteristics of logistics cannot always be taken into account; if you keep a history of manual adjustments, then later the algorithm can be refined to take into account the specifics (using ML and AI technologies).
Distances between adjacent points of the route are calculated using the formula of the spherical projection of the Earth onto the plane through geodetic coordinates, which are defined by default in the ResPartner model. Therefore, the length of the route is determined on the assumption that the points of the route are connected by straight lines. One can imagine that transportation is provided by aero-mobiles. To lay out realistic land routes and calculate real distances, you can install a paid Odoo module, which uses the Google Maps application and determines routes on highways by geodetic coordinates.


Credits
=======

Authors
-------

* Zaporozhets Company

Contributors
------------

* Anton Zaporozhets <ant.zaporozhets@gmail.com>
