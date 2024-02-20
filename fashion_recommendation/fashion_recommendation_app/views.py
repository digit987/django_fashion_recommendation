import pandas as pd
import numpy as np
from random import randint
import csv
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from .models import Product, Rating, Cart, CartItem
from .recommendation import recommend
#from .forms import ProductForm

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('index')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('index')
    else:
        form = AuthenticationForm()
    return render(request, 'registration/login.html', {'form': form})

def logout_view(request):
    if request.method == 'POST':
        logout(request)
        return redirect('index')

@login_required
def rate_product(request, product_id):
    if request.method == 'POST':
        product = Product.objects.get(id=product_id)
        rating_value = int(request.POST.get('rating'))
        Rating.objects.create(user=request.user, product=product, rating=rating_value)
    return redirect('index')

def get_recommended_products(user_id):
    # Read the CSV file into a DataFrame
    df = pd.read_csv('ecommerce_app/ratings.csv')

    # Initialize an empty user-item matrix
    user_item_matrix = {}

    # Iterate over each row in the DataFrame
    for index, row in df.iterrows():
        user_id = row['User ID']
        product_id = row['Product ID']
        rating = row['Rating']

        # Check if the user already exists in the user-item matrix
        if user_id in user_item_matrix:
            # Update the existing user's ratings
            user_item_matrix[user_id][product_id] = 1 if rating > 0 else 0
        else:
            # Create a new entry for the user and set the ratings
            user_item_matrix[user_id] = {product_id: 1 if rating > 0 else 0}

    # Convert the ratings to numpy arrays with dtype=np.float64
    for user_id, ratings in user_item_matrix.items():
        user_item_matrix[user_id] = np.array(list(ratings.values()), dtype=np.float64)

    top_n = 3

    recommended_items = recommend(user_item_matrix, user_id, top_n)
    return recommended_items

def index(request):
    # Retrieve all products
    all_products = Product.objects.all()

    # Retrieve the logged-in user (assuming you have authentication set up)
    user = request.user

    # Get user's recommended products (recommend function returns a list of product IDs)
    recommended_product_ids = get_recommended_products(user.id)

    # Retrieve recommended products from the database
    recommended_products = Product.objects.filter(id__in=recommended_product_ids)

    context = {
        'all_products': all_products,
        'recommended_products': recommended_products,
    }
    return render(request, 'index.html', context)

def populate_user(request):
    df = pd.read_csv("ecommerce_app/ratings.csv")
    df_distinct_users = df.drop_duplicates(subset=['User ID'])
    for index, row in df_distinct_users.iterrows():
        User.objects.create(
        username=row['User ID'],
        password="password@123"
        )
    return HttpResponse("User population completed successfully")

def populate_product(request):
    df = pd.read_csv("ratings.csv")
    df_distinct_products = df.drop_duplicates(subset=['Product ID'])
    for index, row in df_distinct_products.iterrows():
        Product.objects.create(
        product_id=row['Product ID'],
        product_name=row['Product Name'],
        brand=row['Brand'],
        category=row['Category'],
        price=row['Price'],
        color=row['Color'],
        size=row['Size'],
        quantity=randint(1, 10)
        )
    return HttpResponse("Product population completed successfully")

def populate_rating():
    df = pd.read_csv("./ratings.csv")
    for index, row in df.iterrows():
        Rating.objects.create(
        user=row['User ID'],
        product=row['Product ID'],
        rating=row['Rating'],
        )
    return HttpResponse("Rating population completed successfully")

def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('index')
    else:
        form = ProductForm()
    return render(request, 'add_product.html', {'form': form})

def edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            return redirect('index')
    else:
        form = ProductForm(instance=product)
    return render(request, 'edit_product.html', {'form': form})

def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        product.delete()
        return redirect('index')
    return render(request, 'delete_product.html', {'product': product})

@login_required
def add_to_cart(request, product_id):
    product = Product.objects.get(id=product_id)
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    return redirect('cart')

@login_required
def remove_from_cart(request, cart_item_id):
    cart_item = get_object_or_404(CartItem, id=cart_item_id)
    cart_item.delete()
    return redirect('cart')

@login_required
def view_cart(request):
    cart_items = CartItem.objects.filter(cart=request.user.cart)
    total_price = sum(item.product.price * item.quantity for item in cart_items)
    return render(request, 'cart.html', {'cart_items': cart_items, 'total_price': total_price})

def cart(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_items = CartItem.objects.filter(cart=cart)
    return render(request, 'cart.html', {'cart_items': cart_items})

def checkout(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_items = CartItem.objects.filter(cart=cart)
    total_price = sum(item.product.price * item.quantity for item in cart_items)
    order = Order.objects.create(user=request.user, total_price=total_price)
    for cart_item in cart_items:
        OrderItem.objects.create(order=order, product=cart_item.product, quantity=cart_item.quantity, price=cart_item.product.price)
    cart_items.delete()
    return render(request, 'checkout.html', {'order': order})