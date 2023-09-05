import datetime
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.contrib.auth.models import User, Group
from .models import Cart, MenuItem, Order, OrderItem
from .serializers import (
    CartSerializer,
    MenuItemSerializer,
    OrderSerializer,
    OrderItemSerializer,
    UserSerializer,
)
from .permissions import IsManager, IsDeliveryCrew, IsCustomer


class MenuItemsView(generics.ListCreateAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    ordering_fields = ["price", "title"]
    filterset_fields = ["price", "title"]
    search_fields = ["title", "category__title"]

    # disallow POST, PUT, PATCH, DELETE for non-managers
    def check_permissions(self, request):
        if request.method in ["GET"]:
            self.permission_classes = [IsAuthenticated]
        else:
            self.permission_classes = [IsManager | IsAdminUser]
        return super().check_permissions(request)


class SingleMenuItemView(generics.RetrieveUpdateDestroyAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer

    # disallow POST, PUT, PATCH, DELETE for non-managers
    def check_permissions(self, request):
        if request.method in ["GET"]:
            self.permission_classes = [IsAuthenticated]
        else:
            self.permission_classes = [IsManager | IsAdminUser]

        return super().check_permissions(request)


class ManagerView(generics.ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsManager]

    def get_queryset(self):
        return User.objects.filter(groups__name="Manager")

    def post(self, request, *args, **kwargs):
        username = request.data["username"]
        if username:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                return Response(
                    {"message": "User does not exist"}, status=status.HTTP_404_NOT_FOUND
                )
            managers = Group.objects.get(name="Manager")
            managers.user_set.add(user)
            return Response(status=status.HTTP_201_CREATED)

        return Response(
            {"message": "User does not exist"}, status=status.HTTP_404_NOT_FOUND
        )


class UserView(generics.ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsManager]
    group = {"manager": "Manager", "delivery-crew": "Delivery Crew"}

    def get(self, request, *args, **kwargs):
        # check if group name in url is valid
        if kwargs["group"] not in self.group:
            return Response(
                {"message": "Invalid Group"}, status=status.HTTP_404_NOT_FOUND
            )
        groupMem = User.objects.filter(groups__name=self.group[kwargs["group"]])
        return Response(
            self.serializer_class(groupMem, many=True).data, status=status.HTTP_200_OK
        )

    def post(self, request, *args, **kwargs):
        # check if group name in url is valid
        if kwargs["group"] not in self.group:
            return Response(
                {"message": "Invalid Group"}, status=status.HTTP_404_NOT_FOUND
            )

        username = request.data["username"]
        if username:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                return Response(
                    {"message": "User does not exist"}, status=status.HTTP_404_NOT_FOUND
                )
            managers = Group.objects.get(name=self.group[kwargs["group"]])
            managers.user_set.add(user)
            return Response(status=status.HTTP_201_CREATED)

        return Response(
            {"message": "Must provide username"}, status=status.HTTP_400_NOT_FOUND
        )


class SingleUserView(generics.DestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsManager]
    group = {"manager": "Manager", "delivery-crew": "Delivery Crew"}

    def delete(self, request, *args, **kwargs):
        # check if group name in url is valid
        if kwargs["group"] not in self.group:
            return Response(
                {"message": "Invalid Group"}, status=status.HTTP_404_NOT_FOUND
            )

        id = kwargs["pk"]
        if id:
            try:
                user = User.objects.get(id=id)
            except User.DoesNotExist:
                return Response(
                    {"message": "User does not exist"}, status=status.HTTP_404_NOT_FOUND
                )
            if not user.groups.filter(name=self.group[kwargs["group"]]).exists():
                return Response(
                    {"message": "User is not a Manager"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            managers = Group.objects.get(name=self.group[kwargs["group"]])
            managers.user_set.remove(user)
            return Response(status=status.HTTP_200_OK)

        return Response({"message": "Error"}, status=status.HTTP_400_BAD_REQUEST)


class CartView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    permission_classes = [IsCustomer]

    def get(self, request, *args, **kwargs):
        user = request.user
        # if user.groups.filter(name__in=["Manager", "Delivery Crew"]).exists():
        #     return Response({"message": "Only Customers can view their cart"}, status=status.HTTP_403_FORBIDDEN)
        cart = Cart.objects.filter(user=user)
        return Response(
            self.serializer_class(cart, many=True).data, status=status.HTTP_200_OK
        )

    def post(self, request, *args, **kwargs):
        user = request.user
        # if user.groups.filter(name__in=["Manager", "Delivery Crew"]).exists():
        #     return Response({"message": "Only Customers can add to their cart"}, status=status.HTTP_403_FORBIDDEN)
        if Cart.objects.filter(user=user).exists():
            return Response(
                {"message": "Cart already exists for this user"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            menuitem = MenuItem.objects.get(id=request.data["menuitem"])
            quantity = int(request.data["quantity"])
        except KeyError:
            return Response(
                {"message": "Must provide menuitem and quantity"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except MenuItem.DoesNotExist:
            return Response(
                {"message": "Menu item does not exist"},
                status=status.HTTP_404_NOT_FOUND,
            )

        unit_price = menuitem.price
        price = quantity * unit_price
        data = {
            "user_id": user.id,
            "menuitem_id": menuitem.id,
            "quantity": quantity,
            "unit_price": unit_price,
            "price": price,
        }
        serialized_cart = self.serializer_class(data=data)
        serialized_cart.is_valid(raise_exception=True)
        serialized_cart.save()
        return Response({"message": "Cart created"}, status=status.HTTP_201_CREATED)

    def delete(self, request, *args, **kwargs):
        user = request.user
        try:
            cart = Cart.objects.get(user=user)
        except Cart.DoesNotExist:
            return Response(
                {"message": "Cart does not exist"}, status=status.HTTP_404_NOT_FOUND
            )

        cart.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class OrderView(generics.ListCreateAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    def check_permissions(self, request):
        if request.method in ["GET"]:  # GET allowed for all users
            self.permission_classes = [IsAuthenticated]
        elif request.method in ["POST"]:  # POST allowed for customers
            self.permission_classes = [IsCustomer]
        else:
            self.permission_classes = [IsAdminUser]

        return super().check_permissions(request)

    def get(self, request, *args, **kwargs):
        if request.user.groups.filter(name="Manager").exists():
            return super().get(request, *args, **kwargs)
        elif request.user.groups.filter(name="Delivery Crew").exists():
            serialized_order = self.serializer_class(
                Order.objects.filter(delivery_crew=request.user), many=True
            ).data
        else:  # Customer View
            serialized_order = self.serializer_class(
                Order.objects.filter(user=request.user), many=True
            ).data

        return Response(serialized_order, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        user = request.user
        try:
            cart = Cart.objects.get(user=user)
        except Cart.DoesNotExist:
            return Response(
                {"message": "This user does not have a cart"},
                status=status.HTTP_404_NOT_FOUND,
            )

        order_data = {
            "user_id": user.id,
            "total": cart.price,
            "date": datetime.date.today(),
        }
        serialized_order = self.serializer_class(data=order_data)
        serialized_order.is_valid(raise_exception=True)
        serialized_order.save()

        orderitem_data = {
            "order_id": serialized_order.data["id"],
            "menuitem_id": cart.menuitem.id,
            "quantity": cart.quantity,
            "unit_price": cart.unit_price,
            "price": cart.price,
        }
        serialized_orderitem = OrderItemSerializer(data=orderitem_data)
        serialized_orderitem.is_valid(raise_exception=True)
        serialized_orderitem.save()

        cart.delete()

        return Response({"message": "Order created"}, status=status.HTTP_201_CREATED)


class SingleOrderView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    def check_permissions(self, request):
        if request.method in ["GET"]:
            self.permission_classes = [IsCustomer]
        elif request.method in ["PATCH"]:
            self.permission_classes = [IsManager | IsDeliveryCrew]
        elif request.method in ["DELETE"]:
            self.permission_classes = [IsManager]
        else:
            self.permission_classes = [IsAdminUser]

        return super().check_permissions(request)

    def get(self, request, *args, **kwargs):
        user = request.user
        try:
            order = Order.objects.get(id=kwargs["pk"])
            orderitem = OrderItem.objects.get(order=kwargs["pk"])
        except Order.DoesNotExist:
            return Response(
                {"message": "Order does not exist"}, status=status.HTTP_404_NOT_FOUND
            )

        if user.id != order.user.id:
            return Response(
                {"messsage": "You are not authorized to view this order"},
                status=status.HTTP_403_FORBIDDEN,
            )

        serialized_orderitem = OrderItemSerializer(orderitem)

        return Response(
            serialized_orderitem.data,
            status=status.HTTP_200_OK,
        )

    def patch(self, request, *args, **kwargs):
        user = request.user
        try:
            order = Order.objects.get(id=kwargs["pk"])
        except Order.DoesNotExist:
            return Response(
                {"message": "Order does not exist"}, status=status.HTTP_404_NOT_FOUND
            )
        if user.groups.filter(name="Manager").exists():
            status_data = {}
            if "status" in request.data.keys():
                status_data["status"] = request.data["status"]
            if "delivery_crew" in request.data.keys():
                if not User.objects.filter(id=request.data["delivery_crew"]).exists():
                    return Response(
                        {"message": "User does not exist"},
                        status=status.HTTP_404_NOT_FOUND,
                    )
                if (
                    not User.objects.get(id=request.data["delivery_crew"])
                    .groups.filter(name="Delivery Crew")
                    .exists()
                ):
                    return Response(
                        {"message": "User is not a delivery crew"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                status_data["delivery_crew_id"] = request.data["delivery_crew"]
            if not status_data:
                return Response(
                    {"message": "Must provide status or delivery crew"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            serialized_order = self.serializer_class(
                order, data=status_data, partial=True
            )

        elif user.groups.filter(name="Delivery Crew").exists():
            if user != order.delivery_crew:
                return Response(
                    {"message": "You are not authorized to update this order"},
                    status=status.HTTP_403_FORBIDDEN,
                )
            try:
                status_data = {"status": request.data["status"]}
            except KeyError:
                return Response(
                    {"message": "Must provide status code 0 or 1"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            serialized_order = self.serializer_class(
                order, data=status_data, partial=True
            )

        serialized_order.is_valid(raise_exception=True)
        serialized_order.save()
        return Response({"message": "Order updated"}, status=status.HTTP_200_OK)

    # def put(self, request, *args, **kwargs):
    #     user = request.user
    #     try:
    #         order = Order.objects.get(id=kwargs["pk"])
    #     except Order.DoesNotExist:
    #         return Response(
    #             {"message": "Order does not exist"}, status=status.HTTP_404_NOT_FOUND
    #         )
    #     status_data = {}
    #     if "user_id" not in request.data.keys():
    #         status_data["user_id"] = order.user.id
    #     if "total" not in request.data.keys():
    #         status_data["total"] = order.total
    #     if "date" not in request.data.keys():
    #         status_data["date"] = order.date
    #     if "status" in request.data.keys():
    #         status_data["status"] = request.data["status"]
    #     if "delivery_crew" in request.data.keys():
    #         status_data["delivery_crew_id"] = request.data["delivery_crew"]
    #     serialized_order = self.serializer_class(data=status_data, partial=True)
    #     serialized_order.is_valid(raise_exception=True)
    #     serialized_order.save()
    #     return Response({"message": "Order updated"}, status=status.HTTP_200_OK)

    def delete(self, request, *args, **kwargs):
        try:
            order = Order.objects.get(id=kwargs["pk"])
        except Order.DoesNotExist:
            return Response(
                {"message": "Order does not exist"}, status=status.HTTP_404_NOT_FOUND
            )
        order.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
