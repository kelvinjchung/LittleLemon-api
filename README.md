# LittleLemon Restaurant API Project
Built with Django with DRF and Djoser. For practice in building APIs and handling HTTP requests locally, as a part of the Meta Back-End Developer Course.

___
This project features multiple APIs mimicking what a restaurant may use to handle orders received through a website. 

1. There are three types of users: Manager, Delivery Crew, and Customer. Based on what group the authenticated user is a part of, API calls have different functions or are prohibited.
2. `api/menu-items` show a Django Browsable API view of the available menu items in the database. `api/menu-items/<int:pk>` shows details of the specified menu-item, indexed by its primary key.
3. `api/groups/<str:group>/users` allow managers to view all users of a particular group, or add users to a specific group. `api/groups/<str:group>/users/<int:pk>` allows managers to remove a specified user
from a group.
5. Customers are allowed to add menu items to their carts as well as view their current cart using `api/cart/menu-items`. Customers can also delete their cart.
6. Customers can place an order of all items in their cart using `api/orders`, effectively deleting their cart. They can also view all outstanding orders. Managers can assign orders to certain delivery crew.
Delivery crew can use the API to view only the orders to which they are assigned.
7. Using `api/orders/<int:pk>`, customers can view the order if it is their own. Delivery crew that is assigned to the specified order can update the order with the order status change. Managers can update order
status as well as the delivery crew assigned to the order. Managers can also delete orders using this API. 
