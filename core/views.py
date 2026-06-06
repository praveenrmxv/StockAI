from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Product, Sale
from .forms import ProductForm
import numpy as np
import pandas as pd
from .models import Sale
import numpy as np
from .models import Profile
from .forms import ProfileForm
from collections import defaultdict
from sklearn.linear_model import LinearRegression
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required



def home(request):
    return render(request, 'home.html')


@login_required
def inventory(request):
    form = ProductForm()

    if request.method == "POST":
        form = ProductForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('/inventory/')   # ✅ yahan return hai

    products = Product.objects.all()

    return render(request, 'inventory.html', {   # ✅ ALWAYS RETURN
        'form': form,
        'products': products
    })


@login_required
def dashboard(request):
    products = Product.objects.all()
    sales = Sale.objects.all()

    # ===== BASIC DATA =====
    total_products = products.count()
    total_sales = sum([s.quantity * s.price for s in sales])

    # ===== MONTHLY SALES =====
    monthly_sales = {}
    for s in sales:
        month = s.date.strftime("%b")
        monthly_sales[month] = monthly_sales.get(month, 0) + (s.quantity * s.price)

    months = list(monthly_sales.keys())
    sales_values = list(monthly_sales.values())

    # ===== ML PREDICTION =====
    from sklearn.linear_model import LinearRegression
    import numpy as np

    predicted_sales = 0

    if len(months) > 1:
        X = np.arange(len(months)).reshape(-1, 1)
        y = np.array(sales_values)

        model = LinearRegression()
        model.fit(X, y)

        predicted_sales = model.predict([[len(months)]])[0]

    # ===== DEPENDENCY ANALYSIS =====
    prices = [s.price for s in sales]
    quantities = [s.quantity for s in sales]

    correlation = 0
    if len(prices) > 1:
        correlation = np.corrcoef(prices, quantities)[0][1]

    # ===== INSIGHT =====
    if correlation > 0.5:
        insight = "High demand even at higher prices 📈"
    elif correlation < -0.5:
        insight = "Price increase reduces sales 📉"
    else:
        insight = "No strong relationship found"

    # ===== ALERT SYSTEM =====
    alerts = []

    for p in products:
        if p.quantity < 5:
            alerts.append(f"{p.name} is low in stock ⚠️")

    if len(quantities) > 1 and quantities[-1] < quantities[-2]:
        alerts.append("Recent sales are decreasing 📉")

    # ===== RECOMMENDATION SYSTEM =====
    from collections import defaultdict

    product_sales = defaultdict(int)

    for s in sales:
        product_sales[s.product_name] += s.quantity

    avg_sales = sum(product_sales.values()) / len(product_sales) if product_sales else 0

    recommendations = []

    for product, qty in product_sales.items():
        if qty > avg_sales:
            recommendations.append(f"{product}: Increase stock 📈")
        elif qty < avg_sales:
            recommendations.append(f"{product}: Reduce stock 📉")
        else:
            recommendations.append(f"{product}: Maintain stock ✅")

    # ===== SCATTER DATA =====
    scatter_data = [
        {"x": s.price, "y": s.quantity} for s in sales
    ]

    # ===== FINAL RENDER =====
    return render(request, 'dashboard.html', {
        'total_products': total_products,
        'total_sales': total_sales,
        'months': months,
        'sales_values': sales_values,
        'predicted_sales': round(predicted_sales, 2),
        'correlation': round(correlation, 2),
        'insight': insight,
        'alerts': alerts,
        'recommendations': recommendations,
        'scatter_data': scatter_data,
    })


# @login_required
# def upload_csv(request):
#     if request.method == 'POST':
#         file = request.FILES['file']

#         df = pd.read_csv(file)

#         # 🔥 CLEANING START
#         df.columns = df.columns.str.strip().str.lower()

#         # Rename columns (safe)
#         df.rename(columns={
#             'product_name': 'product_name',
#             'quantity': 'quantity',
#             'price': 'price',
#             'date': 'date'
#         }, inplace=True)

#         # Remove null & duplicates
#         df.dropna(inplace=True)
#         df.drop_duplicates(inplace=True)

#         # Type conversion
#         df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce')
#         df['price'] = pd.to_numeric(df['price'], errors='coerce')
#         df['date'] = pd.to_datetime(df['date'], errors='coerce')

#         df.dropna(inplace=True)

#         # Remove invalid data
#         df = df[(df['quantity'] > 0) & (df['price'] > 0)]

#         # 🔥 SAVE
#         for _, row in df.iterrows():
#             Sale.objects.create(
#                 product_name=row['product_name'],
#                 quantity=int(row['quantity']),
#                 price=float(row['price']),
#                 date=row['date']
#             )

#     return render(request, 'upload.html')






@login_required
def upload_csv(request):

    if request.method == 'POST':

        file = request.FILES.get('file')

        # FILE CHECK
        if not file:
            return render(request, 'upload.html', {
                'error': 'No file selected!'
            })

        # ONLY CSV
        if not file.name.endswith('.csv'):
            return render(request, 'upload.html', {
                'error': 'Please upload a CSV file only!'
            })

        try:

            # READ CSV
            df = pd.read_csv(file)

            # CLEAN COLUMN NAMES
            df.columns = [
                col.strip().lower().replace(" ", "_")
                for col in df.columns
            ]

            # 🔥 AUTO DETECT COLUMNS
            column_mapping = {}

            for col in df.columns:

                # PRODUCT NAME
                if any(word in col for word in [
                    'product',
                    'item',
                    'name'
                ]):
                    column_mapping[col] = 'product_name'

                # QUANTITY
                elif any(word in col for word in [
                    'qty',
                    'quantity',
                    'stock',
                    'units'
                ]):
                    column_mapping[col] = 'quantity'

                # PRICE
                elif any(word in col for word in [
                    'price',
                    'amount',
                    'cost',
                    'rate'
                ]):
                    column_mapping[col] = 'price'

                # DATE
                elif any(word in col for word in [
                    'date',
                    'day',
                    'created'
                ]):
                    column_mapping[col] = 'date'

            # RENAME COLUMNS
            df.rename(columns=column_mapping, inplace=True)

            # REQUIRED FIELDS
            required_columns = [
                'product_name',
                'quantity',
                'price',
                'date'
            ]

            # CHECK REQUIRED
            missing = []

            for col in required_columns:
                if col not in df.columns:
                    missing.append(col)

            if missing:
                return render(request, 'upload.html', {
                    'error': f'Could not detect columns: {missing}'
                })

            # REMOVE NULLS & DUPLICATES
            df.dropna(inplace=True)
            df.drop_duplicates(inplace=True)

            # TYPE CONVERSION
            df['quantity'] = pd.to_numeric(
                df['quantity'],
                errors='coerce'
            )

            df['price'] = pd.to_numeric(
                df['price'],
                errors='coerce'
            )

            df['date'] = pd.to_datetime(
                df['date'],
                errors='coerce'
            )

            # REMOVE BAD DATA
            df.dropna(inplace=True)

            df = df[
                (df['quantity'] > 0) &
                (df['price'] > 0)
            ]

            # SAVE DATA
            for _, row in df.iterrows():

                Sale.objects.create(
                    product_name=row['product_name'],
                    quantity=int(row['quantity']),
                    price=float(row['price']),
                    date=row['date']
                )

            return render(request, 'upload.html', {
                'success': 'CSV uploaded successfully!'
            })

        except Exception as e:

            return render(request, 'upload.html', {
                'error': str(e)
            })

    return render(request, 'upload.html')






def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('/dashboard/')
        else:
            return render(request, 'login.html', {'error': 'Invalid credentials'})

    return render(request, 'login.html')


# def profile(request):
#     profile, created = Profile.objects.get_or_create(user=request.user)

#     if request.method == 'POST':
#         form = ProfileForm(request.POST, request.FILES, instance=profile)
#         if form.is_valid():
#             form.save()
#     else:
#         form = ProfileForm(instance=profile)

#     return render(request, 'profile.html', {'form': form})


@login_required
def profile(request):

    profile, created = Profile.objects.get_or_create(
        user=request.user
    )

    if request.method == 'POST':

        form = ProfileForm(
            request.POST,
            request.FILES,
            instance=profile
        )

        if form.is_valid():
            form.save()
            return redirect('/profile/')

    else:
        form = ProfileForm(instance=profile)

    return render(request, 'profile.html', {
        'form': form,
        'profile': profile
    })

